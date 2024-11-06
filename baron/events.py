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
    try:
        with db.atomic():
            new_event = Events.create(
                author_id=event_author_id,
                name=event_name,
                min_attendees=event_min_attendees
            )
            EventOptions.create(
                event_id=new_event.id,
                date=event_date,
                place=event_place,
                author_id=event_author_id
            )
            for attendee in event_attendees:
                attendee_id = find_user_by_username(attendee)
                UsersEvents.create(
                    user_id=attendee_id,
                    event_id=new_event.id
                )
            return new_event.id
    except IntegrityError as ex:
        logger.error(ex)
