"""An app to serve a music library."""
import base64
import os
import subprocess
import sqlite3
import tempfile

import mimetypes

from flask import (Blueprint, Flask, Response, abort, current_app, g, jsonify,
                   redirect, render_template, request, url_for)
from flask_compress import Compress
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from six.moves import configparser

from db.db_manager import DbManager
from models.album import Album
from models.artist import Artist
from models.track import Track
from models.user import User


_CONFIG = configparser.ConfigParser()
_CONFIG.read("mach2.ini")

MACH2 = Blueprint("mach2", __name__)

_LOGIN_MANAGER = LoginManager()
_LOGIN_MANAGER.login_view = "mach2.login"


def get_db():
    """Get the application database."""
    database = getattr(g, "_database", None)
    if database is None:
        database = sqlite3.connect(current_app.config["DATABASE"])
        database.row_factory = sqlite3.Row
        setattr(g, "_database", database)

    return database


@MACH2.teardown_app_request
def close_connection(exception):
    """Close the database connection."""
    database = getattr(g, "_database", None)
    if database is not None:
        database.close()


def query_db(query, args=(), one=False):
    """Query the application database."""
    cur = get_db().execute(query, args)
    result = cur.fetchall()
    cur.close()
    return (result[0] if result else None) if one else result


@_LOGIN_MANAGER.request_loader
def load_user_from_request(req):
    """Load the user from the request.

    Args:
        req (flask.Request): The request object.

    """
    # first, try to login using the api_key url arg
    api_key = req.args.get('api_key', None)

    if not api_key:
        # next, try to login using Basic Auth
        api_key = req.headers.get('Authorization', None)

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
                        anonymous=result[5],
                        transcode_command=result[7])

        if user:
            return user

    # finally, return None if both methods did not login the user
    return None


@MACH2.route("/")
@login_required
def index():
    """Return the index."""
    return render_template("index.html", user=current_user)


@MACH2.route("/albums")
@login_required
def albums():
    returned_albums = []
    result_albums = []

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
        returned_albums = Album.search(current_app.config["LIBRARY"],
                                       **all_params)
    else:
        returned_albums = Album.all(current_app.config["LIBRARY"], **params)

    for returned_album in returned_albums:
        result_albums.append(returned_album.as_dict())

    return jsonify(result_albums)


@MACH2.route("/albums/<int:album_id>/tracks")
@login_required
def album_tracks(album_id):
    result_tracks = []
    returned_album = Album(current_app.config["LIBRARY"], id=album_id)

    for album_track in returned_album.tracks:
        result_tracks.append(album_track.as_dict())

    return jsonify(result_tracks)


@MACH2.route("/albums/<int:album_id>/artists")
@login_required
def album_artists(album_id):
    result_artists = []
    returned_album = Album(current_app.config["LIBRARY"], id=album_id)

    for album_artist in returned_album.artists:
        result_artists.append(album_artist.as_dict())

    return jsonify(result_artists)


@MACH2.route("/albums/<int:album_id>")
@login_required
def album(album_id):
    returned_album = Album(current_app.config["LIBRARY"], id=album_id)

    return jsonify(returned_album.as_dict())


@MACH2.route("/albums/<album_name>")
@login_required
def album_search(album_name):
    result_albums = []

    for returned_album in Album.search(current_app.config["LIBRARY"],
                                       name={"data": album_name,
                                             "operator": "LIKE"}):
        result_albums.append(returned_album.as_dict())

    return jsonify(result_albums)


@MACH2.route("/artists")
@login_required
def artists():
    order_by = None
    order_direction = None
    lim = None
    off = None
    returned_artists = []
    result_artists = []

    if request.args.get("order"):
        order_by = request.args.get("order")

    if request.args.get("direction"):
        order_direction = request.args.get("direction")

    if request.args.get("limit"):
        lim = request.args.get("limit")

    if request.args.get("offset"):
        off = request.args.get("offset")

    if order_by:
        returned_artists = Artist.all(current_app.config["LIBRARY"],
                                      order=order_by,
                                      direction=order_direction, limit=lim,
                                      offset=off)
    else:
        returned_artists = Artist.all(current_app.config["LIBRARY"], limit=lim,
                                      offset=off)

    for returned_artist in returned_artists:
        result_artists.append(returned_artist.as_dict())

    return jsonify(result_artists)


