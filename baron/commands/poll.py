import logging

from peewee import Update, Model, CharField, ForeignKeyField, DateTimeField, PostgresqlDatabase, IntegrityError, \
    BigIntegerField, SQL
from requests import options
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext, CommandHandler, MessageHandler
import DB_connect
from baron.models import db
from configs.models import load_config_global

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Настройка подключения к базе данных через Peewee
if db.is_closed():
    db.connect()
    db.execute_sql('SET search_path TO petrenko_test')

# Модели для таблиц events и event_options
class Event(Model):
    id = CharField(primary_key=True)  # ID события
    author_id = CharField()
    name = CharField()
    min_attendees = CharField()
    created_at = DateTimeField()
    status_id = CharField()

    class Meta:
        database = db  # Подключение к базе данных
        db_table = 'events'  # Указываем имя таблицы

class EventOption(Model):
    event = ForeignKeyField(Event, backref='options')  # Внешний ключ на событие
    date = DateTimeField()
    place = CharField()
    place_link = CharField(null=True)
    created_at = DateTimeField()
    author_id = CharField()

    class Meta:
        database = db  # Подключение к базе данных
        db_table = 'event_options'  # Указываем имя таблицы

# Модель для таблицы users_poll
class UserPoll(Model):
    user_id = BigIntegerField()  # ID пользователя (например, ID Telegram)
    event_option_id = BigIntegerField()  # ID выбранного варианта (ссылка на event_options)
    status = CharField(default='pending')  # Статус выбора (например, "confirmed", "declined", "pending")

    class Meta:
        database = db  # Подключение к базе данных
        db_table = 'users_poll' # Имя таблицы в базе данных

    @classmethod
    def create_or_update(cls, user_id, event_option_id, status='pending'):
        """Метод для создания или обновления записи о выборе пользователя"""
        user_poll, created = cls.get_or_create(user_id=user_id, event_option_id=event_option_id)
        if not created:
            user_poll.status = status  # Обновляем статус, если запись уже существует
            user_poll.save()
        return user_poll

