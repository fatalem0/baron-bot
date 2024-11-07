import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from baron.events import find_event_by_id
from baron.models import UsersEvents, Users
from baron.users import find_user_by_username

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def approve_event_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    found_user = find_user_by_username(username)

    if not found_user:
        await update.message.reply_text("Не нашли тебя в БД, сорян(")
        return

    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите event_id.")
        return

    try:
        event_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
        return

    found_event = find_event_by_id(event_id)

    if found_event:
        logger.info(f'found_event.author_id = {found_event.author_id}')
        logger.info(f'found_user.id = {found_user.id}')
        if found_user.id != found_event.author_id:
            await update.message.reply_text("Ты не автор события! Даже не пробуй его подтверждать")
            return

        attendees = UsersEvents.select(Users).join(Users).where(UsersEvents.event_id == found_event.id)
        attendees_with_at_symbol = ', '.join(['@' + attendee.username for attendee in attendees])

        sent_to_others_message = (
            f"✅Событие '{found_event.name}' согласовано!\n"
            # f"📍Место - {found_event.}\n"
            # f"🕒Время - {event_date}\n"
            f"🫂Участники - {attendees_with_at_symbol}\n"
        )

        for attendee in attendees.objects():
            try:
                await context.bot.send_message(chat_id=attendee.with_bot_chat_id, text=sent_to_others_message,
                                               parse_mode=ParseMode.MARKDOWN)
            except TelegramError as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {attendee.username}: {e}")
    else:
        await update.message.reply_text('Ты что, выпил?. Такого события не существует')
