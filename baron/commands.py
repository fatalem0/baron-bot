import logging

from peewee import IntegrityError
from telegram import Update, constants
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes

from baron.events import create_event_cmd
from baron.models import db, Users
from baron.users import find_user_by_id
from configs.models import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

DATE, PLACE, ATTENDEES, MIN_ATTENDEES, FINISH_CREATE_EVENT = range(5)


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def _create_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Захотели собраться? А что за повод-то?")

    context.chat_data['is_group'] = update.message.chat.type == constants.ChatType.PRIVATE

    return DATE


async def _set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['event_name'] = update.message.text

    logger.info(
        "Пользователь %s создает мероприятие под названием '%s'",
        update.message.from_user.username,
        context.chat_data['event_name']
    )

    await update.message.reply_text(
        "Когда-нибудь вы обязательно соберётесь... Нет, серьёзно, а когда?"
    )

    return PLACE


async def _set_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['event_date'] = update.message.text

    logger.info(
        "Пользователь %s выбрал дату мероприятия '%s' - %s",
        update.message.from_user.username,
        context.chat_data['event_name'],
        context.chat_data['event_date']
    )

    await update.message.reply_text(
        "Где соберётесь?"
    )

    if context.chat_data.get('is_group', False):
        chat_id = update.message.chat_id
        chat_members = await context.bot.getChatMember(chat_id)
        chat_members_usernames = [member.user.username for member in chat_members]
        context.chat_data['event_attendees'] = chat_members_usernames
        return MIN_ATTENDEES
    else:
        return ATTENDEES


async def _opt_set_attendees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['event_place'] = update.message.text

    logger.info(
        "Пользователь %s выбрал место мероприятия '%s' - %s",
        update.message.from_user.username,
        context.chat_data['event_name'],
        context.chat_data['event_place']
    )

    await update.message.reply_text(
        "Кого позовёте? Напишите имена пользователей в формате @user, каждое с новой строки"
    )

    return MIN_ATTENDEES


async def _set_min_attendees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.chat_data.get('event_attendees', False):
        context.chat_data['event_attendees'] = update.message.text.strip().split('\n')

    logger.info(
        "Пользователь %s выбрал участников мероприятия '%s' - %s",
        update.message.from_user.username,
        context.chat_data['event_name'],
        context.chat_data['event_attendees']
    )

    await update.message.reply_text(
        "Магическое число под конец - сколько минимум человек должно быть?"
    )

    return FINISH_CREATE_EVENT


async def _finish_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_author_name = update.message.from_user.username
    user_id = update.effective_user.id

    event_author_id = find_user_by_id(user_id)
    event_name = context.chat_data['event_name'],
    event_date = context.chat_data['event_date'],
    event_place = context.chat_data['event_place'],
    event_attendees = context.chat_data['event_attendees'],
    event_min_attendees = update.message.text

    new_event_id = create_event_cmd(
        event_author_id,
        event_name,
        event_date,
        event_place,
        event_attendees,
        event_min_attendees
    )

    logger.info(
        """
        event_author_id = %s,
        event_author_name = %s,
        event_id = %s,
        event_name = %s,
        event_date = %s,
        event_place = %s,
        event_attendees = %s,
        event_min_attendees = %s
        """,
        event_author_id,
        event_author_name,
        new_event_id,
        event_name,
        event_date,
        event_place,
        event_attendees,
        event_min_attendees
    )

    finish_msg = (
        f"Готово! ID вашего мероприятия - {new_event_id}\n"
        f"📢Событие - {event_name}\n"
        f"📍Место - {event_place}\n"
        f"🕒Время - {event_date}\n"
        f"Участники - {event_attendees}\n"
        f"Минимальное количество человек - {event_min_attendees}\n"
        "Уведомление для голосования отправлено участникам\n"
    )

    await update.message.reply_text(finish_msg, parse_mode=ParseMode.MARKDOWN)

    return ConversationHandler.END


async def _help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "BarON бот\n"
        "---------\n"
        "Команды:"
        "*/create_event:* Создать мероприятие\n"
        "*/help:* Вывести все команды\n"
    )

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


def main(config: Config) -> None:
    application = Application.builder().token(config.telegram_token).build()

    handles = [
        CommandHandler("start", _start),
        ConversationHandler(
            entry_points=[CommandHandler("create_event", _create_event_command)],
            states={
                DATE: [MessageHandler(filters.TEXT, _set_date)],
                PLACE: [MessageHandler(filters.TEXT, _set_place)],
                ATTENDEES: [MessageHandler(filters.TEXT, _opt_set_attendees)],
                MIN_ATTENDEES: [MessageHandler(filters.TEXT, _set_min_attendees)],
                FINISH_CREATE_EVENT: [MessageHandler(filters.TEXT, _finish_create_event)]
            },
            fallbacks=[]
        ),
        CommandHandler("help", _help_command)
    ]

    for handle in handles:
        application.add_handler(handle)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
