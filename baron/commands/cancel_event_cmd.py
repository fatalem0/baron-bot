import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from baron.events import delete_event_by_id, find_event_by_id
from baron.models import UsersEvents, Users, EventOptions
from baron.users import find_user_by_username, find_user_by_id

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def cancel_event_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите event_id.")
        return

    try:
        event_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
        return

    username = update.effective_user.username
    user_id = update.effective_user.id
    with_bot_chat_id = update.effective_chat.id

    logger.info(f"Вызов команды /cancel_event от {username} с ID = {user_id} в чате {with_bot_chat_id}")

    found_user = find_user_by_username(username)

    if not found_user:
        msg = (
            "Неплохая попытка, но ты не можешь вызвать эту команду!\n"
            "Сначала мне нужно тебя запомнить - пропиши команду /start\n"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    found_event = find_event_by_id(event_id)

    if found_event:
        logger.info(f'found_event.author_id = {found_event.author_id}')
        logger.info(f'found_user.id = {found_user.id}')
        if str(found_user.id) != str(found_event.author_id):
            await update.message.reply_text("Ты не автор события! Даже не пробуй его удалять")
            return

        attendees = UsersEvents.select(Users).join(Users).where(UsersEvents.event_id == found_event.id)
        event = find_event_by_id(event_id)
        event_options = EventOptions.get_or_none(EventOptions.event_id == event_id)
        event_author_name = find_user_by_id(event.author_id)

        delete_event_by_id(event_id)

        sent_to_others_message = (
            f"❌Событие '{found_event.name}' отменено\n"
            f"🏆Организатор события - {event_author_name}\n"
            f"📍Место - {event_options.place}\n"
            f"📌Адрес - {event.latitude}, {event.longitude}\n"
            f"🕒Время - {event_options.date}\n"
        )

        await update.message.reply_text(sent_to_others_message, parse_mode=ParseMode.MARKDOWN)

        for attendee in attendees.objects():
            try:
                await context.bot.send_message(chat_id=attendee.with_bot_chat_id, text=sent_to_others_message,
                                               parse_mode=ParseMode.MARKDOWN)
            except TelegramError as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {attendee.username}: {e}")
    else:
        await update.message.reply_text('Ты что, выпил?. Такого события не существует')
