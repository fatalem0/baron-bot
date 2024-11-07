import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, \
    CallbackQueryHandler

from baron.commands.add_option import add_option_cmd, FINISH_CREATE_OPTION, OPTION_DATE, OPTION_PLACE, set_option_date, \
    set_option_place
from baron.background_jobs.start_background_jobs import start_background_jobs
from baron.commands.approve_event_cmd import approve_event_cmd
from baron.commands.cancel_event_cmd import cancel_event_cmd
from baron.commands.create_event_cmd import set_date, set_place, set_location, opt_set_attendees, set_min_attendees, \
    finish_create_event, create_event_cmd, DATE, PLACE, LOCATION, ATTENDEES, MIN_ATTENDEES, FINISH_CREATE_EVENT, \
    create_event_callback
from baron.commands.create_payment import register_handlers
from baron.commands.help_cmd import help_cmd
from baron.commands.nearby_cmd import nearby_change_handlers
from baron.commands.poll import poll_event, handle_poll_selection
from baron.commands.start_cmd import start_cmd
from configs.models import Config, load_config_global

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main(config: Config = load_config_global()) -> None:
    application = Application.builder().token(config.telegram_token).build()

    handlers = \
        nearby_change_handlers() + [
        CommandHandler("start", start_cmd),

        ConversationHandler(
            entry_points=[CommandHandler("create_event", create_event_cmd)],
            states={
                DATE: [MessageHandler(filters.TEXT, set_date)],
                PLACE: [MessageHandler(filters.TEXT, set_place)],
                LOCATION: [MessageHandler(filters.TEXT, set_location)],
                ATTENDEES: [MessageHandler(filters.TEXT | filters.LOCATION, opt_set_attendees)],
                MIN_ATTENDEES: [MessageHandler(filters.TEXT, set_min_attendees)],
                FINISH_CREATE_EVENT: [MessageHandler(filters.TEXT, finish_create_event)]
            },
            fallbacks=[]
        ),
        CallbackQueryHandler(create_event_callback, pattern="mogu"),
        CallbackQueryHandler(create_event_callback, pattern="ne_mogu"),

        CommandHandler("approve_event", approve_event_cmd),
        CommandHandler("cancel_event", cancel_event_cmd),
        CommandHandler("help", help_cmd),
        CommandHandler("poll", poll_event),
        CallbackQueryHandler(handle_poll_selection, pattern='^.*$'),

        ConversationHandler(
            entry_points=[CommandHandler("add_option", add_option_cmd)],
            states={
                OPTION_DATE: [MessageHandler(filters.TEXT, set_option_date)],
                OPTION_PLACE: [MessageHandler(filters.TEXT, set_option_place)]
            },
            fallbacks=[]
        ),
    ]

    for handler in handlers:
        application.add_handler(handler)

    register_handlers(application)

    application.post_init = start_background_jobs

    application.run_polling(allowed_updates=Update.ALL_TYPES)
