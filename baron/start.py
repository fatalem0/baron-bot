import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, PollAnswerHandler, \
    CallbackQueryHandler

from baron.commands.add_option import add_option_cmd, FINISH_CREATE_OPTION, OPTION_DATE, OPTION_PLACE
from baron.commands.cancel_event_cmd import cancel_event_cmd
from baron.commands.create_event_cmd import set_date, set_place, opt_set_attendees, set_min_attendees, \
    finish_create_event, create_event_cmd, DATE, PLACE, ATTENDEES, MIN_ATTENDEES, FINISH_CREATE_EVENT, \
    create_event_callback
from baron.commands.create_payment import create_payment, handle_buttons, photo_handler, \
    button_handler
from baron.commands.help_cmd import help_cmd
from baron.commands.poll import poll_event, handle_poll_answer
from baron.commands.start_cmd import start_cmd
from configs.models import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main(config: Config) -> None:
    application = Application.builder().token(config.telegram_token).build()

    handlers = [
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
        CallbackQueryHandler(create_event_callback),

        CommandHandler("cancel_event", cancel_event_cmd),

        CommandHandler("help", help_cmd),

        CommandHandler("poll", poll_event),
        PollAnswerHandler(handle_poll_answer),

        CommandHandler("create_payment", create_payment),
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_buttons),
        MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, photo_handler),
        CallbackQueryHandler(button_handler, pattern='button_clicked'),

        ConversationHandler(
            entry_points=[CommandHandler("add_option", add_option_cmd)],
            states={
                OPTION_DATE: [MessageHandler(filters.TEXT, set_date)],
                OPTION_PLACE: [MessageHandler(filters.TEXT, set_place)],
                FINISH_CREATE_OPTION: [MessageHandler(filters.TEXT, finish_create_event)]
            },
            fallbacks=[]
        ),

    ]

    for handler in handlers:
        application.add_handler(handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
