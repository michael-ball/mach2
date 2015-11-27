#!/usr/bin/env python
import configparser
import gevent
from gevent import queue
import logging
import mutagen
import os

from models.track import Track


file_store = queue.Queue()

logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


def store_track_task():
    while not file_store.empty():
        path = file_store.get()
        m = mutagen.File(path, easy=True)
        Track.store(path, m)

        gevent.sleep(0)


def run(path=None):
    if path is not None:
        if os.path.isdir(path):
            store_dir(path)
        else:
            store_file(path)
    else:
        store_dir("/media/Music")


def store_file(path):
    m = mutagen.File(path, easy=True)
    if m:
        if not Track.store(path, m):
            print("Problem saving %s" % (path,))


def store_dir(path):
    logger = logging.getLogger("store_dir")
    logger.info("Scanning files")

    allowed_extensions = [".mp3", ".ogg", ".flac", ".wav", ".aac", ".ape"]
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = "".join([root, "/", name])
            file, ext = os.path.splitext(file_path)

            if ext in allowed_extensions:
                file_store.put(file_path)

    logger.info("Storing tracks")            
    gevent.joinall([gevent.spawn(store_track_task)] * 6)
    logger.info("Done")


def delete_file(path):
    track = Track.find_by_path(path)

    if track:
        track_album = track.album
        track_artists = track.artists

        track.delete()

        if track_album and len(track_album.tracks) == 0:
            track_album.delete()

        for artist in track_artists:
            if len(artist.tracks) == 0:
                artist.delete()


def update_file(path):
    m = mutagen.File(path, easy=True)
    if m:
        track = Track.find_by_path(path)
        track.update(m)


def update_track_filename(oldpath, newpath):
    track = Track.find_by_path(oldpath)
    track.filename = newpath
    track.save()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("mach2.ini")

    run(config["DEFAULT"]["media_dir"])
