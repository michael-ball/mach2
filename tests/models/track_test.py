import mutagen

from models.track import Track


def test_instance(database):
    track = Track(database, 1)
    assert track.id == 1
    assert track.name == "Non album track"
    assert track.filename == "1.mp3"
    assert track.artists

def test_as_dict(database):
    track = Track(database, 1)

    track_dict = track.as_dict()

    assert "_db" not in track_dict.keys()
    assert track_dict["id"] == 1
    assert track_dict["name"] == "Non album track"
    assert track_dict["filename"] == "1.mp3"


def test_album(database):
    track1 = Track(database, 1)
    assert track1.album is None
    track2 = Track(database, 2)
    assert track2.album.name == "Album 1"
    assert track2.album.date == "1999-02-04"


def test_artists(database):
    track = Track(database, 1)
    assert track.artists
    assert track.artists[0].name == "Artist 1"


def test_find_by_path(database):
    track1 = Track.find_by_path("album/2.mp3", database)

    assert track1.filename == "album/2.mp3"
    assert track1.name == "Album track 2"
    assert track1.grouping == "swing"
    assert track1.artists

    nonexistent_track = Track.find_by_path("path/does/not/exist.mp3",
                                           database)
    assert nonexistent_track is None


def test_search(database):
    tracks = Track.search(database, name={"data": "Album track %",
                                          "operator": "LIKE"})

    assert tracks is not None
    assert len(tracks) == 2


def test_store(database, test_file):
    metadata = mutagen.File(test_file, easy=True)

    test_track = Track.store(test_file, metadata, database)

    assert test_track.filename == test_file
    assert test_track.name == "Silence"
    assert test_track.grouping == "Jazz"
    assert test_track.tracknumber == 3

    assert test_track.album.name == "Dummy album"
    assert test_track.album.date == "2003"

    assert test_track.artists
    assert test_track.artists[0].name == "Test Artist Flaf"


def test_update(database, test_file):
    metadata = {"artist": ["New artist"], "title": ["New title"]}

    test_track = Track.find_by_path(test_file, database)
    test_track.update(metadata)

    assert test_track.artists
    assert len(test_track.artists) == 1
    assert test_track.artists[0].name == "New artist"
    assert test_track.name == "New title"


def test_save(database, test_file):
    test_track = Track.find_by_path(test_file, database)

    test_track.name = "Totally new name"
    test_track.save()

    new_track_to_test = Track.find_by_path(test_file, database)

    assert new_track_to_test.name == "Totally new name"


def test_delete(database, test_file):
    test_track = Track.find_by_path(test_file, database)

    test_track.delete()

    should_not_exist = Track.find_by_path(test_file, database)

    assert should_not_exist is None
