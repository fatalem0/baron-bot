import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, PollAnswerHandler

from baron.commands import help_cmd
from baron.commands.create_event_cmd import set_date, set_place, opt_set_attendees, set_min_attendees, \
    finish_create_event, create_event_cmd, DATE, PLACE, ATTENDEES, MIN_ATTENDEES, FINISH_CREATE_EVENT
from baron.commands.poll import poll_event
from baron.commands.start_cmd import start_cmd
from configs.models import Config

from baron.commands.create_payment import register_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main(config: Config) -> None:
    application = Application.builder().token(config.telegram_token).build()

    handles = [
        CommandHandler("start", start_cmd),
        ConversationHandler(
            entry_points=[CommandHandler("create_event", create_event_cmd)],
            states={
                DATE: [MessageHandler(filters.TEXT, set_date)],
                PLACE: [MessageHandler(filters.TEXT, set_place)],
                ATTENDEES: [MessageHandler(filters.TEXT, opt_set_attendees)],
                MIN_ATTENDEES: [MessageHandler(filters.TEXT, set_min_attendees)],
                FINISH_CREATE_EVENT: [MessageHandler(filters.TEXT, finish_create_event)]
            },
            fallbacks=[]
        ),
        CommandHandler("help", help_cmd),
        CommandHandler("poll", poll_event),
        #PollAnswerHandler(handle_poll_answer)
    ]

    register_handlers(application)
    for handle in handles:
        application.add_handler(handle)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
