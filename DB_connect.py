import psycopg2

class DB:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="c-c9qhi5jpif1h5cqvlh32.rw.mdb.yandexcloud.net",
            port="6432",
            sslmode="verify-full",
            dbname="baron",
            user="itmo",
            password="baron-itmo",
            target_session_attrs="read-write",
        )

    def get_conn(self):
        return self.conn
