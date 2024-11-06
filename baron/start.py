import logging

from telegram import Update
from telegram.ext import Application, CommandHandler

from configs.models import Config

from baron.commands.create_event import create_event

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main(config: Config) -> None:
    application = Application.builder().token(config.telegram_token).build()

    application.add_handler(CommandHandler("create_event", create_event))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
