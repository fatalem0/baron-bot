from peewee import (
    CharField,
    ForeignKeyField,
    IntegerField,
    FloatField,
    Model,
    PostgresqlDatabase, Check, DateTimeField, SQL, CompositeKey, BigIntegerField,
)

from configs.models import load_config_global

db = PostgresqlDatabase(
    "baron",
    user="itmo",
    password="baron-itmo",
    host='c-c9qhi5jpif1h5cqvlh32.rw.mdb.yandexcloud.net',
    port="6432",
    sslmode="verify-full"
)


class BaseModel(Model):
    class Meta:
        database = db
        schema = load_config_global().schema

class Users(BaseModel):
    id = IntegerField(primary_key=True)
    username = CharField(unique=True)
    with_bot_chat_id = IntegerField()


class Events(BaseModel):
    id = IntegerField(primary_key=True)
    author_id = ForeignKeyField(Users, backref="events")
    name = CharField()
    min_attendees = IntegerField(constraints=[Check('min_attendees > 1')])
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    status_id = CharField(null=True)
    latitude = FloatField()
    longitude = FloatField()


class EventOptions(BaseModel):
    id = IntegerField(primary_key=True)
    event_id = ForeignKeyField(Events, backref="event_options", on_delete='CASCADE')
    date = CharField()
    place = CharField()
    place_link = CharField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    author_id = ForeignKeyField(Users, backref='authored_options', on_delete='CASCADE')

    class Meta:
        table_name = 'event_options'


class UsersEvents(BaseModel):
    user_id = ForeignKeyField(Users, backref='events', on_delete='CASCADE')
    event_id = ForeignKeyField(Events, backref='users', on_delete='CASCADE')
    joined_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        table_name = 'users_events'
        primary_key = CompositeKey('user_id', 'event_id')


class UserOption(BaseModel):
    user_id = IntegerField(primary_key=True)  # ID пользователя (например, ID Telegram)
    option_id = IntegerField()  # ID выбранного варианта (ссылка на event_options)
    status = CharField(default='pending')  # Статус выбора (например, "confirmed", "declined", "pending")

    class Meta:
        database = db  # Подключение к базе данных
        db_table = 'users_options'  # Имя таблицы в базе данных
        indexes = (
            (('user_id', 'option_id'), True),  # Уникальный индекс на комбинацию user_id и option_id
        )

db.bind([Users, Events], bind_refs=False, bind_backrefs=False)
