from peewee import (
    AutoField,
    BooleanField,
    CharField,
    DateField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase, TimestampField, Check,
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
    id = IntegerField()
    user = ForeignKeyField(User, backref="events")
    created_at = TimestampField(null=True)
    min_person_cnt = IntegerField(default=0, constraints=[Check('min_person_cnt >= 0')])
    status_id = CharField(null=True)

    class Meta:
        database = db
        schema = 'pwa4owski_test'
        table_name = 'events'



db.bind([User, Event], bind_refs=False, bind_backrefs=False)

