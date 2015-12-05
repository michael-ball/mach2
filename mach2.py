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
from models.user import User


DATABASE = "app.db"

compress = Compress()

app = Flask(__name__)
app.secret_key = """\xfc[\x16\x9d\x0f\x86;;\x9e_\x96\x01\xb7\xeay^\x8b\xa0E\x84
    \x91;\x18\xc2"""
app.config.from_object(__name__)

config = configparser.ConfigParser()
config.read("mach2.ini")

login_manager = LoginManager()
login_manager.login_view = "login"

login_manager.init_app(app)
compress.init_app(app)


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
@login_required
def index():
    return render_template("index.html", user=current_user)


@app.route("/albums")
@login_required
def albums():
    returned_albums = []
    albums = []

    order_by = request.args.get("order", None)
    order_direction = request.args.get("direction", None)
    lim = request.args.get("limit", None)
    off = request.args.get("offset", None)
    conditions = request.args.getlist("conditions")

    search_params = {}

    if conditions:
        field = conditions[0]
        operator = conditions[1]
        value = conditions[2]

        search_params[field] = {"data": value, "operator": operator}

    params = {}

    if order_by:
        params["order"] = order_by

    if order_direction:
        params["direction"] = order_direction

    if lim:
        params["limit"] = lim

    if off:
        params["offset"] = off

    all_params = params.copy()
    all_params.update(search_params)

    if search_params:
        returned_albums = Album.search(**all_params)
    else:
        returned_albums = Album.all(**params)

    for album in returned_albums:
        albums.append(album.__dict__)

    return json.dumps(albums)


@app.route("/albums/<int:album_id>/tracks")
@login_required
def album_tracks(album_id):
    tracks = []
    album = Album(id=album_id)

    for track in album.tracks:
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/albums/<int:album_id>/artists")
@login_required
def album_artists(album_id):
    artists = []
    album = Album(id=album_id)

    for artist in album.artists:
        artists.append(artist.__dict__)

    return json.dumps(artists)


@app.route("/albums/<int:album_id>")
@login_required
def album(album_id):
    album = Album(id=album_id)

    return json.dumps(album.__dict__)


@app.route("/albums/<album_name>")
@login_required
def album_search(album_name):
    albums = []

    for album in Album.search(name={"data": album_name, "operator": "LIKE"}):
        albums.append(album.__dict__)

    return json.dumps(albums)


@app.route("/artists")
@login_required
def artists():
    order_by = None
    order_direction = None
    lim = None
    off = None
    returned_artists = []
    artists = []

    if request.args.get("order"):
        order_by = request.args.get("order")

    if request.args.get("direction"):
        order_direction = request.args.get("direction")

    if request.args.get("limit"):
        lim = request.args.get("limit")

    if request.args.get("offset"):
        off = request.args.get("offset")

    if order_by:
        returned_artists = Artist.all(order=order_by,
                                      direction=order_direction,
                                      limit=lim, offset=off)
    else:
        returned_artists = Artist.all(limit=lim, offset=off)

    for artist in returned_artists:
        artists.append(artist.__dict__)

    return json.dumps(artists)


@app.route("/artists/<int:artist_id>/tracks")
@login_required
def artist_tracks(artist_id):
    tracks = []
    artist = Artist(id=artist_id)

    for track in artist.tracks:
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/artists/<int:artist_id>/albums")
@login_required
def artist_albums(artist_id):
    albums = []
    artist = Artist(id=artist_id)

    for album in artist.albums:
        albums.append(album.__dict__)

    return json.dumps(albums)


@app.route("/artists/<int:artist_id>")
@login_required
def artist_info(artist_id):
    artist = Artist(id=artist_id)

    return json.dumps(artist.__dict__)


@app.route("/artists/<artist_name>")
@login_required
def artist_search(artist_name):
    artists = []
    for artist in Artist.search(name={
                                "data": artist_name,
                                "operator": "LIKE"
                                }):
        artists.append(artist.__dict__)

    return json.dumps(artists)


@app.route("/tracks")
@login_required
def tracks():
    order_by = None
    order_direction = None
    lim = None
    off = None
    returned_tracks = []
    tracks = []

    if request.args.get("order"):
        order_by = request.args.get("order")

    if request.args.get("direction"):
        order_direction = request.args.get("direction")

    if request.args.get("limit"):
        lim = request.args.get("limit")

    if request.args.get("offset"):
        off = request.args.get("offset")

    if order_by:
        returned_tracks = Track.all(order=order_by, direction=order_direction,
                                    limit=lim, offset=off)
    else:
        returned_tracks = Track.all(limit=lim, offset=off)

    for track in returned_tracks:
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@app.route("/tracks/<int:track_id>/artists")
@login_required
def track_artists(track_id):
    artists = []
    track = Track(id=track_id)

    for artist in track.artists:
        artists.append(artist.__dict__)

    return json.dumps(artists)


@app.route("/tracks/<int:track_id>")
@login_required
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


@app.route("/tracks/<track_name>")
@login_required
def track_search(track_name):
    tracks = []
    for track in Track.search(name={"data": track_name, "operator": "LIKE"}):
        tracks.append(track.__dict__)

    return json.dumps(tracks)


@login_manager.user_loader
def load_user(userid):
    user = None
    result = query_db("SELECT * FROM user WHERE id = ?", [userid], one=True)

    if result:
        user = User(id=result[0], username=result[1], password_hash=result[2],
                    authenticated=1, active=result[4], anonymous=0)

    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = None
        result = query_db("SELECT * FROM user WHERE username = ?",
                          [request.form["username"]], one=True)

        if result:
            user = User(id=result[0],
                        username=result[1],
                        password_hash=result[2],
                        authenticated=0,
                        active=result[4],
                        anonymous=result[5])

        password = request.form["password"]

        if user and user.verify(password):
            login_user(user)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            user = None

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    app.run()
