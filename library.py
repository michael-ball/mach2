#!/usr/bin/env python
"""This module implements a library for storing information on audio tracks."""
import logging
import os

from gevent import monkey, queue
from gevent.pool import Group
import mutagen
import six
from six.moves import configparser, range

from db.db_manager import DbManager
from models.track import Track


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

if six.PY2:
    def _u(string):
        return unicode(string, encoding="utf_8")
else:
    def _u(string):
        return string


class MediaLibrary(object):
    """Implements methods for storing and managing media in a library."""

    def __init__(self, media_dir, database):
        """Create a media library object.

        Args:
            media_dir (str): The path of the media directory
            database (DatabaseManager): The media database

        """
        self.__media_dir = media_dir
        self.__database = database

    def store_track_task(self, file_queue):
        """Store a track from the supplied queue.

        Args:
            file_queue (Queue[str]): A queue containing file paths.

        """
        try:
            path = file_queue.get()
            metadata = mutagen.File(path, easy=True)
            Track.store(_u(path), metadata, self.__database)
        except queue.Empty:
            pass

    def run(self, path=None):
        """Store all tracks located in the supplied path.

        Args:
            path (str): The path to an audio file or directory containing audio
                files.

        """
        if path is not None:
            if os.path.isdir(path):
                self.store_dir(path)
            else:
                self.store_file(path)
        else:
            self.store_dir(self.__media_dir)

        self.__database.export()

    def store_file(self, path):
        """Store an audio file.

        Args:
            path (str): The path to an audio file.

        """
        metadata = mutagen.File(path, easy=True)
        if metadata:
            if not Track.store(_u(path), metadata, self.__database):
                _LOGGER.error("Problem saving %s", path)

    def store_dir(self, path):
        """Store all audio files in a directory.

        Args:
            path (str): The path to a directory.

        """
        _LOGGER.info("Scanning files")

        file_queue = queue.Queue()

        allowed_extensions = [".mp3", ".ogg", ".flac", ".wav", ".aac", ".ape"]
        for root, dummy, files in os.walk(path):
            for name in files:
                file_path = "".join([root, "/", name])
                dummy, ext = os.path.splitext(file_path)

                if ext.lower() in allowed_extensions:
                    file_queue.put(file_path)

        _LOGGER.info("Storing tracks")

        tasks = Group()
        for i in range(file_queue.qsize()):
            tasks.spawn(self.store_track_task, file_queue)

        tasks.join()

        _LOGGER.info("Done")

    def delete_file(self, path):
        """Delete a file from the library.

        Args:
            path (str): The path for the file.

        """
        track = Track.find_by_path(_u(path), self.__database)

        if track:
            track_album = track.album
            track_artists = track.artists

            track.delete()

            if track_album and len(track_album.tracks) == 0:
                track_album.delete()

            for artist in track_artists:
                if len(artist.tracks) == 0:
                    artist.delete()

    def update_file(self, path):
        """Update a file in the library.

        Args:
            path (str): The path for the file.

        """
        metadata = mutagen.File(path, easy=True)
        if metadata:
            track = Track.find_by_path(_u(path), self.__database)
            track.update(metadata)

    def update_track_filename(self, oldpath, newpath):
        """Update a track's filename.

        Args:
            oldpath (str): The old path of the file.
            newpath (str): The new path of the file.

        """
        track = Track.find_by_path(_u(oldpath), self.__database)
        track.filename = _u(newpath)
        track.save()


if __name__ == "__main__":
    monkey.patch_all(thread=False)
    __CONFIG = configparser.ConfigParser()
    __CONFIG.read("mach2.ini")

    db = DbManager(__CONFIG.get("DEFAULT", "library"))
    media_path = __CONFIG.get("DEFAULT", "media_dir")

    media_library = MediaLibrary(media_path, db)

    media_library.run()
