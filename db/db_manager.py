import configparser
import os
import sqlite3


class DbManager:
    class __DbManager:
        config = configparser.ConfigParser()
        config.read("mach2.ini")

        def iterdump(connection):
            cu = connection.cursor()
            yield("BEGIN TRANSACTION;")

            q = """
                SELECT "name", "type", "sql"
                FROM "sqlite_master"
                    WHERE "sql" NOT NULL AND
                    "type" == 'table'
                    ORDER BY "name";
                """
            schema_res = cu.execute(q).fetchall()
            for table_name, type, sql in schema_res:
                if table_name == "sqlite_sequence":
                    yield("DELETE FROM \"sqlite_sequence\";")
                elif table_name == "sqlite_stat1":
                    yield("ANALYZE \"sqlite_master\";")
                elif table_name.startswith("sqlite_"):
                    continue
                else:
                    yield("{0};".format(sql))

                table_name_ident = table_name.replace("\"", "\"\"")
                res = cu.execute("PRAGMA table_info(\"{0}\")".format(
                    table_name_ident))
                column_names = [
                    str(table_info[1]) for table_info in res.fetchall()]
                q = """
                    SELECT 'INSERT INTO "{0}" VALUES({1})' FROM "{0}";
                    """.format(table_name_ident, ",".join(
                    """'||quote("{0}")||'""".format(
                        col.replace(
                            "\"", "\"\"")) for col in column_names))
                query_res = cu.execute(q)
                for row in query_res:
                    yield("{0};".format(row[0]))

            q = """
                SELECT "name", "type", "sql"
                FROM "sqlite_master"
                    WHERE "sql" NOT NULL AND
                    "type" IN ('index', 'trigger', 'view')
                """
            schema_res = cu.execute(q)
            for name, type, sql in schema_res.fetchall():
                yield("{0};".format(sql))

            yield("COMMIT;")

        def __init__(self):
            new_db = False
            cache_size_kb = 9766

            if not os.path.isfile(self.config["DEFAULT"]["database"]):
                new_db = True

            if new_db:
                self.conn = sqlite3.connect(":memory:")
                self.create_tables()
            else:
                self.conn = sqlite3.connect(self.config["DEFAULT"]["database"])
                library_info = os.stat(self.config["DEFAULT"]["database"])
                cache_size_kb = round((library_info.st_size * 1.2) / 1024)

                cursor = self.conn.cursor()
                # Setting pragma with ? placeholder produces an error
                cursor.execute("pragma cache_size=-%s" % cache_size_kb)
                cursor.close()

            self.conn.row_factory = sqlite3.Row

        def export(self):
            if not os.path.isfile(self.config["DEFAULT"]["database"]):
                script = ""

                for line in DbManager.__DbManager.iterdump(self.conn):
                    script = "\n".join((script, line))

                tempconn = sqlite3.connect(
                    self.config["DEFAULT"]["database"])
                tempcur = tempconn.cursor()

                tempcur.executescript(script)
                tempcur.close()

        def __str__(self):
            return repr(self)

        def commit(self):
            return self.conn.commit()

        def cursor(self):
            return self.conn.cursor()

        def close(self):
            return self.conn.close()

        def interrupt(self):
            return self.conn.interrupt()

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
