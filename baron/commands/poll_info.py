import logging

from peewee import Update, Model, CharField, ForeignKeyField, DateTimeField, PostgresqlDatabase, IntegrityError, \
    BigIntegerField, SQL, fn
from requests import options
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler
import DB_connect
from baron.models import db
from configs.models import load_config_global

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Настройка подключения к базе данных через Peewee
if db.is_closed():
    db.connect()
