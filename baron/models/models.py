from peewee import (
    BooleanField,
    CharField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase, TimestampField, Check, DateTimeField, CompositeKey,
)

db = PostgresqlDatabase(
        "baron",
        user="itmo",
        password="baron-itmo",
        host='c-c9qhi5jpif1h5cqvlh32.rw.mdb.yandexcloud.net',
        port="6432",
        sslmode="verify-full",
        sslrootcert=r"C:\Users\user\.postgresql\root.crt"
)


class User(Model):
    id = IntegerField(primary_key=True)
    tg_tag = CharField()

    class Meta:
        database = db
        schema = 'pwa4owski_test'
        table_name = 'users'

class Event(Model):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(User, backref="events", column_name="author_id")
    created_at = TimestampField(null=True)
    min_person_cnt = IntegerField(default=0, constraints=[Check('min_person_cnt >= 0')])
    status_id = CharField(null=True)

    class Meta:
        database = db
        schema = 'pwa4owski_test'
        table_name = 'events'

class UserEvent(Model):
    user = ForeignKeyField(User, backref='events', on_delete='CASCADE')
    event = ForeignKeyField(Event, backref='users', on_delete='CASCADE')
    joined_at = TimestampField()

    class Meta:
        database = db
        schema = 'pwa4owski_test'
        table_name = 'event_group'
        primary_key = CompositeKey('user', 'event')


class Option(Model):
    id = IntegerField(primary_key=True)
    event = ForeignKeyField(Event, backref="options", on_delete='CASCADE')
    start_time = DateTimeField()
    place_name = CharField()
    place_link = CharField(null=True)
    author = ForeignKeyField(User, backref='authored_options', on_delete='CASCADE')

    class Meta:
        database = db
        table_name = 'options'


class UsersOptions(Model):
    user = ForeignKeyField(User, backref='user_options', on_delete='CASCADE')
    option = ForeignKeyField(Option, backref='option_users', on_delete='CASCADE')
    match = BooleanField()

    class Meta:
        database = db
        table_name = 'users_options'
        primary_key = CompositeKey('user', 'option')


db.bind([User, Event, UserEvent, Option, UsersOptions], bind_refs=False, bind_backrefs=False)

