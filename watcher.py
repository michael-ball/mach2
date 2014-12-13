import atexit
import configparser

import pyinotify

import library


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print("Creating:", event.pathname)
        library.run(event.pathname)

    def process_IN_DELETE(self, event):
        print("Removing:", event.pathname)
        library.delete_file(event.pathname)

    def process_IN_MOVED_TO(self, event):
        print("Moved to:", event.pathname)
        library.update_track_filename(event.src_pathname, event.pathname)

    def process_IN_MODIFY(self, event):
        print("Modified:", event.pathname)
        library.update_file(event.pathname)


class LibraryWatcher:

    def __init__(self, path):
        print("Setting up library watcher")

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
                    pyinotify.ThreadedNotifier(self.wm, EventHandler()))

        self.notifier.coalesce_events()
        self.notifier.start()

        if not hasattr(self, "wdd"):
            setattr(self, "wdd", self.wm.add_watch(path, mask, rec=True,
                                                   auto_add=True))

        print("Set up watch on ", path)

        atexit.register(self.stop)

    def stop(self):
        if self.wdd[self.path] > 0:
            self.wm.rm_watch(self.wdd[self.path], rec=True)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("mach2.ini")

    watch = LibraryWatcher(config["DEFAULT"]["media_dir"])
