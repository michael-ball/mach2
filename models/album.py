from common import utils
from db.db_manager import DbManager


class Album():
    def __init__(self, id=None, **kwargs):
        if id is not None:
            db = DbManager()
            for row in db.execute("""SELECT * FROM album WHERE id = ?""",
                                  (id,)):
                setattr(self, "id", id)
                setattr(self, "name", row[1])
                setattr(self, "date", row[2])
        else:
            for (key, value) in kwargs.items():
                setattr(self, key, value)

    def delete(self):
        db = DbManager()

        for track in self.tracks:
            track.delete()

        delete_sql = "DELETE FROM album WHERE id = ?"
        db.execute(delete_sql, (self.id,))

        delete_track_rel_sql = "DELETE FROM album_track WHERE album_id = ?"
        db.execute(delete_track_rel_sql, (self.id,))

        delete_artist_rel_sql = "DELETE FROM album_artist WHERE album_id = ?"
        db.execute(delete_artist_rel_sql, (self.id,))

        db.commit()

        return True

    @property
    def artists(self):
        from models.artist import Artist

        if not hasattr(self, "_artists"):
            setattr(self, "_artists", [])

            db = DbManager()

            for row in db.execute("""SELECT artist.* FROM artist INNER JOIN
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

            for row in db.execute("""SELECT track.* FROM track
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

            set_clause = utils.update_clause_from_dict(dirty_attributes)

            dirty_attributes[id] = self.id
            
            sql = " ".join(("UPDATE album"), set_clause, "WHERE id = :id")
            db.execute(sql, dirty_attributes)
            db.commit()

    def search(**search_params):
        albums = []

        db = DbManager()

        where_clause = utils.make_where_clause(search_params)

        result = None
        if where_clause:
            statement = " ".join(("SELECT * FROM album", where_clause))
            result = db.execute(statement, search_params)
        else:
            result = db.execute("SELECT * FROM album")

        for row in result:
            albums.append(
                Album(id=row[0], name=row[1], date=row[2])
            )

        return albums
