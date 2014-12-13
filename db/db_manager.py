import configparser
import sqlite3


class DbManager:
    class __DbManager:
        def __init__(self):
            config = configparser.ConfigParser()
            config.read("mach2.ini")
            self.conn = sqlite3.connect(config["DEFAULT"]["database"])

        def __str__(self):
            return repr(self)

        def execute(self, *args):
            return self.conn.execute(*args)

        def cursor(self):
            return self.conn.cursor()

        def commit(self):
            return self.conn.commit()

        def close(self):
            return self.conn.close()

        def rollback(self):
            return self.conn.rollback()

        def executemany(self, *args):
            return self.conn.executemany(*args)

        def executescript(self, *args):
            return self.conn.executescript(*args)

        def create_function(self, *args):
            return self.conn.create_function(*args)

        def create_aggregate(self, *args):
            return self.conn.create_aggregate(*args)

        def create_collation(self, *args):
            return self.conn.create_collation(*args)

        def interrupt(self):
            return self.conn.interrupt()

    instance = None

    def __new__(cls):
        if not DbManager.instance:
            DbManager.instance = DbManager.__DbManager()

        return DbManager.instance