@MACH2.route("/artists/<int:artist_id>/tracks")
@login_required
def artist_tracks(artist_id):
    result_tracks = []
    returned_artist = Artist(current_app.config["LIBRARY"], id=artist_id)

    for artist_track in returned_artist.tracks:
        result_tracks.append(artist_track.as_dict())

    return jsonify(result_tracks)


@MACH2.route("/artists/<int:artist_id>/albums")
@login_required
def artist_albums(artist_id):
    result_albums = []
    returned_artist = Artist(current_app.config["LIBRARY"], id=artist_id)

    for artist_album in returned_artist.albums:
        result_albums.append(artist_album.as_dict())

    return jsonify(result_albums)


@MACH2.route("/artists/<int:artist_id>")
@login_required
def artist_info(artist_id):
    artist = Artist(current_app.config["LIBRARY"], id=artist_id)

    return jsonify(artist.as_dict())


@MACH2.route("/artists/<artist_name>")
@login_required
def artist_search(artist_name):
    result_artists = []
    for artist in Artist.search(current_app.config["LIBRARY"],
                                name={
                                    "data": artist_name,
                                    "operator": "LIKE"
    }):
        result_artists.append(artist.as_dict())

    return jsonify(artists)


@MACH2.route("/tracks")
@login_required
def tracks():
    order_by = None
    order_direction = None
    lim = None
    off = None
    returned_tracks = []
    result_tracks = []

    if request.args.get("order"):
        order_by = request.args.get("order")

    if request.args.get("direction"):
        order_direction = request.args.get("direction")

    if request.args.get("limit"):
        lim = request.args.get("limit")

    if request.args.get("offset"):
        off = request.args.get("offset")

    if order_by:
        returned_tracks = Track.all(current_app.config["LIBRARY"],
                                    order=order_by, direction=order_direction,
                                    limit=lim, offset=off)
    else:
        returned_tracks = Track.all(current_app.config["LIBRARY"],
                                    limit=lim, offset=off)

    for returned_track in returned_tracks:
        result_tracks.append(returned_track.as_dict())

    return jsonify(result_tracks)


@MACH2.route("/tracks/<int:track_id>/artists")
@login_required
def track_artists(track_id):
    result_artists = []
    returned_track = Track(current_app.config["LIBRARY"], id=track_id)

    for track_artist in returned_track.artists:
        result_artists.append(track_artist.as_dict())

    return jsonify(result_artists)


@MACH2.route("/tracks/<int:track_id>")
@login_required
def track(track_id):
    def stream_file(filename, proc, chunksize=8192):
        with open(filename, "rb") as streamed_file:
            while True:
                chunk = streamed_file.read(chunksize)
                if proc.poll() is None or chunk:
                    yield chunk
                elif not chunk:
                    os.remove(filename)
                    break

    local_track = Track(current_app.config["LIBRARY"], id=track_id)

    dummy, temp_filename = tempfile.mkstemp()

    transcode_tokens = current_user.transcode_command.split()
    transcode_command_items = []
    for token in transcode_tokens:
        if token == "{filename}":
            transcode_command_items.append(local_track.filename)
        elif token == "{output}":
            transcode_command_items.append(temp_filename)
        else:
            transcode_command_items.append(token)

    proc = subprocess.Popen(transcode_command_items)

    mime_string = "application/octet-stream"

    mime = mimetypes.guess_type(temp_filename)
    if mime[0]:
        mime_string = mime[0]

    resp = Response(stream_file(temp_filename, proc), mimetype=mime_string)

    if mime[1]:
        resp.headers["Content-Encoding"] = mime[1]

    return resp


@MACH2.route("/tracks/<track_name>")
@login_required
def track_search(track_name):
    result_tracks = []
    for returned_track in Track.search(current_app.config["LIBRARY"],
                                       name={"data": track_name,
                                             "operator": "LIKE"}):
        result_tracks.append(returned_track.as_dict())

    return jsonify(result_tracks)


