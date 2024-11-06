from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, CallbackContext
from baron.models import Events

async def init_nearby_handler(event_id: int, update: Update, context: CallbackContext):
    event: Events = Events.get_by_id(event_id)
    # TODO: make adv