# Обработчик команды /poll {id}
async def poll_event(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите ID события, например: /poll 123")
        return

    event_id = context.args[0]
    user_id = update.message.from_user.id  # Получаем ID пользователя, который вызвал команду

    try:
        # Получаем событие по ID
        event = Event.get_or_none(Event.id == event_id)

        if not event:
            await update.message.reply_text(f"Событие с ID {event_id} не найдено.")
            return

        # Получаем все варианты для этого события
        options = EventOption.select().where(EventOption.event == event)

        if not options.exists():
            await update.message.reply_text("Для указанного события нет доступных вариантов.")
            return

        # Формируем информацию о событии
        event_info = f"Событие: {event.name}\nМинимальное количество участников: {event.min_attendees}\nСтатус: {event.status_id}\nДата начала: {event.created_at}"

        # Получаем выборы пользователя из таблицы users_poll
        user_selections = UserPoll.select().where(UserPoll.user_id == user_id, UserPoll.event_option_id.in_([option.id for option in options]))

        # Формируем клавиатуру с вариантами и метками "Выбрано" или "Отменить"
        reply_keyboard = []
        for option in options:
            # Проверяем, сделал ли пользователь выбор для этого варианта
            selected = any(selection.event_option_id == option.id for selection in user_selections)
            button_text = f"{option.place} - {option.date.strftime('%Y-%m-%d %H:%M')}"
            if selected:
                button_text += " (Выбрано)"
            reply_keyboard.append([KeyboardButton(button_text)])

        # Добавляем кнопку "Предложить свой вариант"
        reply_keyboard.append([KeyboardButton("Предложить свой вариант")])

        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

        # Отправляем информацию о событии и клавиатуру
        await update.message.reply_text(
            f"{event_info}\n\nВыберите один из предложенных вариантов или предложите свой:",
            reply_markup=markup
        )

    except IntegrityError as e:
        await update.message.reply_text("Ошибка при получении данных из базы.")
        print(f"Ошибка: {e}")
    except Exception as e:
        await update.message.reply_text("Произошла непредвиденная ошибка.")
        print(f"Ошибка: {e}")


async def handle_poll_selection(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    selection_text = update.message.text

    # Проверим, выбрал ли пользователь вариант (смотрим на текст кнопки)
    if " (Выбрано)" in selection_text:
        # Если уже выбрано, значит, нужно отменить выбор
        option_text = selection_text.replace(" (Выбрано)", "")
        option = EventOption.select().where(
            EventOption.place + ' - ' + EventOption.date.strftime('%Y-%m-%d %H:%M') == option_text).first()

        if option:
            try:
                # Удаляем выбор пользователя из таблицы users_poll
                UserPoll.delete().where(UserPoll.user_id == user_id, UserPoll.event_option_id == option.id).execute()
                await update.message.reply_text(
                    f"Вы отменили выбор: {option.place} - {option.date.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                await update.message.reply_text("Ошибка при отмене выбора.")
                print(f"Ошибка: {e}")
        else:
            await update.message.reply_text("Не удалось найти выбранный вариант.")
    else:
        # Если еще не выбрано, нужно записать выбор пользователя
        option_text = selection_text
        option = EventOption.select().where(
            EventOption.place + ' - ' + EventOption.date.strftime('%Y-%m-%d %H:%M') == option_text).first()

        if option:
            try:
                # Записываем выбор пользователя в таблицу users_poll
                UserPoll.create(user_id=user_id, event_option_id=option.id)
                await update.message.reply_text(
                    f"Вы выбрали: {option.place} - {option.date.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                await update.message.reply_text("Ошибка при записи выбора.")
                print(f"Ошибка: {e}")
        else:
            await update.message.reply_text("Не удалось найти выбранный вариант.")

# # Функция для получения списка всех зарегистрированных пользователей из базы данных
# def get_all_users():
#     db = DB_connect.DB()
#     connection = db.get_conn()
#     cursor = connection.cursor()
#
#     # Получаем всех пользователей
#     cursor.execute(f"SELECT id, username FROM {load_config_global().schema}.users")
#     users = cursor.fetchall()  # Список кортежей (user_id, tg_tag)
#
#     if cursor:
#         cursor.close()
#     if connection:
#         connection.close()
#     return users
#
#
# # Функция для подключения к базе данных PostgreSQL и получения данных о событии
# def get_event_details(event_id: int):
#     db = None
#     connection = None
#     cursor = None
#     try:
#         db = DB_connect.DB()
#         connection = db.get_conn()
#         cursor = connection.cursor()
#
#         cursor.execute(
#             f"SELECT event_id, date, place, place_link, created_at, author_id FROM {load_config_global().schema}.event_options "
#             f"WHERE"
#             f" event_id = %s;",
#             (event_id,))
#         result = cursor.fetchone()
#
#         if result:
#             event_id, date, place, place_link, created_at, author_id = result
#             return {
#                 "place": place,
#                 "place_link": place_link,
#                 "date": date
#             }
#         else:
#             return None
#     except Exception as e:
#         logger.error("Ошибка подключения к базе данных: %s", e)
#         return None
#     finally:
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()
#
#
# # Функция для сохранения результата в базе данных
# def save_poll_result(user_id, option_id, match):
#     try:
#         db = DB_connect.DB()
#         connection = db.get_conn()
#         cursor = connection.cursor()
#
#         cursor.execute(f"""
#             INSERT INTO {load_config_global().schema}.users_options (user_id, option_id, match)
#             VALUES (%s, %s, %s)
#         """, (user_id, option_id, match))
#         connection.commit()
#
#     except Exception as e:
#         logger.error("Ошибка при сохранении результата опроса: %s", e)
#
#     finally:
#         cursor.close()
#         connection.close()
#
#
# async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Получаем информацию о ответе на опрос
#     poll_answer = update.poll_answer
#     user_id = poll_answer.user.id
#     poll_id = poll_answer.poll_id  # poll_id опроса
#
#
#
#     selected_option_text = poll_answer.option_ids[0]  # Текст выбранной опции
#
#     # Определяем match на основе выбранной опции
#     match = selected_option_text == 0  # Если выбрал "Да", match = True
#
#     # Сохраняем результат голосования в базе данных
#     save_poll_result(user_id, poll_id, match)
#
#
# async def poll_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if not context.args:
#         await update.message.reply_text("Пожалуйста, укажите event_id.")
#         return
#
#     try:
#         event_id = int(context.args[0])  # Получаем event_id из команды
#     except ValueError:
#         await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
#         return
#
#     # Получаем данные о событии
#     event_details = get_event_details(event_id)
#     if not event_details:
#         await update.message.reply_text("Событие не найдено в базе данных.")
#         return
#
#     # Формируем текст опроса
#     question = f"Хотите ли вы посетить '{event_details['place']}'?"
#     options = ["Да", "Нет"]
#     link_text = f"[Ссылка на место]({event_details['place_link']})"
#     date = event_details['date']
#     additional_info = f"Начало: {date}\n{link_text}"
#
#     # Получаем список всех пользователей, которые зарегистрировались
#     users = get_all_users()
#
#     for user_id, tg_tag in users:
#         try:
#             # Отправка опроса в личные сообщения каждому пользователю
#             poll_message = await context.bot.send_poll(
#                 chat_id=user_id,
#                 question=question,
#                 options=options,
#                 is_anonymous=False,  # Публичный опрос
#                 allows_multiple_answers=False  # Одиночный ответ
#             )
#
#             # Отправка дополнительной информации в личные сообщения
#             await context.bot.send_message(
#                 chat_id=user_id,
#                 text=additional_info,
#                 parse_mode="Markdown"
#             )
#
#         except Exception as e:
#             print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
#
#     await update.message.reply_text("Опрос отправлен в личные сообщения всем зарегистрированным пользователям.")
