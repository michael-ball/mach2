import configparser
import json

from flask import Flask

from models.album import Album
from models.artist import Artist
from models.track import Track


app = Flask(__name__)
app.config.from_object(__name__)


@app.route("/")
def hello():
    return "Hello world!"


@app.route("/search/album/<albumname>")
def album_search(albumname):
    albums = []
    for album in Album.search(name=albumname):
        albums.append(album.__dict__)

    return json.dumps(albums)


@app.route("/search/artist/<artistname>")
def artist_search(artistname):
    artists = []
    for artist in Artist.search(name=artistname):
        artists.append(artist.__dict__)

    return json.dumps(artists)


@app.route("/search/track/<trackname>")
def track_search(trackname):
    tracks = []
    for track in Track.search(name=trackname):
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/artist/<int:artist_id>/tracks")
def artist_tracks(artist_id):
    tracks = []
    artist = Artist(artist_id)

    for track in artist.tracks:
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/artist/<int:artist_id>/albums")
def artist_albums(artist_id):
    albums = []
    artist = Artist(artist_id)

    for album in artist.albums:
        albums.append(album.__dict__)

    return json.dumps(albums)


@app.route("/album/<int:album_id>/tracks")
def album_tracks(album_id):
    tracks = []
    album = Album(album_id)

    for track in album.tracks:
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/album/<int:album_id>/artists")
def album_artists(album_id):
    artists = []
    album = Album(album_id)

    for artist in album.artists:
        artists.append(artist.__dict__)

    return json.dumps(artists)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("mach2.ini")

    app.run(debug=config["DEFAULT"]["debug"])
