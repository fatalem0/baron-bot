from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, CallbackContext, \
    ConversationHandler
from baron.models import Events
from baron.clients.gis import GisAPI
from configs.models import load_config_global

CHANGE = 777


def make_adv_buttons(event_id: int, prompt: str = "Бар"):
    event: Events = Events.get_by_id(event_id)
    gis = GisAPI(load_config_global())
    items = gis.adv(lat=event.latitude, lon=event.longitude, prompt=prompt)

    return [[InlineKeyboardButton(item.name, callback_data='nearby_address')]
            for item in items]


async def reply_adv_buttons(update: Update, context: CallbackContext):
    event_id = context.user_data['event_id']
    prompt = context.user_data['prompt']
    adv_buttons = make_adv_buttons(event_id, prompt)
    change_button = [InlineKeyboardButton("Изменить поиск", callback_data='change_nearby_prompt')]
    keyboard = adv_buttons + [change_button]

    text = "Подобрал вот такие варианты" if adv_buttons else "Это плохое место, я не смог найти тут ничего"

    await update.effective_chat.send_message(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def change_nearby_prompt_button(update: Update, context: CallbackContext):
    text = "Отправь мне текст для поиска мест"
    await update.effective_chat.send_message(text)
    return CHANGE


async def change_nearby_prompt_handler(update: Update, context: CallbackContext):
    context.user_data['prompt'] = update.message.text
    await reply_adv_buttons(update, context)
    return ConversationHandler.END


async def init_nearby_handler(event_id: int, update: Update, context: CallbackContext):
    context.user_data['event_id'] = event_id
    context.user_data['prompt'] = "Бар"
    await reply_adv_buttons(update, context)


def nearby_change_handlers():
    return [
        ConversationHandler(
            entry_points=[CallbackQueryHandler(change_nearby_prompt_button, pattern='change_nearby_prompt')],
            states={
                CHANGE: [MessageHandler(filters.TEXT, change_nearby_prompt_handler)]
            },
            fallbacks=[]
        )
    ]
