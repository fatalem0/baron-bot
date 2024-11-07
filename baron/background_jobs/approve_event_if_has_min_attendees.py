import logging

from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from baron.models import Events, UsersEvents, Users, EventOptions
from baron.users import find_user_by_id

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def approve_event_if_has_min_attendees(context: ContextTypes.DEFAULT_TYPE):
    created_events = Events.select().where(Events.status_id == 'created')

    for event in created_events:
        attendees_count = UsersEvents.select().where(UsersEvents.event_id == event.id).count()

        if attendees_count >= event.min_attendees:
            # Если набрали минимальное количество, то обновляем статус события на 'approved'
            event.status_id = 'approved'
            event.save()

            attendees = UsersEvents.select(Users).join(Users).where(UsersEvents.event_id == event.id)
            attendees_with_at_symbol = ', '.join(['@' + attendee.username for attendee in attendees.objects()])

            logger.info(f'approve_event_if_has_min_attendees attendees - {attendees}')

            try:
                event_options = EventOptions.get_or_none(EventOptions.event_id == event.id)
                event_author: Users = find_user_by_id(event.author_id)

                sent_to_others_message = (
                    f"✅Событие '{event.name}' согласовано!\n"
                    f"🏆Организатор события - {event_author.username}\n"
                    f"📍Место - {event_options.place}\n"
                    f"📌Адрес - {event.latitude}, {event.longitude}\n"
                    f"🕒Время - {event_options.date}\n"
                    f"🫂Участники - {attendees_with_at_symbol}\n"
                )

                for attendee in attendees.objects():
                    try:
                        await context.bot.send_message(chat_id=attendee.with_bot_chat_id, text=sent_to_others_message,
                                                       parse_mode=ParseMode.MARKDOWN)
                    except TelegramError as e:
                        logger.error(f"Ошибка при отправке сообщения пользователю {attendee.username}: {e}")
            except TelegramError as e:
                logger.error(f"Ошибка при подтверждении события {event.name} {event.name}: {e}")
