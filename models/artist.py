from common import utils
from models.base import BaseModel


class Artist(BaseModel):

    def __init__(self, db, id=None, **kwargs):
        self._db = db

        if id is not None:
            for row in self._db.execute("SELECT * FROM artist WHERE id = ?",
                                        (id,)):
                for key in ["id", "name", "sortname", "musicbrainz_artistid"]:
                    setattr(self, key, row[key])
        else:
            for (key, value) in kwargs.items():
                setattr(self, key, value)

    def delete(self):
        for album in self.albums:
            album.delete()

        with self._db.conn:
            delete_artist = "DELETE FROM artist WHERE id = ?"
            self._db.execute(delete_artist, (self.id,))

            delete_track_rel = "DELETE FROM artist_track WHERE artist_id = ?"
            self._db.execute(delete_track_rel, (self.id,))

            delete_album_rel = "DELETE FROM album_artist WHERE artist_id = ?"
            self._db.execute(delete_album_rel, (self.id,))

        return True

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, db):
        self._db = db

    @property
    def tracks(self):
        from models.track import Track

        if not hasattr(self, "_tracks"):
            setattr(self, "_tracks", [])

            for row in self._db.execute("SELECT track.* FROM track INNER "
                                        "JOIN artist_track ON track.id = "
                                        "artist_track.track_id WHERE "
                                        "artist_id = ? ORDER BY name ASC",
                                        (self.id,)):

                track = Track(id=row["id"], db=self._db,
                              tracknumber=row["tracknumber"], name=row["name"],
                              grouping=row["grouping"],
                              filename=row["filename"])
                self._tracks.append(track)

        return self._tracks

    @property
    def albums(self):
        from models.album import Album

        if not hasattr(self, "_albums"):
            setattr(self, "_albums", [])

            for row in self._db.execute("SELECT album.* FROM album INNER "
                                        "JOIN album_artist ON album.id = "
                                        "album_artist.album_id WHERE "
                                        "artist_id = ? ORDER BY date ASC",
                                        (self.id,)):
                album = Album(id=row["id"], db=self._db, name=row["name"],
                              date=row["date"])
                self._albums.append(album)

        return self._albums

    def save(self):
        dirty_attributes = {}

        # check if the internal dict has been modified
        for (attr, value) in self.__dict__.items():
            if self.__data[attr] != getattr(self, attr):
                dirty_attributes[attr] = value

        if len(dirty_attributes) > 0:
            set_clause = utils.update_clause_from_dict(dirty_attributes)

            dirty_attributes[id] = self.id

            sql = " ".join(("UPDATE artist", set_clause, "WHERE id = :id"))

            with self._db.conn:
                self._db.execute(sql, dirty_attributes)

    @classmethod
    def search(cls, database, **search_params):
        """Find an artist with the given params

        Args:
            name: dict, with 'data' and 'operator' keys
            sortname: dict, with 'data' and 'operator' keys
            musicbrainz_artist_id: dict, with 'data' and 'operator' keys
        """
        artists = []

        # unpack search params
        where_params = {}
        value_params = {}
        for (attr, value) in search_params.items():
            where_params[attr] = value["operator"]
            value_params[attr] = value["data"]

        where_clause = utils.make_where_clause(where_params)

        result = []
        if where_clause:
            statement = " ".join(("SELECT * FROM artist", where_clause))
            result = database.execute(statement, value_params)
        else:
            result = database.execute("SELECT * FROM artist")

        for row in result:
            artists.append(
                Artist(id=row["id"], db=database, name=row["name"],
                       sortname=row["sortname"],
                       musicbrainz_artistid=row["musicbrainz_artistid"])
            )

        return artists

    @classmethod
    def all(cls, database, order="sortname", direction="ASC", limit=None,
            offset=None):

        artists = []

        select_string = "SELECT * FROM artist ORDER BY %s %s" % (order,
                                                                 direction)

        if limit is not None and offset is not None:
            select_string = " ".join((select_string,
                                      "LIMIT %s OFFSET %s" % (limit, offset)))

        result = database.execute(select_string)

        for row in result:
            artists.append(
                Artist(id=row["id"], db=database, name=row["name"],
                       sortname=row["sortname"],
                       musicbrainz_artistid=row["musicbrainz_artistid"])
            )

        return artists
