#!/usr/bin/env python
"""Runs mach2."""
from gevent import joinall, monkey, spawn
from gevent.pywsgi import WSGIServer
monkey.patch_all(thread=False)

from six.moves import configparser  # NOQA : E402

from mach2 import create_app  # NOQA : E402
from watcher import LibraryWatcher  # NOQA : E402

APP = create_app()


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("mach2.ini")

    http_server = WSGIServer(('', 5000), APP, log=None)
    server = spawn(http_server.serve_forever)

    watcher = LibraryWatcher(config.get("DEFAULT", "media_dir"),
                             config.get("DEFAULT", "library"))

    def check_for_events():
        """Check for changes in the library."""
        while True:
            watcher.check_for_events()

    watcher_routine = spawn(check_for_events)

    joinall([watcher_routine, server])
