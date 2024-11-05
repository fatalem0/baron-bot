from peewee import (
    CharField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase, Check, DateTimeField, SQL, CompositeKey,
)

db = PostgresqlDatabase(
    "baron",
    user="itmo",
    password="baron-itmo",
    host='c-c9qhi5jpif1h5cqvlh32.rw.mdb.yandexcloud.net',
    port="6432",
    sslmode="verify-full",
    sslrootcert=r"/Users/fatalem0/.postgresql/root.crt"
)


class BaseModel(Model):
    class Meta:
        database = db
        schema = 'tsyganov_test'


class Users(BaseModel):
    id = IntegerField(primary_key=True)
    username = CharField(unique=True)


class Events(BaseModel):
    author_id = ForeignKeyField(Users, backref="events")
    name = CharField()
    min_attendees = IntegerField(constraints=[Check('min_attendees > 1')])
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    status_id = CharField(null=True)


class EventOptions(BaseModel):
    event_id = ForeignKeyField(Events, backref="event_options", on_delete='CASCADE')
    date = DateTimeField()
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


db.bind([Users, Events], bind_refs=False, bind_backrefs=False)
