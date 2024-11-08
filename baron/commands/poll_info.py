import logging

from peewee import fn
from telegram import Update
from telegram.ext import ContextTypes

from baron.events import find_event_by_id
from baron.models import UserOption, EventOptions, Events

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def poll_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите event_id.")
        return

    try:
        event_id = int(context.args[0])  # Получаем event_id из команды
    except ValueError:
        await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
        return

    event = find_event_by_id(event_id)
    if event is None:
        await update.message.reply_text("Мероприятия с таким id не найдено. Пожалуйста, укажите существующее.")
        return

    event_options = (
        UserOption
        .select(UserOption.option_id, EventOptions.place, EventOptions.date, fn.COUNT(UserOption.user_id).alias('count'))
        .join(EventOptions)
        .where(
            (EventOptions.event_id == event_id) &
            (UserOption.status == 'confirmed')
        )
        .group_by(UserOption.option_id, EventOptions.place, EventOptions.date)
        .order_by(fn.COUNT(UserOption.user_id).desc())
        .limit(10)
    )

    results = f"Результаты голосования по событию {event_id}:\n"
    cnt = 1

    for option in event_options:
        results += f"{cnt}) Место - \"{option.option_id.place}\", Время - \"{option.option_id.date}\", За: {option.count}\n"
        cnt += 1

    logger.info(results)
    await update.message.reply_text(results)


