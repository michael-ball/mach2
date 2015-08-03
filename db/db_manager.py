import configparser
import os

import apsw


class DbManager:
    class __DbManager:
        config = configparser.ConfigParser()
        config.read("mach2.ini")

        def __init__(self):
            new_db = False
            cache_size_kb = 9766

            if not os.path.isfile(self.config["DEFAULT"]["database"]):
                new_db = True

            if new_db:
                self.conn = apsw.Connection(":memory:")
                self.create_tables()
            else:
                self.conn = apsw.Connection(self.config["DEFAULT"]["database"])
                library_info = os.stat(self.config["DEFAULT"]["database"])
                cache_size_kb = round((library_info.st_size * 1.2) / 1024)

                cursor = self.conn.cursor()
                # Setting pragma with ? placeholder errors out
                cursor.execute("pragma cache_size=-%s" % cache_size_kb)
                cursor.close()

        def __del__(self):
            if not os.path.isfile(self.config["DEFAULT"]["database"]):
                tempconn = apsw.Connection(self.config["DEFAULT"]["database"],
                                           apsw.SQLITE_OPEN_READWRITE |
                                           apsw.SQLITE_OPEN_CREATE)

                with tempconn.backup("main", 
                                     self.conn, "main") as backup:
                    backup.step()

        def __str__(self):
            return repr(self)

        def cursor(self):
            return self.conn.cursor()

        def close(self):
            return self.conn.close()

        def interrupt(self):
            return self.conn.interrupt()

        def last_insert_rowid(self):
            return self.conn.last_insert_rowid()

        def create_tables(self):
            cursor = self.conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS album (id
                           INTEGER PRIMARY KEY, name TEXT, date TEXT,
                           musicbrainz_albumid TEXT)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS album_artist (
                    album_id INTEGER,
                    artist_id INTEGER,
                    CONSTRAINT ALBUM_ARTIST_PK PRIMARY KEY (album_id,
                    artist_id),
                    CONSTRAINT ALBUM_ARTIST_FK_ALBUM FOREIGN KEY (album_id)
                        REFERENCES album(id),
                    CONSTRAINT ALBUM_ARTIST_FK_ARTIST FOREIGN KEY
                        (artist_id) REFERENCES artist(id)
                )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS album_track (
                    album_id INTEGER,
                    track_id INTEGER,
                    CONSTRAINT ALBUM_TRACK_PK PRIMARY KEY (album_id,
                        track_id),
                    FOREIGN KEY(album_id) REFERENCES album(id),
                    FOREIGN KEY(track_id) REFERENCES track(id)
                )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS artist (id
                    INTEGER PRIMARY KEY, name
                    TEXT(2000000000), sortname TEXT(2000000000),
                    musicbrainz_artistid TEXT(2000000000))""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS artist_track (
                    artist_id INTEGER,
                    track_id INTEGER,
                    CONSTRAINT ARTIST_TRACK_PK PRIMARY KEY (artist_id,
                        track_id),
                    FOREIGN KEY(artist_id) REFERENCES artist(id),
                    FOREIGN KEY(track_id) REFERENCES track(id)
                )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS track (
                    id INTEGER,
                    tracknumber INTEGER,
                    name TEXT(2000000000),
                    grouping TEXT(2000000000),
                    filename TEXT(2000000000),
                    CONSTRAINT TRACK_PK PRIMARY KEY (id)
                )""")
            cursor.execute("""CREATE UNIQUE INDEX IF NOT EXISTS
                           artist_musicbrainz_artistid ON
                           artist(musicbrainz_artistid ASC)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS track_filename_IDX
                           ON track(filename)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS track_grouping_IDX
                           ON track(grouping)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS track_name_IDX ON
                           track(name)""")
            cursor.execute("""CREATE INDEX IF NOT EXISTS
                           track_tracknumber_IDX ON track(tracknumber)""")
            cursor.close()

    instance = None

    def __new__(self):
        if not DbManager.instance:
            DbManager.instance = DbManager.__DbManager()
        
        return DbManager.instance
