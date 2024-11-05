import logging

from telegram import Update
from telegram.ext import Application, CommandHandler

from baron.commands.create_event import create_event

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    application = Application.builder().token("TOKEN").build()

    application.add_handler(CommandHandler("create_event", create_event))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
