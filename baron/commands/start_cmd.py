import logging

from peewee import IntegrityError
from telegram import Update
from telegram.ext import ContextTypes

from baron.models import db, Users

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    user_id = update.effective_user.id

    logger.info(f"Received /start from user: {username} with ID: {user_id}")

    if db.is_closed():
        db.connect()

    try:
        user, created = Users.get_or_create(id=user_id, defaults={'username': username})
        if created:
            await update.message.reply_text(f"Welcome, {username}! You have been registered.")
            logger.info(f"New user registered: {username}")
        else:
            await update.message.reply_text(f"Welcome back, {username}!")
            logger.info(f"Returning user: {username}")
    except IntegrityError as e:
        logger.error(f"Error inserting user {username}: {e}")
        await update.message.reply_text("An error occurred while registering. Please try again.")
    finally:
        if not db.is_closed():
            db.close()
