from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from peewee import fn
from baron.models import  Events, EventOptions, UserOption
from baron.models import db


async def show_stats(update, context):
    # Подключаемся к базе данных, если соединение закрыто
    if db.is_closed():
        db.connect()

    # Получаем события с флагом 'pending'
    events = Events.select().where(Events.status_id == "pending")

    # Проверяем, есть ли события с таким статусом
    if not events.exists():
        await update.message.reply_text("Нет доступных событий в статусе 'pending'.")
        return

    # Создаем клавиатуру с кнопками для каждого события
    event_keyboard = [
        [InlineKeyboardButton(f"{event.name} (ID: {event.id})", callback_data=f"event_{event.id}")]
        for event in events
    ]

    # Отправляем сообщение с клавиатурой
    await update.message.reply_text(
        "Выберите событие для просмотра статистики:",
        reply_markup=InlineKeyboardMarkup(event_keyboard)
    )

async def handle_event_selection(update, context):
    # Получаем ID события из callback_data
    query = update.callback_query
    event_id = int(query.data.split('_')[1])

    # Проверяем наличие события
    event = Events.get_or_none(Events.id == event_id)
    if not event:
        await query.answer("Выбранное событие не найдено.")
        return

    # Получаем все варианты для выбранного события
    options = (
        EventOptions
        .select(EventOptions, fn.COUNT(UserOption.id).alias('votes'))
        .join(UserOption, on=(EventOptions.id == UserOption.option_id), join_type='LEFT_OUTER')
        .where(EventOptions.event == event)
        .group_by(EventOptions.id)
    )

    # Формируем сообщение с вариантами и количеством голосов
    options_text = "\n".join(
        f"{option.place} - {option.date.strftime('%Y-%m-%d %H:%M')} : {option.votes} голосов"
        for option in options
    )

    # Отправляем сообщение с информацией по вариантам события
    await query.message.reply_text(
        f"Событие: {event.name}\n\nДоступные варианты:\n{options_text}"
    )

# Регистрируем обработчики в диспетчере
#dispatcher.add_handler(CommandHandler("show_events", show_events))
#dispatcher.add_handler(CallbackQueryHandler(handle_event_selection, pattern="^event_"))
