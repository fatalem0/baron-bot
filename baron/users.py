import logging

from peewee import IntegrityError

from baron.models import Users, db, UsersEvents

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def find_user_by_id(id):
    if db.is_closed():
        db.connect()

    try:
        return Users.get(Users.id == id).id
    finally:
        if not db.is_closed():
            db.close()


def find_user_by_username(username):
    user = Users.get_or_none(Users.username == username)

    if user is None:
        logger.error(f"Пользователь с именем {username} не найден")
    else:
        logger.info(f"Пользователь с именем {username} найден")

    return user


def delete_user_from_event(user_id):
    try:
        UsersEvents.delete().where(UsersEvents.user_id == user_id).execute()
        logger.info(f"Запись с user_id = {user_id} удалена из таблицы users_events")
    except IntegrityError as ex:
        logger.error(f'Ошибка при записи с user_id = {user_id} из таблицы users_events: {ex}')
