from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from baron.events import delete_event_by_id


async def cancel_event_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите event_id.")
        return

    try:
        event_id = int(context.args[0])  # Получаем event_id из команды
    except ValueError:
        await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
        return

    delete_event_by_id(event_id)

    msg = (
        f"Жаль! Событие с ID = {event_id} было отменено\n"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
