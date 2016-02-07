import json
import unittest

import pytest

from mach2 import create_app


@pytest.mark.usefixtures("app")
class Mach2TestCase(unittest.TestCase):

    def setUp(self):
        app = create_app(database=self.db, library=self.library_db)
        app.config['TESTING'] = True
        self.app = app.test_client()

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login(self):
        rv = self.login("admin", "testpass")
        assert bytes("Log out", "utf-8") in rv.data
        self.logout()
        rv = self.login("wrong", "definitelywrong")
        assert bytes("Log out", "utf-8") not in rv.data
        self.logout()

    def test_album(self):
        self.login("admin", "testpass")

        rv = self.app.get("/albums/1")
        assert bytes("Album 1", "utf-8") in rv.data

        self.logout()

    def test_artists(self):
        self.login("admin", "testpass")
        rv = self.app.get("/artists")

        assert bytes("Artist 1", "utf-8") in rv.data
        assert bytes("Artist 2", "utf-8") in rv.data

        artists = json.loads(rv.data.decode("utf-8"))
        assert artists

        self.logout()
