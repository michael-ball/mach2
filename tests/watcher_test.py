"""Tests for the watcher module."""
from os import remove
from os.path import dirname, join, realpath
from shutil import copy, move, rmtree
from tempfile import mkdtemp
import unittest

import mutagen
import six

from db.db_manager import DbManager
from models.track import Track
from watcher import LibraryWatcher


if six.PY2:
    def _u(string):
        return unicode(string, encoding="utf_8")
else:
    def _u(string):
        return string


class WatcherTestCase(unittest.TestCase):
    """Defines tests for the watcher module.

    Extends:
        unittest.Testcase

    """

    @classmethod
    def setUpClass(cls):
        """Set up fixtures for the tests."""
        cls._tempdir = mkdtemp()
        cls._tempdbdir = mkdtemp()
        cls._db_path = join(cls._tempdbdir, "test.db")
        copy(join(dirname(realpath(__file__)), "test.db"), cls._db_path)
        cls._db = DbManager(cls._db_path)
        cls._watcher = LibraryWatcher(cls._tempdir, cls._db_path)

    @classmethod
    def tearDownClass(cls):
        """Remove test fixtures."""
        cls._watcher.stop()
        rmtree(cls._tempdbdir)
        rmtree(cls._tempdir)

    def test_watcher_actions(self):
        """Test creating, moving, modifying and deleting a file."""
        new_file = join(dirname(realpath(__file__)), "testnew.ogg")
        copy(new_file, self._tempdir)

        self._watcher.check_for_events()

        found_track = Track.find_by_path(join(self._tempdir, "testnew.ogg"),
                                         self._db)
        assert found_track
        assert "testnew.ogg" in found_track.filename
        assert found_track.artists
        found_artist = False
        for artist in found_track.artists:
            if _u("Art Ist") == artist.name:
                found_artist = True
                break

        assert found_artist

        original_file = join(self._tempdir, "testnew.ogg")
        moved_file = join(self._tempdir, "testmoved.ogg")
        move(original_file, moved_file)

        self._watcher.check_for_events()

        moved_track = Track.find_by_path(moved_file, self._db)

        assert moved_track
        assert "testmoved.ogg" in moved_track.filename

        original_metadata = mutagen.File(moved_file, easy=True)

        original_metadata["title"] = [_u("New title")]
        original_metadata.save()

        self._watcher.check_for_events()

        modified_track = Track.find_by_path(moved_file, self._db)

        assert modified_track
        assert modified_track.name == "New title"

        remove(moved_file)

        self._watcher.check_for_events()

        assert Track.find_by_path(moved_file, self._db) is None
