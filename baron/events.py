import logging

from peewee import IntegrityError, DoesNotExist

from baron.models import Events, db, EventOptions, UsersEvents, Users
from baron.users import find_user_by_username

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def create_event(
        event_author_id,
        event_name,
        event_date,
        event_place,
        event_attendees,
        event_min_attendees,
        event_latitude,
        event_longitude
):
    logger.info(
        """
        Пытаемся создать ивент
        event_author_id = %s,
        event_name = %s,
        event_date = %s,
        event_place = %s,
        event_attendees = %s,
        event_min_attendees = %s,
        event_latitude = %s,
        event_longitude = %s
        """,
        event_author_id,
        event_name,
        event_date,
        event_place,
        event_attendees,
        event_min_attendees,
        event_latitude,
        event_longitude
    )
    try:
        with db.atomic():
            new_event = Events.create(
                author_id=event_author_id,
                name=event_name,
                min_attendees=event_min_attendees,
                latitude=event_latitude,
                longitude=event_longitude,
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


def delete_event_by_id(event_id):
    try:
        with db.atomic():
            EventOptions.delete().where(EventOptions.event_id == event_id).execute()
            logger.info(f'Записb в таблице event_options с ID = {event_id} удалены')
            UsersEvents.delete().where(UsersEvents.event_id == event_id).execute()
            logger.info(f'Записи в таблице users_events с ID = {event_id} удалены')
            Events.delete().where(Events.id == event_id).execute()
            logger.info(f'Запись в таблице events с ID = {event_id} удалена')
    except IntegrityError as ex:
        logger.error(f'Ошибка при удалении ивента с ID = {event_id}: {ex}')


def find_event_by_id(event_id):
    try:
        return Events.get(Events.id == event_id)
    except DoesNotExist:
        logger.error(f'Event with ID {event_id} does not exist.')
        return None
    except IntegrityError as ex:
        logger.error(f'Error finding event with ID {event_id}: {ex}')
        return None


def create_option(event_id, option_date, option_place, option_author_id):
    logger.info(
        """
        Пытаемся создать опцию
        event_id = %s,
        option_date = %s,
        option_place = %s,
        option_author_id = %s
        """, event_id, option_date, option_place, option_author_id)
    try:
        with db.atomic():
            option = EventOptions.create(
                event_id=event_id,
                date=option_date,
                place=option_place,
                author_id=option_author_id
            )
            logger.info('Создана запись в таблице event_options')
            return option.id
    except IntegrityError as ex:
        logger.error(f'Error creating event_option with for event with ID {event_id}: {ex}')


def get_event_members(event_id):
    try:
        user_ids = UsersEvents.select(UsersEvents.user_id).where(UsersEvents.event_id == event_id)
        return Users.select().where(Users.id.in_(user_ids))
    except DoesNotExist:
        logger.error(f"No members found for event with ID {event_id}.")
        return []
    except Exception as ex:
        logger.error(f"Error retrieving members for event with ID {event_id}: {ex}")
        return []