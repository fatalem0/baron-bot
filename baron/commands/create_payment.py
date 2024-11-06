from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, CallbackContext
import time

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
        print("handle_buttons-update->", update)
        print("handle_buttons-context->", context.user_data)
        # Переключаем обработчик на ожидание фото
        context.user_data['expecting_photo'] = True
    elif user_choice == "Отмена":
        # Сообщаем об отмене и убираем клавиатуру
        await update.message.reply_text("Отмена операции.", reply_markup=ReplyKeyboardMarkup([[]]))

# Шаг 3. Обрабатываем отправку фото пользователем - место для парсинга
async def photo_handler(update: Update, context: CallbackContext) -> None:
    print("expect photo->", update)
    print("expect photo context.user_data ->", context.user_data)
    keyboard = [
        [InlineKeyboardButton("Отправьте свою часть долга", callback_data='button_clicked')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if context.user_data.get('expecting_photo'):
        # Сброс флага ожидания фото
        context.user_data['expecting_photo'] = False
        # Сохраняем фото
        # photo_file = update.message.photo[-1].get_file()
        # photo_file.download('user_photo.jpg')

        await update.message.reply_text("Фото счета успешно загружено!", reply_markup= reply_markup)
    else:
        await update.message.reply_text("Отправьте команду /create_payment, чтобы загрузить фото.")


async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Обязательный ответ для Telegram
    # Действие при нажатии на кнопку
    await query.edit_message_text(text="Вы оплатили долг")

# Функция для регистрации обработчиков
def register_handlers(dispatcher):
    # Регистрируем обработчик команды /upload_photo
    dispatcher.add_handler(CommandHandler("create_payment", create_payment))

    # Регистрируем обработчик текстовых сообщений (нажатие кнопок)
    dispatcher.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_buttons))

    # Регистрируем обработчик для фото
    dispatcher.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, photo_handler))

    # Обработчик для нажатия на кнопку
    dispatcher.add_handler(CallbackQueryHandler(button_handler, pattern='button_clicked'))
