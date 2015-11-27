import configparser
import json
import mimetypes
import os
import sqlite3
import subprocess
import tempfile
import threading

from flask import Flask, Response, current_app, g, redirect, render_template
from flask import request, url_for
from flask.ext.compress import Compress
from flask.ext.login import LoginManager, current_user, login_required
from flask.ext.login import login_user, logout_user


from models.album import Album
from models.artist import Artist
from models.track import Track


DATABASE = "app.db"

compress = Compress()

app = Flask(__name__)
app.config.from_object(__name__)

config = configparser.ConfigParser()
config.read("mach2.ini")

app.config["DEBUG"] = config["DEFAULT"]["debug"]

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.session_protection = "strong"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        setattr(g, "_database", db)

    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route("/")
def hello():
    return "Hello world!"


@app.route("/search/album/<album_name>")
def album_search(album_name):
    albums = []
    for album in Album.search(name={'data': album_name, 'operator': 'LIKE'}):
        albums.append(album.__dict__)

    return json.dumps(albums)


@app.route("/search/artist/<artist_name>")
def artist_search(artist_name):
    artists = []
    for artist in Artist.search(name={
                                'data': artist_name,
                                'operator': 'LIKE'
                                }):
        artists.append(artist.__dict__)

    return json.dumps(artists)


@app.route("/search/track/<track_name>")
def track_search(track_name):
    tracks = []
    for track in Track.search(name={'data': track_name, 'operator': 'LIKE'}):
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/artist/<int:artist_id>/tracks")
def artist_tracks(artist_id):
    tracks = []
    artist = Artist(id=artist_id)

    for track in artist.tracks:
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/artist/<int:artist_id>/albums")
def artist_albums(artist_id):
    albums = []
    artist = Artist(id=artist_id)

    for album in artist.albums:
        albums.append(album.__dict__)

    return json.dumps(albums)


@app.route("/album/<int:album_id>/tracks")
def album_tracks(album_id):
    tracks = []
    album = Album(id=album_id)

    for track in album.tracks:
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/album/<int:album_id>/artists")
def album_artists(album_id):
    artists = []
    album = Album(id=album_id)

    for artist in album.artists:
        artists.append(artist.__dict__)

    return json.dumps(artists)


@app.route("/track/<int:track_id>")
def track(track_id):
    def stream_file(filename, chunksize=8192):
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(chunksize)
                if chunk:
                    yield chunk
                else:
                    os.remove(filename)
                    break

    local_track = Track(track_id)

    fd, temp_filename = tempfile.mkstemp()

    subprocess.call(["ffmpeg", "-y", "-i", local_track.filename, "-acodec",
                     "libopus", "-b:a", "64000", "-f", "opus", temp_filename])

    mime_string = "application/octet-stream"

    mime = mimetypes.guess_type(temp_filename)
    if mime[0]:
        mime_string = mime[0]

    resp = Response(stream_file(temp_filename), mimetype=mime_string)

    if mime[1]:
        resp.headers["Content-Encoding"] = mime[1]

    return resp

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("mach2.ini")

    login_manager.init_app(app)
    compress.init_app(app)

    app.run()
