import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, ContextTypes

from baron.events import create_event, find_event_by_id, create_option, get_event_members
from baron.users import find_user_by_id, delete_user_from_event, find_user_by_username

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

OPTION_DATE, OPTION_PLACE, FINISH_CREATE_OPTION = range(3)



async def add_option_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите event_id.")
        return

    try:
        event_id = int(context.args[0])  # Получаем event_id из команды
    except ValueError:
        await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
        return

    event = find_event_by_id(event_id)
    if event is None:
        await update.message.reply_text("Мероприятия с таким id не найдено. Пожалуйста, укажите существующее.")
        return

    context.chat_data['event_id'] = event_id

    await update.message.reply_text(
        "Значит, тебе что-то не нравится? Ну хорошо - предлагай свое время для встречи"
    )
    context.chat_data['is_group'] = update.message.chat.type != 'private'

    return OPTION_DATE



async def set_option_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['event_date'] = update.message.text

    logger.info(
        "Пользователь %s создает вариант мероприятия со временем проведения %s",
        update.message.from_user.username,
        context.chat_data['event_date']
    )

    await update.message.reply_text(
        "Теперь напиши куда идем, только без банальностей, пожалуйста.."
    )

    return OPTION_PLACE


async def set_option_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['event_place'] = update.message.text

    logger.info(
        "Пользователь %s предлагает место %s для проведения мероприятия",
        update.message.from_user.username,
        context.chat_data['event_place']
    )

    event_id = context.chat_data['event_id']
    user_id = update.effective_user.id

    option_author_id = find_user_by_id(user_id)
    event_date = context.chat_data['event_date']
    event_place = context.chat_data['event_place']

    new_option_id = create_option(
        event_id,
        event_date,
        event_place,
        option_author_id
    )

    logger.info("Опция %s добавлена", new_option_id)


    attendees = get_event_members(event_id)
    found_attendee_with_bot_chat_ids = [found_attendee.with_bot_chat_id for found_attendee in attendees]

    for attendee_with_bot_chat_id in found_attendee_with_bot_chat_ids:
        await context.bot.send_message(
            chat_id=attendee_with_bot_chat_id,
            text=f"Добавился новый вариант досуга на мероприятие {event_id}, чтобы заново проголосовать, введи команду /poll {event_id}",
            parse_mode=ParseMode.MARKDOWN,
        )

    return ConversationHandler.END