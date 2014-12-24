import sqlite3

from common import utils
from db.db_manager import DbManager
from models.artist import Artist
from models.album import Album


class Track:

    def __init__(self, id=None, **kwargs):

        setattr(self, "__data", {})

        if id is not None:
            db = DbManager()
            for row in db.execute("""SELECT * FROM track WHERE id = ?""",
                                  (id,)):
                setattr(self, "id", row[0])
                setattr(self, "tracknumber", row[1])
                setattr(self, "name", row[2])
                setattr(self, "grouping", row[3])
                setattr(self, "filename", row[4])
        else:
            for (key, value) in kwargs.items():
                setattr(self, key, value)
                self.__data[key] = value

    def delete(self):
        db = DbManager()

        delete_sql = "DELETE FROM track WHERE id = ?"
        db.execute(delete_sql, (self.id,))
        db.commit()

        return True

    @property
    def album(self):
        if not hasattr(self, "_album"):
            setattr(self, "_album", None)

            db = DbManager()

            for row in db.execute("""SELECT album.* FROM album INNER JOIN
                                  album_track ON album.id =
                                  album_track.album_id WHERE track_id = ?
                                  LIMIT 1""", (self.id,)):
                setattr(self, "_album", Album(row[0]))

        return self._album

    @property
    def artists(self):
        if not hasattr(self, "_artists"):
            db = DbManager()

            setattr(self, "_artists", [])
            for row in db.execute("""SELECT artist.* FROM artist INNER JOIN
                                  artist_track ON artist.id =
                                  artist_track.artist_id WHERE
                                  artist.id = ?""", (self.id,)):
                self._artists.append(Artist(row[0]))

        return self._artists

    def update(self, metadata):
        db = DbManager()
        c = db.cursor()

        artist_names = metadata["artist"]
        musicbrainz_artist_ids = []
        artistsorts = []
        try:
            musicbrainz_artist_ids = metadata["musicbrainz_artistid"]
        except KeyError:
            pass
        try:
            artistsorts = metadata["artistsort"]
        except KeyError:
            pass

        i = 0
        artists = []

        for artist_name in artist_names:
            musicbrainz_artistid = None
            artistsort = None

            try:
                musicbrainz_artistid = musicbrainz_artist_ids[i]
            except IndexError:
                pass
            try:
                artistsort = artistsorts[i]
            except IndexError:
                pass

            rows = None

            if musicbrainz_artistid:
                rows = c.execute("""SELECT * FROM artist WHERE
                    musicbrainz_artist_id = ?""",
                                 (musicbrainz_artistid,))
            else:
                rows = c.execute("""SELECT * FROM artist WHERE
                    name = ?""", (artist_name,))

            row = rows.fetchone()

            if row:
                artist = Artist(id=row[0], name=row[1],
                                sortname=row[2],
                                musicbrainz_artist_id=row[3])

                if artist.name != artist_name:
                    c.execute("""UPDATE artist SET name = ? WHERE id = ?""",
                              (artist_name, artist.id))
                    artist.name = artist_name

                if artist.sortname != artistsort:
                    c.execute("""UPDATE artist SET sortname = ? WHERE id =
                              ? """, (artistsort, id))
                    artist.sortname = artistsort

            else:
                c.execute("""INSERT INTO artist
                    (name, sortname, musicbrainz_artist_id) VALUES(
                    ?,?,?)""", (artist_name, artistsort,
                                musicbrainz_artistid))

                artist = Artist(
                    id=c.lastrowid, name=artist_name,
                    sortname=artistsort,
                    musicbrainz_artist_id=musicbrainz_artistid
                )

                i += 1

            artists.append(artist)

        album_name = None
        album_date = None
        mb_albumid = None

        album = None
        try:
            album_name = metadata["album"][0]
        except KeyError:
            pass
        try:
            album_date = metadata["date"][0]
        except KeyError:
            pass

        try:
            mb_albumid = metadata["musicbrainz_albumid"][0]
        except KeyError:
            pass

        if mb_albumid:
            rows = c.execute(
                """SELECT * FROM album WHERE musicbrainz_albumid = ?""",
                (mb_albumid,)
            )

            row = rows.fetchone()

            if row:
                album = Album(id=row[0], name=row[1], date=row[2],
                              mb_albumid=row[3])
            else:
                c.execute("""INSERT INTO album (name, `date`,
                          musicbrainz_albumid) VALUES (?,?,?)""",
                          (album_name, album_date, mb_albumid))

                album = Album(id=c.lastrowid, name=album_name,
                              date=album_date, musicbrainz_albumid=mb_albumid)

        elif album_name:
            rows = c.execute(
                """SELECT album.* FROM album INNER JOIN album_artist ON
                album_artist.album_id = album.id WHERE album.name = ?
                AND artist_id = ?""", (album_name, artist.id)
            )
            row = rows.fetchone()

            if row:
                album = Album(id=row[0], name=row[1], date=row[2])
            else:
                c.execute("""INSERT INTO album (name, `date`) VALUES
                (?,?)""", (album_name, album_date))

                album = Album(id=c.lastrowid, name=album_name,
                              date=album_date)

        if album:
            if album.name != album_name:
                c.execute("""UPDATE album SET name = ? WHERE id = ?""",
                          (album_name, album.id))
                album.name = album_name

            if album.date != album_date:
                c.execute("""UPDATE album SET date = ? WHERE id = ?""",
                          (album_date, album.id))
                album.date = album_date

        for artist in artists:
            if album:
                try:
                    c.execute(
                        """INSERT INTO album_artist (artist_id,
                        album_id) VALUES(?,?)""",
                        (artist.id, album.id)
                    )
                except sqlite3.IntegrityError:
                    pass

        track_number = None
        track_name = None
        track_grouping = None
        try:
            track_number = metadata["tracknumber"][0]
        except KeyError:
            pass
        try:
            track_name = metadata["title"][0]
        except KeyError:
            pass
        try:
            track_grouping = metadata["grouping"][0]
        except KeyError:
            pass

        c.execute("""UPDATE track SET tracknumber = ?, name = ?,
                  grouping = ? WHERE id = ?""",
                  (track_number, track_name, track_grouping,
                   self.id))

        if album:
            try:
                c.execute("""INSERT INTO album_track (album_id,
                          track_id) VALUES(?,?)""",
                          (album.id, self.id))
            except sqlite3.IntegrityError:
                pass

        for artist in artists:
            try:
                c.execute("""INSERT INTO artist_track
                          (artist_id, track_id) VALUES(?,?)""",
                          (artist.id, self.id))
            except sqlite3.IntegrityError:
                pass

        db.commit()
        c.close()
        return True

    def save(self):
        dirty_attributes = {}

        # check if the internal dict has been modified
        for (attr, value) in self.__dict__.items():
            if self.__data[attr] != getattr(self, attr):
                dirty_attributes[attr] = value

        if len(dirty_attributes) > 0:
            db = DbManager()

            set_clause = utils.update_clause_from_dict(dirty_attributes)

            dirty_attributes[id] = self.id

            sql = " ".join(("UPDATE track"), set_clause, "WHERE id = :id")
            db.execute(sql, dirty_attributes)
            db.commit()

    def search(**search_params):
        """Find a track with the given params

        Args:
            tracknumber: dict, with 'data' and 'operator' keys
            name: dict, with 'data' and 'operator' keys
            grouping: dict, with 'data' and 'operator' keys
            filename: dict, with 'data' and 'operator' keys
        """

        db = DbManager()
        tracks = []

        # unpack search params
        where_params = {}
        value_params = {}
        for (attr, value) in search_params.items():
            where_params[attr] = value["operator"]
            value_params[attr] = value["data"]

        where_clause = utils.make_where_clause(where_params)

        result = None
        if where_clause:
            statement = " ".join(("SELECT * FROM track", where_clause))
            result = db.execute(statement, value_params)
        else:
            result = db.execute("SELECT * FROM track")

        for row in result:
            tracks.append(
                Track(id=row[0], tracknumber=row[1], name=row[3],
                      grouping=row[3], filename=row[4])
            )

        return tracks

    def find_by_path(path):
        db = DbManager()
        track = None

        for row in db.execute("SELECT * FROM track WHERE filename = ? LIMIT 1",
                              (path,)):
            track = Track(row[0])

        return track

    def store(filename, metadata):
        db = DbManager()
        c = db.cursor()

        artist_names = metadata["artist"]
        musicbrainz_artist_ids = []
        artistsorts = []
        try:
            musicbrainz_artist_ids = metadata["musicbrainz_artistid"]
        except KeyError:
            pass
        try:
            artistsorts = metadata["artistsort"]
        except KeyError:
            pass

        i = 0
        artists = []

        for artist_name in artist_names:
            musicbrainz_artistid = None
            artistsort = None
            try:
                musicbrainz_artistid = musicbrainz_artist_ids[i]
            except IndexError:
                pass
            try:
                artistsort = artistsorts[i]
            except IndexError:
                pass

            rows = None
            if musicbrainz_artistid:
                rows = c.execute("""SELECT * FROM artist WHERE
                    musicbrainz_artist_id = ?""",
                                 (musicbrainz_artistid,))
            else:
                rows = c.execute("""SELECT * FROM artist WHERE
                    name = ?""", (artist_name,))
            row = rows.fetchone()
            if row:
                artist = Artist(id=row[0], name=row[1],
                                sortname=row[2],
                                musicbrainz_artist_id=row[3])
            else:
                c.execute("""INSERT INTO artist
                    (name, sortname, musicbrainz_artist_id) VALUES(
                    ?,?,?)""", (artist_name, artistsort,
                                musicbrainz_artistid))

                artist = Artist(
                    id=c.lastrowid, name=artist_name,
                    sortname=artistsort,
                    musicbrainz_artist_id=musicbrainz_artistid
                )

                i += 1

            artists.append(artist)

        album_name = None
        album_date = None
        mb_albumid = None

        album = None
        try:
            album_name = metadata["album"][0]
        except KeyError:
            pass
        try:
            album_date = metadata["date"][0]
        except KeyError:
            pass

        try:
            mb_albumid = metadata["musicbrainz_albumid"][0]
        except KeyError:
            pass

        if mb_albumid:
            rows = c.execute(
                """SELECT * FROM album WHERE musicbrainz_albumid = ?""",
                (mb_albumid,)
            )

            row = rows.fetchone()

            if row:
                album = Album(id=row[0], name=row[1], date=row[2],
                              mb_albumid=row[3])
            else:
                c.execute("""INSERT INTO album (name, `date`,
                          musicbrainz_albumid) VALUES (?,?,?)""",
                          (album_name, album_date, mb_albumid))

                album = Album(id=c.lastrowid, name=album_name,
                              date=album_date, musicbrainz_albumid=mb_albumid)

        elif album_name:
            rows = c.execute(
                """SELECT album.* FROM album INNER JOIN album_artist ON
                album_artist.album_id = album.id WHERE album.name = ?
                AND artist_id = ?""", (album_name, artist.id)
            )
            row = rows.fetchone()

            if row:
                album = Album(id=row[0], name=row[1], date=row[2])
            else:
                c.execute("""INSERT INTO album (name, `date`) VALUES
                (?,?)""", (album_name, album_date))

                album = Album(id=c.lastrowid, name=album_name,
                              date=album_date)

        for artist in artists:
            if album:
                try:
                    c.execute(
                        """INSERT INTO album_artist (artist_id,
                        album_id) VALUES(?,?)""",
                        (artist.id, album.id)
                    )
                except sqlite3.IntegrityError:
                    pass

        track_number = None
        track_name = None
        track_grouping = None
        try:
            track_number = metadata["tracknumber"][0]
        except KeyError:
            pass
        try:
            track_name = metadata["title"][0]
        except KeyError:
            pass
        try:
            track_grouping = metadata["grouping"][0]
        except KeyError:
            pass

        track = None
        rows = c.execute("""SELECT * FROM track WHERE filename = ?""",
                         (filename,))
        row = rows.fetchone()
        if row:
            track = Track(id=row[0], tracknumber=row[1], name=row[2],
                          grouping=row[3], filename=row[4])
        else:
            c.execute("""INSERT INTO track (tracknumber, name,
                grouping, filename) VALUES(?,?,?,?)""",
                      (track_number, track_name, track_grouping,
                       filename))

            track = Track(id=c.lastrowid, tracknumber=track_number,
                          name=track_name, grouping=track_grouping,
                          filename=filename)

        if album:
            try:
                c.execute("""INSERT INTO album_track (album_id,
                          track_id) VALUES(?,?)""",
                          (album.id, track.id))
            except sqlite3.IntegrityError:
                pass

        for artist in artists:
            try:
                c.execute("""INSERT INTO artist_track
                          (artist_id, track_id) VALUES(?,?)""",
                          (artist.id, track.id))
            except sqlite3.IntegrityError:
                pass

        db.commit()
        c.close()
        return True
