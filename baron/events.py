import logging

from peewee import IntegrityError

from baron.models import Events, db, EventOptions, UsersEvents
from baron.users import find_user_by_username

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def create_event(event_author_id, event_name, event_date, event_place, event_attendees, event_min_attendees):
    logger.info(
        """
        Пытаемся создать ивент
        event_author_id = %s,
        event_name = %s,
        event_date = %s,
        event_place = %s,
        event_attendees = %s,
        event_min_attendees = %s
        """,
        event_author_id,
        event_name,
        event_date,
        event_place,
        event_attendees,
        event_min_attendees
    )

    try:
        with db.atomic():
            new_event = Events.create(
                author_id=event_author_id,
                name=event_name,
                min_attendees=event_min_attendees
            )
            logger.info('Создана запись в таблице events')
            EventOptions.create(
                event_id=new_event.id,
                date=event_date,
                place=event_place,
                author_id=event_author_id
            )
            logger.info('Создана запись в таблице event_options')

            found_attendees = []
            for attendee in event_attendees:
                logger.info(f'Пытаемся найти пользователя {attendee}')
                found_attendee = find_user_by_username(attendee)

                if found_attendee:
                    attendee_id = found_attendee.id
                    UsersEvents.create(
                        user_id=attendee_id,
                        event_id=new_event.id
                    )
                    found_attendees.append(found_attendee)
                    logger.info('Создана запись в таблице users_events')
                else:
                    logger.info('Запись в таблице users_events не была создана')
            return new_event.id, found_attendees
    except IntegrityError as ex:
        logger.error(f'Ошибка при создании ивента: {ex}')
