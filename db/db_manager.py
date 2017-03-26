"""
db_manager exposes a DbManager class to make interacting with sqlite
databases easier.
"""
import logging
import os
import sqlite3

import six


_LOGGER = logging.getLogger(__name__)

class DbManager(object):
    """DBManager makes interacting with sqlite databases easier."""

    create_album_table = "CREATE TABLE IF NOT EXISTS album (id INTEGER "\
        "PRIMARY KEY, name TEXT, date TEXT, musicbrainz_albumid TEXT)"
    create_album_artist_table = "CREATE TABLE IF NOT EXISTS album_artist ("\
        "album_id INTEGER, artist_id INTEGER, CONSTRAINT ALBUM_ARTIST_PK "\
        "PRIMARY KEY (album_id, artist_id), CONSTRAINT ALBUM_ARTIST_FK_ALBUM "\
        "FOREIGN KEY (album_id) REFERENCES album(id), CONSTRAINT "\
        "ALBUM_ARTIST_FK_ARTIST FOREIGN KEY(artist_id) REFERENCES artist(id))"
    create_album_track_table = "CREATE TABLE IF NOT EXISTS album_track ("\
        "album_id INTEGER, track_id INTEGER, CONSTRAINT ALBUM_TRACK_PK "\
        "PRIMARY KEY (album_id, track_id), FOREIGN KEY(album_id) REFERENCES "\
        "album(id), FOREIGN KEY(track_id) REFERENCES track(id))"
    create_artist_table = "CREATE TABLE IF NOT EXISTS artist (id INTEGER "\
        "PRIMARY KEY, name TEXT(2000000000), sortname TEXT(2000000000), "\
        "musicbrainz_artistid TEXT(2000000000))"
    create_artist_track_table = "CREATE TABLE IF NOT EXISTS artist_track ("\
        "artist_id INTEGER, track_id INTEGER, CONSTRAINT ARTIST_TRACK_PK "\
        "PRIMARY KEY (artist_id, track_id), FOREIGN KEY(artist_id) "\
        "REFERENCES artist(id), FOREIGN KEY(track_id) REFERENCES track(id))"
    create_track_table = "CREATE TABLE IF NOT EXISTS track (id INTEGER, "\
        "tracknumber INTEGER, name TEXT(2000000000), grouping "\
        "TEXT(2000000000), filename TEXT(2000000000), CONSTRAINT TRACK_PK "\
        "PRIMARY KEY (id))"
    create_musicbrainz_artist_index = "CREATE UNIQUE INDEX IF NOT EXISTS "\
        "artist_musicbrainz_artistid ON artist(musicbrainz_artistid ASC)"
    create_track_filename_index = "CREATE INDEX IF NOT EXISTS "\
        "track_filename_IDX ON track(filename)"
    create_track_grouping_index = "CREATE INDEX IF NOT EXISTS "\
        "track_grouping_IDX ON track(grouping)"
    create_track_name_index = "CREATE INDEX IF NOT EXISTS track_name_IDX ON "\
        "track(name)"
    create_track_number_index = "CREATE INDEX IF NOT EXISTS "\
        "track_tracknumber_IDX ON track(tracknumber)"

    @staticmethod
    def iterdump(connection):
        """Iterates through the database, creating commands to dump all the
        tables line by line."""
        cursor = connection.cursor()

        query = """
            SELECT "name", "type", "sql"
            FROM "sqlite_master"
                WHERE "sql" NOT NULL AND
                "type" == 'table'
                ORDER BY "name";
            """
        schema_res = cursor.execute(query).fetchall()
        for table_name, dummy, sql in schema_res:
            if table_name == "sqlite_sequence":
                yield "DELETE FROM \"sqlite_sequence\";"
            elif table_name == "sqlite_stat1":
                yield "ANALYZE \"sqlite_master\";"
            elif table_name.startswith("sqlite_"):
                continue
            else:
                yield six.u("{0};").format(sql)

            table_name_ident = table_name.replace("\"", "\"\"")
            res = cursor.execute("PRAGMA table_info(\"{0}\")".format(
                table_name_ident))
            column_names = [
                str(table_info[1]) for table_info in res.fetchall()]
            query = """
                SELECT 'INSERT INTO "{0}" VALUES({1})' FROM "{0}";
                """.format(table_name_ident, ",".join(
                    """'||quote("{0}")||'""".format(
                        col.replace(
                            "\"", "\"\"")) for col in column_names))
            query_res = cursor.execute(query)
            for row in query_res:
                yield six.u("{0};").format(row[0])

        query = """
            SELECT "name", "type", "sql"
            FROM "sqlite_master"
                WHERE "sql" NOT NULL AND
                "type" IN ('index', 'trigger', 'view')
            """
        schema_res = cursor.execute(query)
        for dummy, dummy2, sql in schema_res.fetchall():
            yield six.u("{0};").format(sql)

    def __init__(self, db_file):
        new_db = False
        cache_size_kb = 9766
        self.db_file = db_file

        if not os.path.isfile(self.db_file):
            new_db = True

        if new_db:
            self.conn = sqlite3.connect(":memory:")
            self.create_tables()
        else:
            self.conn = sqlite3.connect(self.db_file)
            library_info = os.stat(self.db_file)
            cache_size_kb = round((library_info.st_size * 1.2) / 1024)

            cursor = self.conn.cursor()
            # Setting pragma with ? placeholder produces an error
            cursor.execute("pragma cache_size=-%s" % cache_size_kb)
            cursor.close()

        self.conn.row_factory = sqlite3.Row

    def export(self):
        """Export the database."""
        if not os.path.isfile(self.db_file):
            tempconn = sqlite3.connect(self.db_file)
            tempcur = tempconn.cursor()
            tempcur.execute("PRAGMA journal_mode=WAL;")
            tempcur.close()

            try:
                with tempconn:
                    for line in DbManager.iterdump(self.conn):
                        tempconn.execute(line)

            except sqlite3.Error as exc:
                _LOGGER.error(exc)

            tempconn.close()

    def __str__(self):
        return repr(self)

    def execute(self, script, parameters=None):
        """Execute an sql statement"""
        if parameters:
            return self.conn.execute(script, parameters)

        return self.conn.execute(script)

    def commit(self):
        """Commit the current transaction"""
        return self.conn.commit()

    def cursor(self):
        """Create a cursor"""
        return self.conn.cursor()

    def close(self):
        """Close the connection"""
        return self.conn.close()

    def interrupt(self):
        """Interrupt the connection"""
        return self.conn.interrupt()

    def create_tables(self):
        """Create the database tables"""
        with self.conn:
            self.conn.execute(DbManager.create_album_table)
            self.conn.execute(DbManager.create_album_artist_table)
            self.conn.execute(DbManager.create_album_track_table)
            self.conn.execute(DbManager.create_artist_table)
            self.conn.execute(DbManager.create_artist_track_table)
            self.conn.execute(DbManager.create_track_table)
            self.conn.execute(DbManager.create_musicbrainz_artist_index)
            self.conn.execute(DbManager.create_track_filename_index)
            self.conn.execute(DbManager.create_track_grouping_index)
            self.conn.execute(DbManager.create_track_name_index)
            self.conn.execute(DbManager.create_track_number_index)
