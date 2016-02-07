from models.album import Album


def test_instance(database):
    album = Album(id=1, db=database)
    assert album.id == 1
    assert album.name == "Album 1"
    assert album.date == "1999-02-04"


def test_artists(database):
    album = Album(id=1, db=database)
    assert len(album.artists) == 1
    assert album.artists[0].name == "Artist 2"


def test_tracks(database):
    album = Album(id=1, db=database)
    assert len(album.tracks) == 2
    assert album.tracks[0].name == "Album track 1"
    assert album.tracks[0].tracknumber == 1
    assert album.tracks[0].filename == "album/1.mp3"
    assert album.tracks[1].name == "Album track 2"
    assert album.tracks[1].tracknumber == 2
    assert album.tracks[1].grouping == "swing"
    assert album.tracks[1].filename == "album/2.mp3"


def test_delete(database):
    with database.conn:
        cursor = database.cursor()

        cursor.execute("INSERT INTO album (name, date) VALUES(?,?)",
                       ("Test album", "2016-02-05"))

        album_id = cursor.lastrowid
        cursor.close()

        album = Album(album_id, db=database)

        assert album.delete()

    test_album = Album(album_id, db=database)
    assert not hasattr(test_album, "name")


def test_search(database):
    search_payload = {"name": {"data": "Album 1", "operator": "="}}
    album_results = Album.search(db=database, **search_payload)

    assert len(album_results) > 0

    invalid_search_payload = {"name": {"data": "This album does not exist",
                                       "operator": "="}}
    no_album_results = Album.search(db=database, **invalid_search_payload)

    assert len(no_album_results) == 0


def test_all(database):
    album_results = Album.all(db=database)

    assert len(album_results) > 0
