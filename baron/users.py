import logging

from baron.models import Users, db

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
