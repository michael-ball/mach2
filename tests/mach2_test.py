"""Tests for the mach2 app."""
import json
import random
import string
import unittest

import pytest
import six

from mach2 import create_app


@pytest.mark.usefixtures("app")
class Mach2TestCase(unittest.TestCase):
    """Provides tests for the mach2 app."""

    def setUp(self):
        """Set up the state before the tests run."""
        app = create_app(database=self.db, library=self.library_db)
        app.config["TESTING"] = True
        self.app = app.test_client()

    def login(self, username, password):
        """Log in to the app.

        Args:
            username (str): The username to log in with.
            password (str): The password to log in with.

        """
        return self.app.post("/login", data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        """Log out of the app."""
        return self.app.get("/logout", follow_redirects=True)

    def test_login(self):
        """Test logging in to the app."""
        rv = self.login("admin", "testpass")
        assert six.b("Log out") in rv.data
        self.logout()
        rv = self.login("wrong", "definitelywrong")
        assert six.b("Log out") not in rv.data
        self.logout()

    def test_album(self):
        """Test retrieving albums."""
        self.login("admin", "testpass")

        rv = self.app.get("/albums/1")
        assert six.b("Album 1") in rv.data

        self.logout()

    def test_artists(self):
        """Test retrieving artists."""
        self.login("admin", "testpass")
        rv = self.app.get("/artists")

        assert six.b("Artist 1") in rv.data
        assert six.b("Artist 2") in rv.data

        artists = json.loads(rv.data.decode("utf-8"))
        assert artists

        self.logout()

    def test_encoding_options(self):
        """Test setting encoding options."""
        self.login("admin", "testpass")

        transcode_string = "".join(
            random.choice(
                string.ascii_lowercase + string.digits) for _ in range(10))

        transcode_command = dict(transcode_command=transcode_string)

        put_response = self.app.put(
            "/user", data=json.dumps(transcode_command),
            content_type="application/json")

        assert put_response.status_code == 200

        get_response = self.app.get("/user")

        user = json.loads(get_response.data.decode("utf-8"))
        assert user["transcode_command"] == six.u(transcode_string)
