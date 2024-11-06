from peewee import IntegrityError
from telegram import Update
from telegram.ext import ContextTypes

from baron.models.models import db, User, Event, UserEvent

async def create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_names = update.message.text.split(' ')[1:]

    author_id = update.effective_user.id

    # Start a database transaction
    with db.atomic():
        # Create the event with the specified min_person_cnt
        event = Event.create(
            user=author_id,
            min_person_cnt=5,
            created_at=None,
            status_id="pending"
        )

        print(f"Created event with ID: {event.id}")

        user_instances = []
        for tg_name in tg_names:
            try:
                # Attempt to retrieve the user; do not create a new one
                user = User.get(User.tg_tag == tg_name)
                print(f"User found: {tg_name}")

                # Add the found user instance to the list
                user_instances.append(user)

            except User.DoesNotExist:
                # If the user does not exist, raise an error and stop execution
                raise ValueError(f"User with username '{tg_name}' does not exist in the database.")

        # Create UserEvent entries for each user in the event_group (UserEvent) table
        for user in user_instances:
            try:
                UserEvent.create(
                    user=user,
                    event=event,
                    joined_at=None
                )
                print(f"Linked user {user.id} to event {event.id}")
            except IntegrityError:
                print(f"User {user.id} is already linked to event {event.id}")

    print(f"Event {event.id} with users created successfully.")
    return event  # Return the created event instance for further use if needed
