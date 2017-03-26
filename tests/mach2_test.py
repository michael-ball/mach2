import json
import unittest

import pytest
import six

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
        assert six.b("Log out") in rv.data
        self.logout()
        rv = self.login("wrong", "definitelywrong")
        assert six.b("Log out") not in rv.data
        self.logout()

    def test_album(self):
        self.login("admin", "testpass")

        rv = self.app.get("/albums/1")
        assert six.b("Album 1") in rv.data

        self.logout()

    def test_artists(self):
        self.login("admin", "testpass")
        rv = self.app.get("/artists")

        assert six.b("Artist 1") in rv.data
        assert six.b("Artist 2") in rv.data

        artists = json.loads(rv.data.decode("utf-8"))
        assert artists

        self.logout()
