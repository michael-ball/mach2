"""
Defines a watcher service to update the media library.

This module implements a monitoring service to update the library when files
are added or removed from the media library directory.
"""
from atexit import register
import logging
import os

import pyinotify

from db.db_manager import DbManager
from library import MediaLibrary


_LOGGER = logging.getLogger(__name__)


class EventHandler(pyinotify.ProcessEvent):
    """Event handler defining actions for adding/moving/removing files.

    Extends:
        pyinotify.ProcessEvent

    """

    def __init__(self, media_library, pevent=None, **kwargs):
        """Create the event handler.

        Args:
            media_library (MediaLibrary): The media library.

        """
        self.__library = media_library

        super(self.__class__, self).__init__(pevent=None, **kwargs)

    def process_IN_CREATE(self, event):
        """Add a file to the library when it is created.

        Args:
            event (pynotify.Event) - the event raised by inotify.

        """
        _LOGGER.debug("Creating: %s", event.pathname)
        self.__library.run(event.pathname)

    def process_IN_DELETE(self, event):
        """Remove a file from the library when it is deleted.

        Args:
            event (pynotify.Event) - the event raised by inotify.

        """
        _LOGGER.debug("Removing: %s", event.pathname)

        if not os.path.isdir(event.pathname):
            self.__library.delete_file(event.pathname)

    def process_IN_MOVED_TO(self, event):
        """Update a file's information in the library when it is moved.

        Args:
            event (pynotify.Event) - the event raised by inotify.

        """
        _LOGGER.debug("Moved to: %s", event.pathname)
        self.__library.update_track_filename(event.src_pathname,
                                             event.pathname)

        # moving the file may also hint that the metadata has changed
        self.__library.update_file(event.pathname)

    def process_IN_MODIFY(self, event):
        """Update a file's information in the library when it is modified.

        Args:
            event (pynotify.Event) - the event raised by inotify.

        """
        _LOGGER.debug("Modified: %s", event.pathname)

        if not os.path.isdir(event.pathname):
            self.__library.update_file(event.pathname)


class LibraryWatcher(object):
    """Watches the library."""

    def __init__(self, path, database_path):
        """Create the LibraryWatcher.

        Args:
            path (str): the patch of the directory to watch.

        """
        _LOGGER.info("Setting up library watcher")
        database = DbManager(database_path)
        library = MediaLibrary(path, database)
        _LOGGER.info("Using %s", database)

        if not hasattr(self, "path"):
            setattr(self, "path", path)

        if not hasattr(self, "wm"):
            setattr(self, "wm", pyinotify.WatchManager())

        mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | \
            pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM | \
            pyinotify.IN_MODIFY

        if not hasattr(self, "notifier"):
            setattr(self,
                    "notifier",
                    pyinotify.Notifier(self.wm, EventHandler(library),
                                       timeout=10))

        if not hasattr(self, "wdd"):
            setattr(self, "wdd", self.wm.add_watch(path, mask, rec=True,
                                                   auto_add=True))

        self.notifier.coalesce_events()

        _LOGGER.info("Set up watch on %s", path)

        register(self.stop)

        while True:
            self.check_for_events()

    def stop(self):
        """Remove all the watched paths."""
        if self.wdd[self.path] > 0:
            self.wm.rm_watch(self.wdd[self.path], rec=True)

    def check_for_events(self):
        """Check for any notification events."""
        assert self.notifier._timeout is not None
        self.notifier.process_events()
        while self.notifier.check_events():
            self.notifier.read_events()
            self.notifier.process_events()


if __name__ == "__main__":
    from six.moves import configparser

    config = configparser.ConfigParser()
    config.read("mach2.ini")

    watch = LibraryWatcher(config.get("DEFAULT", "media_dir"),
                           config.get("DEFAULT", "library"))
