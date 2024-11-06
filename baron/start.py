import logging
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, PollAnswerHandler, ContextTypes
import DB_connect  # Подключение к вашей базе данных
from baron.commands.create_event import create_event  # Ваша логика создания события

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Функция для подключения к базе данных PostgreSQL и получения данных о событии
def get_event_details(event_id: int):
    db = None
    connection = None
    cursor = None
    try:
        db = DB_connect.DB()
        connection = db.get_conn()
        cursor = connection.cursor()

        cursor.execute("SELECT place_name, place_link, start_time FROM petrenko_test.options WHERE id = %s;", (event_id,))
        result = cursor.fetchone()

        if result:
            place_name, place_link, start_time = result
            return {
                "place_name": place_name,
                "place_link": place_link,
                "start_time": start_time
            }
        else:
            return None
    except Exception as e:
        logger.error("Ошибка подключения к базе данных: %s", e)
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# Функция для получения списка всех зарегистрированных пользователей из базы данных
def get_all_users():
    db = DB_connect.DB()
    connection = db.get_conn()
    cursor = connection.cursor()

    # Получаем всех пользователей
    cursor.execute("SELECT id, tg_tag FROM petrenko_test.users")
    users = cursor.fetchall()  # Список кортежей (user_id, tg_tag)

    if cursor:
        cursor.close()
    if connection:
        connection.close()
    return users


# Основной хендлер для команды /poll_event
# Основной хендлер для команды /poll_event
async def poll_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите event_id.")
        return

    try:
        event_id = int(context.args[0])  # Получаем event_id из команды
    except ValueError:
        await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
        return

    # Получаем данные о событии
    event_details = get_event_details(event_id)
    if not event_details:
        await update.message.reply_text("Событие не найдено в базе данных.")
        return

    # Формируем текст опроса
    question = f"Хотите ли вы посетить '{event_details['place_name']}'?"
    options = ["Да", "Нет"]
    link_text = f"[Ссылка на место]({event_details['place_link']})"
    start_time = event_details['start_time'].strftime("%Y-%m-%d %H:%M")
    additional_info = f"Начало: {start_time}\n{link_text}"

    # Получаем список всех пользователей, которые зарегистрировались
    users = get_all_users()

    for user_id, tg_tag in users:
        try:
            # Отправка опроса в личные сообщения каждому пользователю
            poll_message = await context.bot.send_poll(
                chat_id=user_id,
                question=question,
                options=options,
                is_anonymous=False,              # Публичный опрос
                allows_multiple_answers=False     # Одиночный ответ
            )

            # Отправка дополнительной информации в личные сообщения
            await context.bot.send_message(
                chat_id=user_id,
                text=additional_info,
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    await update.message.reply_text("Опрос отправлен в личные сообщения всем зарегистрированным пользователям.")

# Функция для обработки ответов на опрос
async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем информацию о ответе на опрос
    poll_answer = update.poll_answer
    user_id = poll_answer.user.id
    poll_id = poll_answer.poll_id  # poll_id опроса
    selected_option_text = poll_answer.option_ids[0]  # Текст выбранной опции

    # Определяем match на основе выбранной опции
    match = selected_option_text == "Да"  # Если выбрал "Да", match = True

    # Сохраняем результат голосования в базе данных
    save_poll_result(user_id, poll_id, match)

# Функция для сохранения результата в базе данных
def save_poll_result(user_id, poll_id, match):
    try:
        db = DB_connect.DB()
        connection = db.get_conn()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO petrenko_test.users_options (user_id, poll_id, match)
            VALUES (%s, %s, %s)
        """, (user_id, poll_id, match))  # Добавляем option_id
        connection.commit()

    except Exception as e:
        logger.error("Ошибка при сохранении результата опроса: %s", e)

    finally:
        cursor.close()
        connection.close()

# Функция для проверки и добавления пользователя в базу данных
def check_and_add_user(user_id, tg_tag):
    db = DB_connect.DB()
    connection = db.get_conn()
    cursor = connection.cursor()

    # Проверяем, есть ли пользователь в базе
    cursor.execute("""
        SELECT id FROM petrenko_test.users WHERE id = %s
    """, (user_id,))
    user_exists = cursor.fetchone() is not None

    # Если пользователя нет, добавляем его
    if not user_exists:
        cursor.execute("""
            INSERT INTO petrenko_test.users (id, tg_tag)
            VALUES (%s, %s)
        """, (user_id, tg_tag))
        connection.commit()

    if cursor:
        cursor.close()
    if connection:
        connection.close()
    return user_exists

# Хендлер для команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    tg_tag = user.username if user.username else f"{user.first_name} {user.last_name or ''}"

    # Проверяем и добавляем пользователя в базу данных
    user_exists = check_and_add_user(user_id, tg_tag)

    # Отправляем соответствующее сообщение
    if user_exists:
        await update.message.reply_text("Вы уже зарегистрированы.")
    else:
        await update.message.reply_text(
            f"Привет, {user.first_name}! Вы успешно зарегистрированы как {tg_tag}."
        )

def main() -> None:
    application = Application.builder().token("7755010868:AAHq4MoVsoeHM1_XcVBV9m8tbnQcJppsvHI").build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("create_event", create_event))
    application.add_handler(CommandHandler("poll", poll_event))
    application.add_handler(PollAnswerHandler(handle_poll_answer))  # Обработка ответов на опрос

    application.run_polling(allowed_updates=Update.ALL_TYPES)
