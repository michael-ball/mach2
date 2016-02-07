from models.artist import Artist


def test_instance(database):
    album = Artist(id=1, db=database)
    assert album.id == 1
    assert album.name == "Artist 1"


def test_albums(database):
    artist1 = Artist(id=1, db=database)
    assert len(artist1.albums) == 0
    artist2 = Artist(id=2, db=database)
    assert len(artist2.albums) == 1
    assert artist2.albums[0].name == "Album 1"
    assert artist2.albums[0].date == "1999-02-04"


def test_tracks(database):
    artist1 = Artist(id=1, db=database)
    assert len(artist1.tracks) == 1
    assert artist1.tracks[0].name == "Non album track"
    assert artist1.tracks[0].tracknumber is None
    assert artist1.tracks[0].filename == "1.mp3"
    artist2 = Artist(id=2, db=database)
    assert artist2.tracks[0].name == "Album track 1"
    assert artist2.tracks[0].tracknumber == 1
    assert artist2.tracks[0].filename == "album/1.mp3"
    assert artist2.tracks[1].name == "Album track 2"
    assert artist2.tracks[1].tracknumber == 2
    assert artist2.tracks[1].grouping == "swing"
    assert artist2.tracks[1].filename == "album/2.mp3"


def test_delete(database):
    with database.conn:
        cursor = database.cursor()

        cursor.execute("INSERT INTO artist (name) VALUES(?)", ("Test artist",))

        artist_id = cursor.lastrowid

        artist = Artist(artist_id, db=database)

        assert artist.delete()

    test_artist = Artist(artist_id, db=database)
    assert not hasattr(test_artist, "name")


def test_search(database):
    search_payload = {"name": {"data": "Artist 1", "operator": "="}}
    artist_results = Artist.search(db=database, **search_payload)

    assert len(artist_results) > 0

    invalid_search_payload = {"name": {"data": "This artist does not exist",
                                       "operator": "="}}
    no_artist_results = Artist.search(db=database, **invalid_search_payload)

    assert len(no_artist_results) == 0


def test_all(database):
    artist_results = Artist.all(db=database)

    assert len(artist_results) > 0
