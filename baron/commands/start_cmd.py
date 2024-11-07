import logging

from peewee import IntegrityError
from telegram import Update
from telegram.ext import ContextTypes

from baron.models import db, Users

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    user_id = update.effective_user.id
    with_bot_chat_id = update.effective_chat.id

    logger.info(f"Вызов команды /start от {username} с ID = {user_id} в чате {with_bot_chat_id}")

    try:
        user, created = Users.get_or_create(id=user_id, defaults={'username': username},
                                            with_bot_chat_id=with_bot_chat_id)
        start_msg = (
            "🎉 Добро пожаловать в BarOn Bot! 🎉\n"
            "Надоело собирать всех своих друзей в бар? Давай сделаем это удобнее\n\n"
            "🔥 Что я могу сделать:\n"
            "- Создать сообщение с датой и местом, где хочешь собрать друзей, и переслать его \n"
            "- Устроить голосование по поводу даты и места \n"
            "- Собрать всех желающих в отдельный чат \n\n"
            "Чтобы узнать все мои команды, пиши /help"
        )
        if created:
            prefix_start_msg = (
                f"{username}, welcome to the club, buddy\n"
            )
            result_start_msg = prefix_start_msg + start_msg

            await context.bot.send_message(chat_id=with_bot_chat_id, text=result_start_msg)
            logger.info(f"Пользователь {username} успешно зарегистрирован")
        else:
            await context.bot.send_message(chat_id=with_bot_chat_id, text=start_msg)
    except IntegrityError as e:
        logger.error(f"Ошибка при создании пользователя {username}: {e}")
        await update.message.reply_text("Кажется, у нас технические шоколадки. Попробуй снова")
