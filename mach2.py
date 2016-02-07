import base64
import configparser
import json
import mimetypes
import os
import sqlite3
import tempfile

from flask import Blueprint, Flask, Response, current_app, g, redirect, \
    render_template, request, url_for
from flask.ext.compress import Compress
from flask.ext.login import LoginManager, current_user, login_required
from flask.ext.login import login_user, logout_user
from gevent import subprocess

from models.album import Album
from models.artist import Artist
from models.track import Track
from models.user import User

import builtins


builtins.library_db = None


config = configparser.ConfigParser()
config.read("mach2.ini")

mach2 = Blueprint("mach2", __name__)

login_manager = LoginManager()
login_manager.login_view = "mach2.login"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        setattr(g, "_database", db)

    return db


@mach2.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@login_manager.request_loader
def load_user_from_request(request):
    # first, try to login using the api_key url arg
    api_key = request.args.get('api_key', None)

    if not api_key:
        # next, try to login using Basic Auth
        api_key = request.headers.get('Authorization', None)

        if api_key:
            api_key = api_key.replace('Basic ', '', 1)
            try:
                api_key = base64.b64decode(api_key)
            except TypeError:
                pass

    if api_key:
        user = None
        result = query_db("SELECT * FROM user WHERE api_key = ?",
                          [api_key], one=True)

        if result:
            user = User(id=result[0],
                        username=result[1],
                        password_hash=result[2],
                        authenticated=0,
                        active=result[4],
                        anonymous=result[5])

        if user:
            return user

    # finally, return None if both methods did not login the user
    return None


@mach2.route("/")
@login_required
def index():
    return render_template("index.html", user=current_user)


@mach2.route("/albums")
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
        returned_albums = Album.search(db=builtins.library_db, **all_params)
    else:
        returned_albums = Album.all(db=builtins.library_db, **params)

    for album in returned_albums:
        albums.append(album.as_dict())

    return json.dumps(albums)


@mach2.route("/albums/<int:album_id>/tracks")
@login_required
def album_tracks(album_id):
    tracks = []
    album = Album(db=builtins.library_db, id=album_id)

    for track in album.tracks:
        tracks.append(track.as_dict())

    return json.dumps(tracks)


@mach2.route("/albums/<int:album_id>/artists")
@login_required
def album_artists(album_id):
    artists = []
    album = Album(db=builtins.library_db, id=album_id)

    for artist in album.artists:
        artists.append(artist.as_dict())

    return json.dumps(artists)


@mach2.route("/albums/<int:album_id>")
@login_required
def album(album_id):
    album = Album(db=builtins.library_db, id=album_id)

    return json.dumps(album.as_dict())


@mach2.route("/albums/<album_name>")
@login_required
def album_search(album_name):
    albums = []

    for album in Album.search(db=builtins.library_db,
                              name={"data": album_name, "operator": "LIKE"}):
        albums.append(album.as_dict())

    return json.dumps(albums)


@mach2.route("/artists")
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
        returned_artists = Artist.all(db=builtins.library_db, order=order_by,
                                      direction=order_direction,
                                      limit=lim, offset=off)
    else:
        returned_artists = Artist.all(db=builtins.library_db, limit=lim,
                                      offset=off)

    for artist in returned_artists:
        artists.append(artist.as_dict())

    return json.dumps(artists)


@mach2.route("/artists/<int:artist_id>/tracks")
@login_required
def artist_tracks(artist_id):
    tracks = []
    artist = Artist(db=builtins.library_db, id=artist_id)

    for track in artist.tracks:
        tracks.append(track.as_dict())

    return json.dumps(tracks)


@mach2.route("/artists/<int:artist_id>/albums")
@login_required
def artist_albums(artist_id):
    albums = []
    artist = Artist(db=builtins.library_db, id=artist_id)

    for album in artist.albums:
        albums.append(album.as_dict())

    return json.dumps(albums)


@mach2.route("/artists/<int:artist_id>")
@login_required
def artist_info(artist_id):
    artist = Artist(id=artist_id, db=builtins.library_db)

    return json.dumps(artist.as_dict())


@mach2.route("/artists/<artist_name>")
@login_required
def artist_search(artist_name):
    artists = []
    for artist in Artist.search(db=builtins.libary_db,
                                name={
                                    "data": artist_name,
                                    "operator": "LIKE"
                                }):
        artists.append(artist.as_dict())

    return json.dumps(artists)


@mach2.route("/tracks")
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
        returned_tracks = Track.all(db=builtins.library_db, order=order_by,
                                    direction=order_direction, limit=lim,
                                    offset=off)
    else:
        returned_tracks = Track.all(db=builtins.library_db,
                                    limit=lim, offset=off)

    for track in returned_tracks:
        tracks.append(track.as_dict())

    return json.dumps(tracks)


@mach2.route("/tracks/<int:track_id>/artists")
@login_required
def track_artists(track_id):
    artists = []
    track = Track(db=builtins.library_db, id=track_id)

    for artist in track.artists:
        artists.append(artist.as_dict())

    return json.dumps(artists)


@mach2.route("/tracks/<int:track_id>")
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

    local_track = Track(db=builtins.library_db, id=track_id)

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


@mach2.route("/tracks/<track_name>")
@login_required
def track_search(track_name):
    tracks = []
    for track in Track.search(db=builtins.library_db,
                              name={"data": track_name, "operator": "LIKE"}):
        tracks.append(track.as_dict())

    return json.dumps(tracks)


@login_manager.user_loader
def load_user(userid):
    user = None
    result = query_db("SELECT * FROM user WHERE id = ?", [userid], one=True)

    if result:
        user = User(id=result[0], username=result[1], password_hash=result[2],
                    authenticated=1, active=result[4], anonymous=0)

    return user


@mach2.route("/login", methods=["GET", "POST"])
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
            return redirect(request.args.get("next") or url_for("mach2.index"))
        else:
            user = None

    return render_template("login.html")


@mach2.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@mach2.before_app_first_request
def setup_globals():
    setattr(g, "_db_path", current_app.config["DATABASE"])


def create_app(database=None, library=None):
    app = Flask(__name__)
    if database:
        app.config["DATABASE"] = database
    else:
        app.config["DATABASE"] = config["DEFAULT"]["app_db"]

    if library:
        builtins.library_db = library

    app.config["DEBUG"] = config["DEFAULT"]["debug"]
    app.config["SECRET_KEY"] = config["DEFAULT"]["secret_key"]

    app.register_blueprint(mach2)

    login_manager.init_app(app)

    compress = Compress()
    compress.init_app(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
