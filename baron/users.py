import logging

from peewee import IntegrityError

from baron.models import Users, db, UsersEvents, UserOption

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def find_user_by_id(user_id):
    user = Users.get_or_none(Users.id == user_id)

    if user is None:
        logger.error(f"Пользователь с id = {user_id} не найден")
    else:
        logger.info(f"Пользователь с id = {user_id} найден")

    return user


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


def create_user_option(user_id, option_id):
    logger.info(
        """
        Пытаемся создать опцию, за которую проголосовал пользователь
        user_id = %s,
        option_id = %s
        """, user_id, option_id)
    try:
        UserOption.create(
            user_id=user_id,
            option_id=option_id
        )
        logger.info(f'Запись в таблице user_option, где user_id = {user_id}, option_id = {option_id} создана')
    except IntegrityError as ex:
        logger.error(f'Ошибка при создании записи, где user_id = {user_id}, option_id = {option_id} в таблице user_option: {ex}')