@MACH2.route("/user", defaults={"user_id": None},
             methods=["GET", "POST", "PUT"])
@MACH2.route("/user/<int:user_id>", methods=["DELETE", "GET", "PUT"])
@login_required
def users(user_id):
    """Create, retrieve, update or delete a user.

    Args:
        user_id (obj:`int`, optional): The ID of the user. Defaults to None.
            If none, and the request uses a GET or PUT method, this works
            on the currently logged in user.

    """
    def update_user(user, user_data):
        """Update the user with the supplied data.

        Args:
            user (obj:`User`): The user to update.
            user_data (obj:`Dict[str, str]`): The data to update the user with.

        """
        db_conn = get_db()
        if "password" in user_data:
            password_hash, api_key = user.new_password(
                user_data["password"])

            update_query = ("UPDATE user SET password_hash = ?, "
                            "api_key = ? WHERE id = ?")

            rows_updated = 0

            with db_conn:
                rows_updated = get_db().execute(
                    update_query, (password_hash, api_key, user.id))

            if rows_updated > 0:
                user.password_hash = password_hash
                user.api_key = api_key
            else:
                error = dict(message="Unable to update user")
                return jsonify(error), 500

        if "transcode_command" in user_data:
            update_query = ("UPDATE user SET transcode_command = ? "
                            "WHERE id = ?")

            rows_updated = 0

            with db_conn:
                rows_updated = db_conn.execute(
                    update_query, (user_data["transcode_command"], user.id))

            if rows_updated > 0:
                user.transcode_command = user_data[
                    "transcode_command"]
            else:
                error = dict(message="Unable to update user")
                return jsonify(error), 500

        return jsonify(user.to_dict())

    if user_id:
        local_user = load_user(user_id)

        if not local_user:
            abort(404)

        if request.method == "DELETE":
            query = "DELETE FROM user WHERE user = ?"

            get_db().execute(query, user_id)

            return "", 204

        elif request.method == "PUT":
            user_data = request.get_json()

            if not user_data:
                abort(415)

            return update_user(local_user, user_data)

    else:
        if request.method == "POST":

            new_user_data = request.get_json()

            if not new_user_data:
                abort(415)

            #  TODO: create new user and return the object

        local_user = load_user(current_user.id)

        if request.method == "PUT":
            user_data = request.get_json()

            if not user_data:
                abort(415)

            return update_user(local_user, user_data)

        return jsonify(local_user.to_dict())


@_LOGIN_MANAGER.user_loader
def load_user(user_id):
    local_user = None
    result = query_db("SELECT * FROM user WHERE id = ?", [user_id], one=True)

    if result:
        local_user = User(
            id=result[0], username=result[1],password_hash=result[2],
            authenticated=1, active=result[4], anonymous=0,
            transcode_command=result[7])

    return local_user


@MACH2.route("/login", methods=["GET", "POST"])
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
                        anonymous=result[5],
                        transcode_command=result[7])

        password = request.form["password"]

        if user and user.verify(password):
            login_user(user)
            return redirect(request.args.get("next") or url_for("mach2.index"))
        else:
            user = None

    return render_template("login.html")


@MACH2.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@MACH2.before_app_first_request
def setup_globals():
    setattr(g, "_db_path", current_app.config["DATABASE"])


def create_app(database=None, library=None):
    app = Flask(__name__)
    if database:
        app.config["DATABASE"] = database
    else:
        app.config["DATABASE"] = _CONFIG.get("DEFAULT", "database")

    if library:
        app.config["LIBRARY"] = library
    else:
        app.config["LIBRARY"] = DbManager(_CONFIG.get("DEFAULT", "library"))

    app.config["DEBUG"] = _CONFIG.get("DEFAULT", "debug")
    app.config["SECRET_KEY"] = _CONFIG.get("DEFAULT", "secret_key")

    app.register_blueprint(MACH2)

    _LOGIN_MANAGER.init_app(app)

    compress = Compress()
    compress.init_app(app)

    return app


if __name__ == "__main__":
    APP = create_app()
    APP.run()
