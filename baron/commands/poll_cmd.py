import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes, ConversationHandler

from baron.commands.nearby_cmd import init_nearby_handler
from baron.events import find_event_by_id, get_event_members, create_option
from baron.models import EventOptions, UserOption
from baron.users import find_user_by_username, find_user_by_id, create_user_option

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

START_POLL, NEW_OPTION_ASK_PLACE, NEW_OPTION_END = range(3)


async def poll_cmd(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите ID события, например: /poll 123")
        return

    try:
        event_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный формат event_id. Пожалуйста, укажите числовое значение.")
        return
    username = update.effective_user.username
    user_id = update.effective_user.id
    with_bot_chat_id = update.effective_chat.id

    logger.info(f"Вызов команды /poll от {username} с ID = {user_id} в чате {with_bot_chat_id}")

    found_user = find_user_by_username(username)

    if not found_user:
        msg = (
            "Неплохая попытка, но ты не можешь вызвать эту команду!\n"
            "Сначала мне нужно тебя запомнить - пропиши команду /start\n"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    found_event = find_event_by_id(event_id)

    if not found_event:
        await update.message.reply_text(f"Событие с ID {event_id} не найдено.")
        return

    context.user_data['event_id'] = found_event.id
    context.user_data['event_name'] = found_event.name

    event_attendees = get_event_members(event_id)
    if not event_attendees:
        await update.message.reply_text('Не нашлись участники ивента - погодите это реально?')
        return

    context.user_data['event_attendees'] = event_attendees

    found_event_author = find_user_by_id(found_event.author_id)

    if not found_event_author:
        await update.message.reply_text('Не нашелся автор для ивента - погодите это реально?')
        return

    context.user_data['event_author_id'] = found_event_author.id
    context.user_data['event_author_name'] = found_event_author.username

    event_options = EventOptions.select().where(EventOptions.event_id == found_event.id)

    if not event_options.exists():
        await update.message.reply_text("Для указанного события нет доступных вариантов.")
        return

    event_info_msg = (
        f"Сейчас я покажу тебе варианты для события {event_id} - '{found_event.name}'\n"
        f"🏆Организатор события - {found_event_author.username}\n"
        # f"📍Место, за которое проголосовало большинство - {event_options.place}\n"
        # f"🕒Время, за которое проголосовало большинство - {event_options.date}\n"
        f"🫂Участники - {['@' + event_attendee.username for event_attendee in event_attendees]}\n"
    )

    user_options = UserOption.select().where(UserOption.user_id == user_id,
                                             UserOption.option_id.in_(
                                                 [event_option.id for event_option in event_options]))

    # Формируем клавиатуру с вариантами и метками "Выбрано" или "Отменить"
    reply_keyboard = [
        [
            InlineKeyboardButton("Предложить свой вариант", callback_data="new_option"),
            InlineKeyboardButton("А что есть рядом?", callback_data="adv_option")
        ]
    ]

    for event_option in event_options:
        user_selection = next(
            (user_option for user_option in user_options if user_option.option_id == event_option.id), None)
        status = "🍻" if user_selection and user_selection.status == "confirmed" else "❌"
        button_text = f"{event_option.place} - {event_option.date} ({status})"
        reply_keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{event_option.id}")])

    # Отправляем информацию о событии и клавиатуру
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await update.message.reply_text(
        event_info_msg,
        reply_markup=reply_markup
    )
    logger.info(f'/poll, reply_markup = {reply_markup}')
    logger.info('/poll закончен')

    return START_POLL


async def ask_for_date_when_new_option(update: Update, context: CallbackContext):
    if not update.callback_query:
        return

    query = update.callback_query

    logger.info(
        "Пользователь %s выбрал опцию 'Предложить свой вариант' для мероприятия с id = %s - '%s'",
        query.from_user.username,
        query.from_user.username,
        query.from_user.username
    )

    await update.effective_chat.send_message(
        "Значит, тебе что-то не нравится? Ну хорошо - предлагай свое время для встречи"
    )

    return NEW_OPTION_ASK_PLACE


async def ask_for_place_when_new_option(update: Update, context: CallbackContext):
    new_event_date = update.message.text
    context.user_data['event_date'] = new_event_date

    logger.info(
        "Пользователь %s предложил другую дату мероприятия '%s' - %s",
        update.effective_user.username,
        context.user_data['event_name'],
        new_event_date
    )

    await update.message.reply_text(
        "Теперь напиши куда идем, только без банальностей, пожалуйста.."
    )

    return NEW_OPTION_END


async def end_handling_new_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_author_id = context.user_data['event_author_id']
    event_author_name = context.user_data['event_author_name']

    event_id = context.user_data['event_id']
    event_name = context.user_data['event_name']
    event_attendees = context.user_data['event_attendees']
    attendees_with_at_symbol = ['@' + event_attendee.username for event_attendee in event_attendees]

    new_event_date = context.user_data['event_date']
    new_event_place = update.message.text

    changer_name = update.effective_user.username

    option_id = create_option(event_id, new_event_date, new_event_place, event_author_id)
    context.user_data['new_option_id'] = option_id

    create_user_option(
        update.effective_user.id,
        option_id
    )

    finish_msg = (
        f"Принял! Предложение для события с ID {event_id} создано и отправлено участникам\n"
        f"🏆Предложение от - {changer_name}\n"
        f"📢Событие - {event_name}\n"
        f"📍Предложенное место - {new_event_place}\n"
        f"🕒Предложенное время - {new_event_date}\n"
        f"🫂Приглашенные участники - {attendees_with_at_symbol}\n"
    )

    sent_to_others_message = (
        f"{changer_name} предлагает другой вариант для события с ID {event_id}\n"
        f"📍Предложенное место - {new_event_place}\n"
        f"🕒Предложенное время - {new_event_date}\n"
        "Остальное остаётся прежним:\n"
        f"🏆Организатор события - {event_author_name}\n"
        f"📢Событие - {event_name}\n"
        f"🫂Приглашенные участники - {attendees_with_at_symbol}\n"
        "Что скажешь?\n"
    )

    found_attendee_with_bot_chat_ids = [event_attendee.with_bot_chat_id for event_attendee in event_attendees]

    keyboard = [
        [InlineKeyboardButton("Согласен", callback_data='new_option_soglasen')],
        [InlineKeyboardButton("Не согласен", callback_data='new_option_ne_soglasen')]
    ]

    for attendee_with_bot_chat_id in found_attendee_with_bot_chat_ids:
        await context.bot.send_message(
            chat_id=attendee_with_bot_chat_id,
            text=sent_to_others_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text(finish_msg, parse_mode=ParseMode.MARKDOWN)

    return ConversationHandler.END


async def ask_for_date_when_new_option(update: Update, context: CallbackContext):
    event_id = context.user_data['event_id']
    await init_nearby_handler(event_id, update, context)

    return ConversationHandler.END


async def poll_new_option_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data
    user_id = query.from_user.id
    username = query.from_user.username
    logger.info(f'Ответ от пользователя {username} для команды /poll при выборе другого варианта события = {action}')

    if action == 'new_option_soglasen':
        msg = "Ну, это стыдно конечно - так явно переобуваться. Хорошо, я это запомню"
        create_user_option(
            user_id,
            context.user_data['new_option_id']
        )
        await context.bot.send_message(chat_id=user_id, text=msg)
    elif action == 'new_option_ne_soglasen':
        await context.bot.send_message(chat_id=user_id, text="Полехче жми кнопку, я тебя понял")

    await update.effective_message.edit_reply_markup(reply_markup=None)


# async def handle_poll_selection(update: Update, context: CallbackContext):
#     # Проверка на callback_query
#     if not update.callback_query:
#         return
#
#     query = update.callback_query
#     user_id = query.from_user.id
#     selection_text = query.data
#
#     # Обрабатываем нажатие на кнопку "Предложить свой вариант"
#     if selection_text == "new_option":
#         await handle_suggest_option(update, context)
#         variant = update.message.text
#         context.chat_data['is_group'] = update.message.chat.type != 'private'
#         context.chat_data['event_date'] = update.message.text
#
#         logger.info(
#             "Пользователь %s создает вариант мероприятия со временем проведения %s",
#             update.message.from_user.username,
#             context.chat_data['event_date']
#         )
#
#         await update.message.reply_text(
#             "Теперь напиши куда идем, только без банальностей, пожалуйста.."
#         )
#
#     if selection_text == "adv_option":
#         await handle_adv_option(update, context)
#         return
#
#     try:
#         # Преобразуем option_id из callback_data
#         option_id = int(selection_text)
#     except ValueError:
#         await update.effective_chat.send_message("Неверный формат кнопки.")
#         return
#
#     # Получаем вариант по ID
#     option = EventOptions.get_or_none(EventOptions.id == option_id)
#     if not option:
#         await update.effective_chat.send_message(f"Вариант с ID {option_id} не найден.")
#         return
#
#     # Получаем или создаем запись в UserOption для пользователя и выбранного варианта
#     user_option = UserOption.get_or_none(UserOption.user_id == user_id, UserOption.option_id == option_id)
#
#     # Определяем новый статус на основе текущего
#     if user_option:
#         # Меняем статус с "confirmed" на "canceled" или наоборот
#         new_status = "canceled" if user_option.status == "confirmed" else "confirmed"
#         action = "отменили" if new_status == "canceled" else "подтвердили"
#
#         # Используем метод update() для изменения статуса
#         UserOption.update(status=new_status).where(UserOption.user_id == user_id,
#                                                    UserOption.option_id == option_id).execute()
#     else:
#         # Если записи нет, создаем новую с дефолтным статусом
#         user_option = UserOption.create(user_id=user_id, option_id=option_id, status="confirmed")
#         action = "подтвердили"
#         new_status = "confirmed"
#
#     button_text = f"{option.place} - {option.date} ({'❌' if new_status == 'canceled' else '🍻'})"
#     await query.answer(f"Вы {action} выбор: {option.place} - {option.date}")
#
#     # Обновляем кнопки для всех вариантов события
#     event_options = EventOptions.select().where(EventOptions.event_id == option.event_id)
#     inline_keyboard = []
#
#     for opt in event_options:
#         # Получаем текущий статус для каждого варианта
#         status = "🍻" if UserOption.get_or_none(user_id=user_id, option_id=opt.id, status="confirmed") else "❌"
#         button_text = f"{opt.place} - {opt.date} ({status})"
#         inline_keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"{opt.id}")])
#
#     # Обновляем кнопки для всех вариантов события
#     event_options = EventOptions.select().where(EventOptions.event_id == option.event_id)
#     inline_keyboard = []
#
#     for opt in event_options:
#         # Получаем текущий статус для каждого варианта
#         status = "🍻" if UserOption.get_or_none(user_id=user_id, option_id=opt.id, status="confirmed") else "❌"
#         button_text = f"{opt.place} - {opt.date} ({status})"
#         inline_keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"{opt.id}")])
#
#     # Обновляем кнопки для всех вариантов события
#     event_options = EventOptions.select().where(EventOptions.event_id == option.event_id)
#     inline_keyboard = []
#
#     for opt in event_options:
#         status = "🍻" if UserOption.get_or_none(user_id=user_id, option_id=opt.id, status="confirmed") else "❌"
#         button_text = f"{opt.place} - {opt.date} ({status})"
#         inline_keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"{opt.id}")])
#
#     # Обновляем кнопки для всех вариантов события
#     event_options = EventOptions.select().where(EventOptions.event_id == option.event_id)
#     inline_keyboard = []
#
#     for opt in event_options:
#         status = "🍻" if UserOption.get_or_none(user_id=user_id, option_id=opt.id, status="confirmed") else "❌"
#         button_text = f"{opt.place} - {opt.date} ({status})"
#         inline_keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"{opt.id}")])
#
#     # Добавляем кнопку "Предложить свой вариант"
#     inline_keyboard.append([InlineKeyboardButton("Предложить свой вариант", callback_data="new_option")])
#     inline_keyboard.append([InlineKeyboardButton("А что есть рядом?", callback_data="adv_option")])
#
#     # Обновляем разметку с кнопками
#     try:
#         await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard))
#         logging.info("Сообщение обновлено с новой разметкой.")
#     except Exception as e:
#         logging.error(f"Ошибка при обновлении сообщения: {e}")
#
#
# async def handle_suggest_option(update: Update, context: CallbackContext):
#     logger.info("other variant")
#     # Выводим сообщение или предлагаем пользователю что-то
#     text = "Значит, тебе что-то не нравится? Ну хорошо - предлагай свое время для встречи"
#     await update.effective_chat.send_message(text)
#
#
# async def handle_adv_option(update: Update, context: CallbackContext):
#     event_id = context.user_data['event_id']
#     await init_nearby_handler(event_id, update, context)
