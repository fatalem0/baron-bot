import psycopg2
from configs.models import load_config_global

class DB:
    def __init__(self):
        conf = load_config_global()
        self.conn = psycopg2.connect(
            host="c-c9qhi5jpif1h5cqvlh32.rw.mdb.yandexcloud.net",
            port="6432",
            sslmode="verify-full",
            dbname="baron",
            user="itmo",
            password="baron-itmo",
            target_session_attrs="read-write",
            sslrootcert=conf.sslrootcert
        )

    def get_conn(self):
        return self.conn
