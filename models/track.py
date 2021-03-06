import logging
import sqlite3

from common import utils
from models.artist import Artist
from models.album import Album
from models.base import BaseModel


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


class Track(BaseModel):

    def __init__(self, db, id=None, **kwargs):
        self._db = db

        self.__data = {}

        if id is not None:
            for row in self._db.execute("SELECT * FROM track WHERE id = ?",
                                        (id,)):
                for key in ["id", "tracknumber", "name", "grouping",
                            "filename"]:
                    setattr(self, key, row[key])
                    self.__data[key] = row[key]
        else:
            for (key, value) in kwargs.items():
                setattr(self, key, value)
                self.__data[key] = value

    def delete(self):
        delete_sql = "DELETE FROM track WHERE id = ?"

        with self._db.conn:
            self._db.execute(delete_sql, (self.id,))

            # If there is an old album, remove it if it no longer has any
            # tracks
            try:
                del self._album
            except Exception:
                pass

            old_album = self.album

            if old_album:
                self._db.execute("DELETE FROM album_track WHERE track_id = ?",
                                 (self.id,))

                if not old_album.tracks:
                    old_album.delete()

            # If there are old artists, remove them if they no longer have
            # any tracks
            try:
                del self._artists
            except Exception:
                pass
            old_artists = self.artists

            for old_artist in old_artists:
                self._db.execute("DELETE FROM artist_track WHERE track_id = "
                                 "?", (self.id,))

                if not old_artist.tracks:
                    old_artist.delete()

        return True

    @property
    def db(self):
        return self._db


    @db.setter
    def db(self, db):
        self._db = db

    @property
    def album(self):
        if not hasattr(self, "_album"):
            setattr(self, "_album", None)

            for row in self._db.execute("SELECT album.* FROM album INNER "
                                        "JOIN album_track ON album.id = "
                                        "album_track.album_id WHERE "
                                        "track_id = ? LIMIT 1", (self.id,)):
                setattr(self, "_album", Album(id=row["id"], db=self._db,
                                              name=row["name"],
                                              date=row["date"]))

        return self._album

    @property
    def artists(self):
        if not hasattr(self, "_artists"):
            cursor = self._db.cursor()

            setattr(self, "_artists", [])
            for row in cursor.execute("SELECT artist.* FROM artist INNER JOIN "
                                      "artist_track ON artist.id = "
                                      "artist_track.artist_id WHERE "
                                      "artist_track.track_id = ?",
                                      (self.id,)):
                self._artists.append(Artist(id=row["id"], db=self._db,
                                            name=row["name"],
                                            sortname=row["sortname"],
                                            musicbrainz_artistid=row[
                                                "musicbrainz_artistid"]))

        return self._artists

    def update(self, metadata):
        c = self._db.cursor()

        artist_changed = False
        album_changed = False

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
            artist = None
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
                rows = c.execute("SELECT * FROM artist WHERE "
                                 "musicbrainz_artistid = ?",
                                 (musicbrainz_artistid,))
            else:
                rows = c.execute("SELECT * FROM artist WHERE name = ?",
                                 (artist_name,))

            row = rows.fetchone()

            if row:
                artist = Artist(id=row["id"], db=self._db, name=row["name"],
                                sortname=row["sortname"],
                                musicbrainz_artistid=row[
                                    "musicbrainz_artistid"])

                if artist.name != artist_name:
                    c.execute("UPDATE artist SET name = ? WHERE id = ?",
                              (artist_name, artist.id))
                    artist.name = artist_name

                if artist.sortname != artistsort:
                    c.execute("UPDATE artist SET sortname = ? WHERE id = ?",
                              (artistsort, id))
                    artist.sortname = artistsort

            else:
                c.execute("INSERT INTO artist (name, sortname, "
                          "musicbrainz_artistid) VALUES(?, ?, ?)",
                          (artist_name, artistsort, musicbrainz_artistid))

                artist = Artist(
                    id=c.lastrowid, db=self._db, name=artist_name,
                    sortname=artistsort,
                    musicbrainz_artistid=musicbrainz_artistid
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
                "SELECT * FROM album WHERE musicbrainz_albumid = ?",
                (mb_albumid,)
            )

            row = rows.fetchone()

            if row:
                album = Album(id=row["id"], db=self._db, name=row["name"],
                              date=row["date"],
                              musicbrainz_albumid=row["musicbrainz_albumid"])
            else:
                c.execute("INSERT INTO album (name, `date`, "
                          "musicbrainz_albumid) VALUES (?, ?, ?)",
                          (album_name, album_date, mb_albumid))

                album = Album(id=c.lastrowid, db=self._db, name=album_name,
                              date=album_date, musicbrainz_albumid=mb_albumid)

        elif album_name:
            rows = c.execute(
                "SELECT album.* FROM album INNER JOIN album_artist ON "
                "album_artist.album_id = album.id WHERE album.name = ? "
                "AND artist_id = ?", (album_name, artist.id)
            )
            row = rows.fetchone()

            if row:
                album = Album(id=row["id"], db=self._db, name=row["name"],
                              date=row["date"],
                              musicbrainz_albumid=row["musicbrainz_albumid"])
            else:
                c.execute("INSERT INTO album (name, `date`) VALUES (?, ?)",
                          (album_name, album_date))

                album = Album(id=c.lastrowid, db=self._db, name=album_name,
                              date=album_date)

        if album:
            if album.name != album_name:
                c.execute("UPDATE album SET name = ? WHERE id = ?",
                          (album_name, album.id))
                album.name = album_name

            if album.date != album_date:
                c.execute("UPDATE album SET date = ? WHERE id = ?",
                          (album_date, album.id))
                album.date = album_date

        track_number = None
        track_name = None
        track_grouping = None
        try:
            track_number = metadata["tracknumber"][0]
            setattr(self, "tracknumber", track_number)
        except KeyError:
            pass
        try:
            track_name = metadata["title"][0]
            setattr(self, "name", track_name)
        except KeyError:
            pass
        try:
            track_grouping = metadata["grouping"][0]
            setattr(self, "grouping", track_grouping)
        except KeyError:
            pass

        c.execute("UPDATE track SET tracknumber = ?, name = ?, grouping = ? "
                  "WHERE id = ?", (track_number, track_name, track_grouping,
                                   self.id))

        # If there is an old album, remove it if it no longer has any tracks
        try:
            del self._album
        except Exception:
            pass

        old_album = self.album
        if old_album:
            c.execute("DELETE FROM album_track WHERE track_id = ?",
                      (self.id,))

        # If there are old artists, remove them if they no longer have
        # any tracks
        try:
            del self._artists
        except Exception:
            pass
        old_artists = self.artists

        for old_artist in old_artists:
            c.execute("DELETE FROM artist_track WHERE track_id = ?",
                      (self.id,))

        if album:
            try:
                c.execute("INSERT INTO album_track (album_id, track_id) "
                          "VALUES(?, ?)", (album.id, self.id))
            except sqlite3.IntegrityError:
                pass

            if not old_album.tracks:
                old_album.delete()

            setattr(self, "_album", album)

        for artist in artists:
            try:
                c.execute("INSERT INTO artist_track (artist_id, track_id) "
                          "VALUES(?, ?)", (artist.id, self.id))
            except sqlite3.IntegrityError:
                pass

            if not old_artist.tracks:
                old_artist.delete()

            if album:
                try:
                    c.execute(
                        "INSERT INTO album_artist (artist_id, album_id) "
                        "VALUES(?, ?)", (artist.id, album.id))
                except sqlite3.IntegrityError:
                    pass

        if artists:
            setattr(self, "_artists", artists)

        c.close()
        self._db.commit()

        return True

    def save(self):
        dirty_attributes = {}

        # check if the internal dict has been modified
        for (attr, value) in self.__dict__.items():
            try:
                if self.__data[attr] != getattr(self, attr):
                    dirty_attributes[attr] = value
            except AttributeError:
                pass
            except KeyError:
                pass

        if len(dirty_attributes) > 0:
            set_clause = utils.update_clause_from_dict(dirty_attributes)

            dirty_attributes["id"] = self.id

            sql = " ".join(("UPDATE track", set_clause, "WHERE id = :id"))

            with self._db.conn:
                self._db.execute(sql, dirty_attributes)

    @classmethod
    def search(cls, database, **search_params):
        """Find a track with the given params

        Args:
            tracknumber: dict, with 'data' and 'operator' keys
            name: dict, with 'data' and 'operator' keys
            grouping: dict, with 'data' and 'operator' keys
            filename: dict, with 'data' and 'operator' keys
        """
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
            result = database.execute(statement, value_params)
        else:
            result = database.execute("SELECT * FROM track")

        for row in result:
            tracks.append(
                Track(id=row["id"], db=database, tracknumber=row["tracknumber"],
                      name=row["name"], grouping=row["grouping"],
                      filename=row["filename"])
            )

        return tracks

    @classmethod
    def find_by_path(cls, path, database):
        track = None

        for row in database.execute("SELECT * FROM track WHERE filename = ? "
                                    "LIMIT 1", (path,)):
            track = Track(id=row["id"], db=database,
                          tracknumber=row["tracknumber"], name=row["name"],
                          grouping=row["grouping"], filename=row["filename"])

        return track

    @classmethod
    def store(cls, filename, metadata, database):
        if Track.find_by_path(filename, database):
            return True

        c = database.cursor()

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
            row = None
            if musicbrainz_artistid:
                rows = c.execute("SELECT * FROM artist WHERE "
                                 "musicbrainz_artistid = ?",
                                 (musicbrainz_artistid,))
                row = rows.fetchone()
                if not row:
                    rows = c.execute("SELECT * FROM artist WHERE name = ? "
                                     "AND musicbrainz_artistid IS NULL",
                                     (artist_name,))
                    row = rows.fetchone()

            if not row:
                rows = c.execute("SELECT * FROM artist WHERE name = ?",
                                 (artist_name,))
                row = rows.fetchone()

            if row:
                artist = Artist(id=row["id"], db=database, name=row["name"],
                                sortname=row["sortname"],
                                musicbrainz_artistid=row[
                                    "musicbrainz_artistid"])

                if (musicbrainz_artistid and
                    (not hasattr(artist, "musicbrainz_artistid") or
                     not artist.musicbrainz_artistid)):
                    c.execute("UPDATE artist SET musicbrainz_artistid = ? "
                              "WHERE id = ?",
                              (musicbrainz_artistid, artist.id))

                if (artistsort and
                    (not hasattr(artist, "sortname") or
                     not artist.sortname)):
                    c.execute("UPDATE artist SET sortname = ? WHERE id = ?",
                              (artistsort, artist.id))

            else:
                c.execute("INSERT INTO artist (name, sortname, "
                          "musicbrainz_artistid) VALUES(?, ?, ?)",
                          (artist_name, artistsort, musicbrainz_artistid))

                artist = Artist(
                    id=c.lastrowid, db=database, name=artist_name,
                    sortname=artistsort,
                    musicbrainz_artistid=musicbrainz_artistid
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
            rows = c.execute("SELECT * FROM album WHERE "
                             "musicbrainz_albumid = ?", (mb_albumid,))

            row = rows.fetchone()

            if row:
                album = Album(id=row["id"], db=database, name=row["name"],
                              date=row["date"], musicbrainz_albumid=row[
                                  "musicbrainz_albumid"])
            else:
                c.execute("INSERT INTO album (name, `date`, "
                          "musicbrainz_albumid) VALUES (?, ?, ?)",
                          (album_name, album_date, mb_albumid))

                album = Album(id=c.lastrowid, db=database, name=album_name,
                              date=album_date, musicbrainz_albumid=mb_albumid)

        elif album_name:
            for artist in artists:
                rows = c.execute("SELECT album.* FROM album INNER JOIN "
                                 "album_artist ON album_artist.album_id = "
                                 "album.id WHERE album.name = ? AND "
                                 "artist_id = ?", (album_name, artist.id))
                row = rows.fetchone()

                if row:
                    album = Album(id=row["id"], db=database, name=row["name"],
                                  date=row["date"])
                else:
                    c.execute("INSERT INTO album (name, `date`) VALUES(?, ?)",
                              (album_name, album_date))

                    album = Album(id=c.lastrowid, db=database, name=album_name,
                                  date=album_date)

        for artist in artists:
            if album:
                try:
                    c.execute("INSERT INTO album_artist (artist_id, album_id) "
                              "VALUES(?, ?)", (artist.id, album.id))
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
        rows = c.execute("SELECT * FROM track WHERE filename = ?", (filename,))
        row = rows.fetchone()
        if row:
            track = Track(id=row["id"], db=database,
                          tracknumber=row["tracknumber"], name=row["name"],
                          grouping=row["grouping"], filename=row["filename"])
        else:
            c.execute("INSERT INTO track (tracknumber, name, grouping, "
                      "filename) VALUES(?, ?, ?, ?)",
                      (track_number, track_name, track_grouping,
                       filename))

            track = Track(id=c.lastrowid, db=database, tracknumber=track_number,
                          name=track_name, grouping=track_grouping,
                          filename=filename)

        if album:
            try:
                c.execute("INSERT INTO album_track (album_id, track_id) "
                          "VALUES(?,?)", (album.id, track.id))
            except sqlite3.IntegrityError:
                pass

        for artist in artists:
            try:
                c.execute("INSERT INTO artist_track (artist_id, track_id) "
                          "VALUES(?, ?)", (artist.id, track.id))
            except sqlite3.IntegrityError:
                pass

        database.commit()
        c.close()

        return track

    @classmethod
    def all(cls, database, order="track.id", direction="ASC", limit=None,
            offset=None):
        tracks = []

        select_string = "SELECT * FROM track LEFT JOIN artist_track ON " \
            "artist_track.track_id = track.id LEFT JOIN artist ON " \
            "artist_track.artist_id = artist.id LEFT JOIN album_track ON " \
            "album_track.track_id = track.id LEFT JOIN album ON " \
            "album_track.album_id = album.id ORDER BY %s %s" % (order,
                                                                direction)

        if limit and offset:
            select_string = " ".join((select_string,
                                      "LIMIT %s OFFSET %s" % (limit, offset)))

        result = database.execute(select_string)

        for row in result:
            tracks.append(Track(id=row["id"], db=database,
                                tracknumber=row["tracknumber"],
                                name=row["name"], grouping=row["name"],
                                filename=row["filename"]))

        return tracks
