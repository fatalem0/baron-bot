from peewee import IntegrityError

from baron.models import Events, db, EventOptions, UsersEvents


def create_event(event_author_id, event_name, event_date, event_place, event_attendees, event_min_attendees):
    try:
        with db.atomic():
            new_event = Events.create(
                author_id=event_author_id
            )
            EventOptions.create(
                name=event_name,
                date=event_date,
                place=event_place,
                min_attendees=event_min_attendees
            )
            for attendee in event_attendees:
                UsersEvents.create(
                    event_id=new_event.id,
                    user_id=attendee.id
                )
            return new_event.id
    except IntegrityError:
        pass