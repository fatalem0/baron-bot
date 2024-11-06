from peewee import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🍻BarON бот🍻\n"
        "---------\n"
        "Команды:\n"
        "*/create_event:* Создать мероприятие\n"
        "*/help:* Вывести все команды\n"
    )

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
