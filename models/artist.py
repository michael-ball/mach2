from common import utils
from db.db_manager import DbManager


class Artist:
    def __init__(self, id=None, **kwargs):
        if id is not None:
            db = DbManager()
            cursor = db.cursor()

            for row in cursor.execute("SELECT * FROM artist WHERE id = ?",
                                      (id,)):
                setattr(self, "id", id)
                setattr(self, "name", row[1])
                setattr(self, "sortname", row[2])
                setattr(self, "musicbrainz_artistid", row[3])
        else:
            for (key, value) in kwargs.items():
                setattr(self, key, value)

    def delete(self):
        db = DbManager()
        cursor = db.cursor()

        for album in self.albums:
            album.delete()

        delete_sql = "DELETE FROM artist WHERE id = ?"
        cursor.execute(delete_sql, (self.id,))

        delete_track_rel_sql = "DELETE FROM artist_track WHERE artist_id = ?"
        cursor.execute(delete_track_rel_sql, (self.id,))

        delete_album_rel_sql = "DELETE FROM album_artist WHERE artist_id = ?"
        cursor.execute(delete_album_rel_sql, (self.id,))

        return True

    @property
    def tracks(self):
        from models.track import Track

        if not hasattr(self, "_tracks"):
            setattr(self, "_tracks", [])

            db = DbManager()
            cursor = db.cursor()

            for row in cursor.execute("""SELECT track.* FROM track
                                      INNER JOIN artist_track ON track.id =
                                      artist_track.track_id WHERE artist_id = ?
                                      ORDER BY name ASC""", (self.id,)):

                track = Track(id=row[0], tracknumber=row[1], name=row[2],
                              grouping=row[3], filename=row[4])
                self._tracks.append(track)

        return self._tracks

    @property
    def albums(self):
        from models.album import Album

        if not hasattr(self, "_albums"):
            setattr(self, "_albums", [])

            db = DbManager()
            cursor = db.cursor()

            for row in cursor.execute("""SELECT album.* FROM album
                                      INNER JOIN album_artist ON album.id =
                                      album_artist.album_id WHERE artist_id = ?
                                      ORDER BY date ASC""", (self.id,)):
                album = Album(id=row[0], name=row[1], date=row[2])
                self._albums.append(album)

        return self._albums

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

            sql = " ".join(("UPDATE artist"), set_clause, "WHERE id = :id")
            cursor.execute(sql, dirty_attributes)

    def search(**search_params):
        """Find an artist with the given params

        Args:
            name: dict, with 'data' and 'operator' keys
            sortname: dict, with 'data' and 'operator' keys
            musicbrainz_artist_id: dict, with 'data' and 'operator' keys
        """
        artists = []

        db = DbManager()
        cursor = db.cursor()

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
            result = cursor.execute(statement, value_params)
        else:
            result = cursor.execute("SELECT * FROM artist")

        for row in result:
            artists.append(
                Artist(id=row[0], name=row[1], sortname=row[2],
                       musicbrainz_artistid=row[3])
            )

        return artists
