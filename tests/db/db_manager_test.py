from db.db_manager import DbManager


class TestDbManager:

    def test_create_tables(self):
        assert DbManager.create_album_table == "CREATE TABLE IF NOT EXISTS "\
            "album (id INTEGER PRIMARY KEY, name TEXT, date TEXT, "\
            "musicbrainz_albumid TEXT)"

        assert DbManager.create_album_artist_table == "CREATE TABLE IF NOT "\
            "EXISTS album_artist (album_id INTEGER, artist_id INTEGER, "\
            "CONSTRAINT ALBUM_ARTIST_PK PRIMARY KEY (album_id, artist_id), "\
            "CONSTRAINT ALBUM_ARTIST_FK_ALBUM FOREIGN KEY (album_id) "\
            "REFERENCES album(id), CONSTRAINT ALBUM_ARTIST_FK_ARTIST "\
            "FOREIGN KEY(artist_id) REFERENCES artist(id))"

        assert DbManager.create_album_track_table == "CREATE TABLE IF NOT "\
            "EXISTS album_track (album_id INTEGER, track_id INTEGER, "\
            "CONSTRAINT ALBUM_TRACK_PK PRIMARY KEY (album_id, track_id), "\
            "FOREIGN KEY(album_id) REFERENCES album(id), FOREIGN "\
            "KEY(track_id) REFERENCES track(id))"

        assert DbManager.create_artist_table == "CREATE TABLE IF NOT EXISTS "\
            "artist (id INTEGER PRIMARY KEY, name TEXT(2000000000), sortname "\
            "TEXT(2000000000), musicbrainz_artistid TEXT(2000000000))"

        assert DbManager.create_artist_track_table == "CREATE TABLE IF NOT "\
            "EXISTS artist_track (artist_id INTEGER, track_id INTEGER, "\
            "CONSTRAINT ARTIST_TRACK_PK PRIMARY KEY (artist_id, track_id), "\
            "FOREIGN KEY(artist_id) REFERENCES artist(id), FOREIGN "\
            "KEY(track_id) REFERENCES track(id))"

        assert DbManager.create_track_table == "CREATE TABLE IF NOT EXISTS "\
            "track (id INTEGER, tracknumber INTEGER, name TEXT(2000000000), "\
            "grouping TEXT(2000000000), filename TEXT(2000000000), "\
            "CONSTRAINT TRACK_PK PRIMARY KEY (id))"

        assert DbManager.create_musicbrainz_artist_index == "CREATE UNIQUE "\
            "INDEX IF NOT EXISTS artist_musicbrainz_artistid ON "\
            "artist(musicbrainz_artistid ASC)"

        assert DbManager.create_track_filename_index == "CREATE INDEX IF NOT "\
            "EXISTS track_filename_IDX ON track(filename)"

        assert DbManager.create_track_grouping_index == "CREATE INDEX IF NOT "\
            "EXISTS track_grouping_IDX ON track(grouping)"

        assert DbManager.create_track_name_index == "CREATE INDEX IF NOT "\
            "EXISTS track_name_IDX ON track(name)"

        assert DbManager.create_track_number_index == "CREATE INDEX IF NOT "\
            "EXISTS track_tracknumber_IDX ON track(tracknumber)"
