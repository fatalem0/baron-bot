import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton,  Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, CallbackContext

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Шаг 1. Создаем команду /create_payment
async def create_payment(update: Update, context: CallbackContext) -> None:
    # Создаем клавиатуру с двумя кнопками
    keyboard = [
        [KeyboardButton("Загрузить счёт"), KeyboardButton("Отмена")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    if update.message.chat.type == "private":
        await update.message.reply_text("Функция загрузки счета доступна только из чатов групп")
    else:
        # Отправляем сообщение с клавиатурой
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Шаг 2. Обрабатываем нажатие на кнопки
async def handle_buttons(update: Update, context: CallbackContext) -> None:
    user_choice = update.message.text
    if user_choice == "Загрузить счёт":
        # Сообщаем пользователю, что нужно выбрать фото
        await update.message.reply_text("Пожалуйста, загрузите фото общего счета.")
        logger.info("При загрузке счета: %s, %s", update, context.user_data)
        # Переключаем обработчик на ожидание фото
        context.user_data['expecting_photo'] = True
    elif user_choice == "Отмена":
        # Сообщаем об отмене и убираем клавиатуру
        await update.message.reply_text("Отмена операции.", reply_markup=ReplyKeyboardMarkup([[]]))

# Шаг 3. Обрабатываем отправку фото пользователем - место для парсинга
async def photo_handler(update: Update, context: CallbackContext) -> None:
    logger.info("После загрузки счета: %s, %s",update, context.user_data)
    keyboard = [
        [InlineKeyboardButton("Отправьте свою часть долга", callback_data='button_clicked')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if context.user_data.get('expecting_photo'):
        # Сброс флага ожидания фото
        context.user_data['expecting_photo'] = False
        await update.message.reply_text("Фото счета успешно загружено!", reply_markup= reply_markup)
    else:
        await update.message.reply_text("Отправьте команду /create_payment, чтобы загрузить фото.")

async def button_handler(update: Update, context: CallbackContext) -> None:
    logger.info( "После кнопки: %s", update )
    query = update.callback_query
    await query.answer()  # Обязательный ответ для Telegram
    # Действие при нажатии на кнопку
    await query.edit_message_text(text="Вы оплатили долг.Вы молодец!",)

# Функция для регистрации обработчиков
def register_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("create_payment", create_payment))
    dispatcher.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_buttons))
    dispatcher.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, photo_handler))
    dispatcher.add_handler(CallbackQueryHandler(button_handler, pattern='button_clicked'))
