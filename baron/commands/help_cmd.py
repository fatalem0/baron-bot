from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "🍻BarON бот🍻\n"
        "---------\n"
        "Команды:\n"
        "*/create_event:* Создать событие\n"
        "*/cancel_event {event_id}:* Отменить событие\n"
        "*/add_option {event_id}:* Добавить вариант, куда пойти"
        "*/poll_info {event_id}:* Увидеть результаты голосования онлайн"
        "*/help:* Вывести все команды\n"
    )

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
