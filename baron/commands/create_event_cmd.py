import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, ContextTypes

from baron.events import create_event
from baron.users import find_user_by_id

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

DATE, PLACE, ATTENDEES, MIN_ATTENDEES, FINISH_CREATE_EVENT = range(5)


async def create_event_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Захотели собраться? А что за повод-то?")

    context.chat_data['is_group'] = update.message.chat.type != 'private'

    return DATE


async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def set_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    if context.chat_data['is_group']:
        chat_id = update.message.chat_id
        chat_members = await context.bot.getChatMembers(chat_id)
        chat_members_usernames = [member.user.username for member in chat_members]
        context.chat_data['event_attendees'] = chat_members_usernames
        return MIN_ATTENDEES
    else:
        return ATTENDEES


async def opt_set_attendees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['event_place'] = update.message.text

    logger.info(
        "Пользователь %s выбрал место мероприятия '%s' - %s",
        update.message.from_user.username,
        context.chat_data['event_name'],
        context.chat_data['event_place']
    )

    await update.message.reply_text(
        "Кого позовёте? Напишите имена пользователей, каждое с новой строки"
    )

    return MIN_ATTENDEES


async def set_min_attendees(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def finish_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_author_name = update.message.from_user.username
    user_id = update.effective_user.id

    event_author_id = find_user_by_id(user_id)
    event_name = context.chat_data['event_name']
    event_date = context.chat_data['event_date']
    event_place = context.chat_data['event_place']
    event_attendees = context.chat_data['event_attendees']
    event_min_attendees = update.message.text

    new_event_id, found_attendees = create_event(
        event_author_id,
        event_name,
        event_date,
        event_place,
        event_attendees,
        event_min_attendees
    )

    found_attendees_with_at_symbol = ', '.join(['@' + found_attendee.username for found_attendee in found_attendees])

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
        f"Готово! ID вашего события - {new_event_id}\n"
        f"📢Событие - {event_name}\n"
        f"📍Место - {event_place}\n"
        f"🕒Время - {event_date}\n"
        f"🫂Приглашенные участники - {found_attendees_with_at_symbol}\n"
        f"Минимальное количество человек - {event_min_attendees}\n"
        "Уведомление для голосования отправлено участникам\n"
    )

    await update.message.reply_text(finish_msg, parse_mode=ParseMode.MARKDOWN)

    sent_to_others_message = (
        f"Привет! {event_author_name} приглашает тебя на новое событие\n"
        f"📢Событие - {event_name}\n"
        f"📍Место - {event_place}\n"
        f"🕒Время - {event_date}\n"
        f"🫂Приглашенные участники - {found_attendees_with_at_symbol}\n"
        "Что скажешь?\n"
    )

    found_attendee_usernames = [found_attendee.username for found_attendee in found_attendees]
    not_found_attendee_usernames = list(set(event_attendees) - set(found_attendee_usernames))

    found_attendee_with_bot_chat_ids = [found_attendee.with_bot_chat_id for found_attendee in found_attendees]

    for attendee_with_bot_chat_id in found_attendee_with_bot_chat_ids:
        await context.bot.send_message(
            chat_id=attendee_with_bot_chat_id,
            text=sent_to_others_message,
            parse_mode=ParseMode.MARKDOWN
        )

    final_msg = (
        "Всё, теперь все в курсе про тусовку\n"
    )

    if not_found_attendee_usernames:
        final_msg += (
            f"У меня получилось достучаться до всех, кроме следующих персонажей: {', '.join('@' + not_found_attendee_username for not_found_attendee_username in not_found_attendee_usernames)}\n"
            "Кажется, они ещё не знают про меня. Поделись ссылкой на меня и приглашай их на тусовку!\n"
        )

    await update.message.reply_text(final_msg, parse_mode=ParseMode.MARKDOWN)

    return ConversationHandler.END
