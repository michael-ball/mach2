#!/usr/bin/env python
import configparser
import mutagen
import os

from models.track import Track


def run(path=None):
    print("Scanning files")

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
    file_store = []

    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = "".join([root, "/", name])
            file_store.append(file_path)

    file_store.sort()
    j = 0
    media_files = 0
    print("Storing files")
    for file_path in file_store:
        j += 1
        m = mutagen.File(file_path, easy=True)
        if m:
            if not Track.store(file_path, m):
                print("Problem saving %s" % (file_path,))

            media_files += 1
        print(
            "%d%% complete, (%d files)" % (((j / len(file_store)) * 100),
                                           j)
        )
    print("Stored %d tracks" % (media_files,))


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
