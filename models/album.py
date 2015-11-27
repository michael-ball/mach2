from common import utils
from db.db_manager import DbManager


class Album():
    def __init__(self, id=None, **kwargs):
        if id is not None:
            db = DbManager()
            cursor = db.cursor()

            for row in cursor.execute("SELECT * FROM album WHERE id = ?",
                                      (id,)):
                setattr(self, "id", id)
                setattr(self, "name", row[1])
                setattr(self, "date", row[2])
        else:
            for (key, value) in kwargs.items():
                setattr(self, key, value)

    def delete(self):
        db = DbManager()
        cursor = db.cursor()

        for track in self.tracks:
            track.delete()

        cursor.execute("BEGIN TRANSACTION")

        delete_sql = "DELETE FROM album WHERE id = ?"
        cursor.execute(delete_sql, (self.id,))

        delete_track_rel_sql = "DELETE FROM album_track WHERE album_id = ?"
        cursor.execute(delete_track_rel_sql, (self.id,))

        delete_artist_rel_sql = "DELETE FROM album_artist WHERE album_id = ?"
        cursor.execute(delete_artist_rel_sql, (self.id,))

        cursor.execute("COMMIT TRANSACTION")

        return True

    @property
    def artists(self):
        from models.artist import Artist

        if not hasattr(self, "_artists"):
            setattr(self, "_artists", [])

            db = DbManager()
            cursor = db.cursor()

            for row in cursor.execute("""SELECT artist.* FROM artist INNER JOIN
                                      album_artist ON artist.id =
                                      album_artist.artist_id WHERE album_id = ?
                                      ORDER BY name ASC""", (self.id,)):
                artist = Artist(id=row[0], name=row[1], sortname=row[2],
                                musicbrainz_artistid=row[3])
                self._artists.append(artist)

        return self._artists

    @property
    def tracks(self):
        from models.track import Track

        if not hasattr(self, "_tracks"):
            setattr(self, "_tracks", [])

            db = DbManager()
            cursor = db.cursor()

            for row in cursor.execute("""SELECT track.* FROM track
                                      INNER JOIN album_track ON track.id =
                                      album_track.track_id WHERE album_id = ?
                                      ORDER BY tracknumber ASC""", (self.id,)):

                track = Track(id=row[0], tracknumber=row[1], name=row[2],
                              grouping=row[3], filename=row[4])
                self._tracks.append(track)

        return self._tracks

    def save(self):
        dirty_attributes = {}

        # check if the internal dict has been modified
        for (attr, value) in self.__dict__.items():
            if self.__data[attr] != getattr(self, attr):
                dirty_attributes[attr] = value

        if len(dirty_attributes) > 0:
            db = DbManager()
            cursor = db.cursor()

            set_clause = utils.update_clause_from_dict(dirty_attributes)

            dirty_attributes[id] = self.id

            sql = " ".join(("UPDATE album"), set_clause, "WHERE id = :id")
            cursor.execute(sql, dirty_attributes)

    def search(**search_params):
        """Find an album with the given params

        Args:
            name: dict, with 'data' and 'operator' keys
            date: dict, with 'data' and 'operator' keys
            musicbrainz_albumid: dict, with 'data' and 'operator' keys
        """
        albums = []

        db = DbManager()
        cursor = db.cursor()

        # unpack search params
        where_params = {}
        value_params = {}
        for (attr, value) in search_params.items():
            where_params[attr] = value["operator"]
            value_params[attr] = value["data"]

        where_clause = utils.make_where_clause(where_params)

        result = None
        if where_clause:
            statement = " ".join(("SELECT * FROM album", where_clause))
            result = cursor.execute(statement, value_params)
        else:
            result = cursor.execute("SELECT * FROM album")

        for row in result:
            albums.append(
                Album(id=row[0], name=row[1], date=row[2])
            )

        return albums

    def all(order="album.id", direction="ASC", limit=None, offset=None):
        db = DbManager()
        cursor = db.cursor()
        albums = []

        select_string = """SELECT * FROM album LEFT JOIN album_artist ON
            album_artist.album_id = album.id LEFT JOIN artist ON
            album_artist.artist_id = artist.id ORDER BY %s %s""" % (order,
                                                                    direction)

        if limit is not None and offset is not None:
            select_string = " ".join((select_string,
                                     "LIMIT %s OFFSET %s" % (limit, offset)))

        result = cursor.execute(select_string)

        for row in result:
            albums.append(
                Album(id=row[0], name=row[1], date=row[2])
            )

        return albums
