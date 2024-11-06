import logging

from telegram.ext import ContextTypes

import DB_connect
from telegram import Update

from configs.models import load_config_global

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Функция для получения списка всех зарегистрированных пользователей из базы данных
def get_all_users():
    db = DB_connect.DB()
    connection = db.get_conn()
    cursor = connection.cursor()

    # Получаем всех пользователей
    cursor.execute(f"SELECT id, username FROM {load_config_global().schema}.users")
    users = cursor.fetchall()  # Список кортежей (user_id, tg_tag)

    if cursor:
        cursor.close()
    if connection:
        connection.close()
    return users


# Функция для подключения к базе данных PostgreSQL и получения данных о событии
def get_event_details(event_id: int):
    db = None
    connection = None
    cursor = None
    try:
        db = DB_connect.DB()
        connection = db.get_conn()
        cursor = connection.cursor()

        cursor.execute(
            f"SELECT event_id, date, place, place_link, created_at, author_id FROM {load_config_global().schema}.event_options "
            f"WHERE"
            f" event_id = %s;",
            (event_id,))
        result = cursor.fetchone()

        if result:
            event_id, date, place, place_link, created_at, author_id = result
            return {
                "place": place,
                "place_link": place_link,
                "date": date
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


# Функция для сохранения результата в базе данных
def save_poll_result(user_id, option_id, match):
    try:
        db = DB_connect.DB()
        connection = db.get_conn()
        cursor = connection.cursor()

        cursor.execute(f"""
            INSERT INTO {load_config_global().schema}.users_options (user_id, option_id, match)
            VALUES (%s, %s, %s)
        """, (user_id, option_id, match))
        connection.commit()

    except Exception as e:
        logger.error("Ошибка при сохранении результата опроса: %s", e)

    finally:
        cursor.close()
        connection.close()


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем информацию о ответе на опрос
    poll_answer = update.poll_answer
    user_id = poll_answer.user.id
    poll_id = poll_answer.poll_id  # poll_id опроса



    selected_option_text = poll_answer.option_ids[0]  # Текст выбранной опции

    # Определяем match на основе выбранной опции
    match = selected_option_text == 0  # Если выбрал "Да", match = True

    # Сохраняем результат голосования в базе данных
    save_poll_result(user_id, poll_id, match)


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
    question = f"Хотите ли вы посетить '{event_details['place']}'?"
    options = ["Да", "Нет"]
    link_text = f"[Ссылка на место]({event_details['place_link']})"
    date = event_details['date']
    additional_info = f"Начало: {date}\n{link_text}"

    # Получаем список всех пользователей, которые зарегистрировались
    users = get_all_users()

    for user_id, tg_tag in users:
        try:
            # Отправка опроса в личные сообщения каждому пользователю
            poll_message = await context.bot.send_poll(
                chat_id=user_id,
                question=question,
                options=options,
                is_anonymous=False,  # Публичный опрос
                allows_multiple_answers=False  # Одиночный ответ
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
