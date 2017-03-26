from common import utils
from models.base import BaseModel


class Album(BaseModel):
    """Represents an album."""

    def __init__(self, db, id=None, **kwargs):
        self._db = db

        if id is not None:
            for row in self._db.execute("SELECT * FROM album WHERE id = ?",
                                        (id,)):
                setattr(self, "id", id)
                setattr(self, "name", row[1])
                setattr(self, "date", row[2])
        else:
            for (key, value) in kwargs.items():
                setattr(self, key, value)

    def delete(self):
        for track in self.tracks:
            track.delete()

        with self._db.conn:
            delete_album = "DELETE FROM album WHERE id = ?"
            self._db.execute(delete_album, (self.id,))

            delete_track_rel = "DELETE FROM album_track WHERE album_id = ?"
            self._db.execute(delete_track_rel, (self.id,))

            delete_artist_rel = "DELETE FROM album_artist WHERE album_id = ?"
            self._db.execute(delete_artist_rel, (self.id,))

        return True

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, db):
        self._db = db

    @property
    def artists(self):
        from models.artist import Artist

        if not hasattr(self, "_artists"):
            setattr(self, "_artists", [])

            for row in self._db.execute("SELECT artist.* FROM artist INNER "
                                        "JOIN album_artist ON artist.id = "
                                        "album_artist.artist_id WHERE "
                                        "album_id = ? ORDER BY name ASC",
                                        (self.id,)):
                artist = Artist(id=row[0], db=self._db, name=row[1],
                                sortname=row[2], musicbrainz_artistid=row[3])
                self._artists.append(artist)

        return self._artists

    @property
    def tracks(self):
        from models.track import Track

        if not hasattr(self, "_tracks"):
            setattr(self, "_tracks", [])

            for row in self._db.execute("SELECT track.* FROM track INNER "
                                        "JOIN album_track ON track.id = "
                                        "album_track.track_id WHERE "
                                        "album_id = ? ORDER BY tracknumber "
                                        "ASC", (self.id,)):

                track = Track(id=row["id"], db=self._db,
                              tracknumber=row["tracknumber"],
                              name=row["name"], grouping=row["grouping"],
                              filename=row["filename"])
                self._tracks.append(track)

        return self._tracks

    def save(self):
        dirty_attributes = {}

        # check if the internal dict has been modified
        for (attr, value) in self.__dict__.items():
            if self.__data[attr] != getattr(self, attr):
                dirty_attributes[attr] = value

        if len(dirty_attributes) > 0:
            set_clause = utils.update_clause_from_dict(dirty_attributes)

            dirty_attributes["id"] = self.id

            sql = " ".join(("UPDATE album", set_clause, "WHERE id = :id"))

            with self._db.conn:
                self._db.execute(sql, dirty_attributes)

    @classmethod
    def search(cls, database, **search_params):
        """Find an album with the given params

        Args:
            name: dict, with 'data' and 'operator' keys
            date: dict, with 'data' and 'operator' keys
            musicbrainz_albumid: dict, with 'data' and 'operator' keys
        """
        albums = []

        # unpack search params
        where_params = {}
        value_params = {}
        for (attr, value) in search_params.items():
            where_params[attr] = value["operator"]

            if value["operator"] == "BETWEEN":
                items = value["data"].split(" ")

                value_params["".join((attr, "1"))] = items[0]
                value_params["".join((attr, "2"))] = items[2]
            else:
                value_params[attr] = value["data"]

        where_clause = utils.make_where_clause(where_params)

        result = None
        if where_clause:
            statement = " ".join(("SELECT * FROM album", where_clause))
            result = database.execute(statement, value_params)
        else:
            result = database.execute("SELECT * FROM album")

        for row in result:
            albums.append(
                Album(id=row["id"], db=database, name=row["name"],
                      date=row["date"])
            )

        return albums

    @classmethod
    def all(cls, database, order="album.id", direction="ASC", limit=None,
            offset=None):

        albums = []

        select_string = """SELECT * FROM album LEFT JOIN album_artist ON
            album_artist.album_id = album.id LEFT JOIN artist ON
            album_artist.artist_id = artist.id ORDER BY %s %s""" % (order,
                                                                    direction)

        if limit is not None and offset is not None:
            select_string = " ".join((select_string,
                                      "LIMIT %s OFFSET %s" % (limit, offset)))

        result = database.execute(select_string)

        for row in result:
            albums.append(
                Album(id=row["id"], db=database, name=row["name"],
                      date=row["date"])
            )

        return albums
