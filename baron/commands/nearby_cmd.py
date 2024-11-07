from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, CallbackContext, \
    ConversationHandler
from baron.models import Events
from baron.clients.gis import GisAPI
from configs.models import load_config_global

CHANGE = range(1)


def make_adv_buttons(event_id: int, prompt: str = "Бар"):
    event: Events = Events.get_by_id(event_id)
    gis = GisAPI(load_config_global())
    items = gis.adv(lat=event.latitude, lon=event.longitude)

    return [InlineKeyboardButton(item.name, callback_data='nearby_address')
            for item in items]


async def init_nearby_handler(event_id: int, update: Update, context: CallbackContext):
    context.user_data['event_id'] = event_id
    adv_buttons = make_adv_buttons(event_id)
    change_button = InlineKeyboardButton("Изменить поиск", callback_data='change_nearby_prompt')
    keyboard = [adv_buttons + [change_button]]

    text = "У меня есть для тебя несколько вариантов" if adv_buttons else "Это плохое место, я не смог найти тут ничего"

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def change_nearby_prompt_button(update: Update, context: CallbackContext):
    event_id = context.user_data['event_id']
    adv_buttons = make_adv_buttons(event_id)
    change_button = InlineKeyboardButton("Изменить поиск", callback_data='change_nearby_prompt')
    keyboard = [adv_buttons + [change_button]]

    text = "У меня есть для тебя несколько вариантов" if adv_buttons else "Это плохое место, я не смог найти тут ничего"

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    return CHANGE


async def change_nearby_prompt_handler(update: Update, context: CallbackContext):
    user_prompt = update.message.text
    event_id = context.user_data['event_id']
    adv_buttons = make_adv_buttons(event_id, user_prompt)
    change_button = InlineKeyboardButton("Изменить поиск", callback_data='change_nearby_prompt')
    keyboard = [adv_buttons + [change_button]]

    text = "У меня есть для тебя несколько вариантов" if adv_buttons else "Это плохое место, я не смог найти тут ничего"

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    return ConversationHandler.END

# ADD event_id INTO CONTEXT
async def nearby_prompt_button(update: Update, context: CallbackContext):
    event_id = context.user_data['event_id']
    adv_buttons = make_adv_buttons(event_id)
    change_button = InlineKeyboardButton("Изменить поиск", callback_data='change_nearby_prompt')
    keyboard = [adv_buttons + [change_button]]

    text = "У меня есть для тебя несколько вариантов" if adv_buttons else "Это плохое место, я не смог найти тут ничего"

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    return CHANGE


def nearby_change_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(change_nearby_prompt_button, pattern='change_nearby_prompt')],
        states={
            CHANGE: [MessageHandler(filters.TEXT, change_nearby_prompt_handler)]
        },
        fallbacks=[]
    )
