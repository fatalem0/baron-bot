import logging

from peewee import IntegrityError
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from baron.commands.create_event import create_event
from baron.models.models import db, User, Event

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_tag = update.effective_user.username
    user_id = update.effective_user.id

    logger.info(f"Received /start from user: {tg_tag} with ID: {user_id}")

    if db.is_closed():
        db.connect()

    try:
        user, created = User.get_or_create(id=user_id, defaults={'tg_tag': tg_tag})
        if created:
            await update.message.reply_text(f"Welcome, {tg_tag}! You have been registered.")
            logger.info(f"New user registered: {tg_tag}")
        else:
            await update.message.reply_text(f"Welcome back, {tg_tag}!")
            logger.info(f"Returning user: {tg_tag}")
    except IntegrityError as e:
        logger.error(f"Error inserting user {tg_tag}: {e}")
        await update.message.reply_text("An error occurred while registering. Please try again.")
    finally:
        if not db.is_closed():
            db.close()


logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

token = '7848117850:AAFGNZYd_8vaV9w4E6dfXY3xPlYhMQxtLhA'
def main() -> None:
    db.bind([User, Event], bind_refs=False, bind_backrefs=False)

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("create_event", create_event))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
