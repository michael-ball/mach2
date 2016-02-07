import os

import pytest

from db.db_manager import DbManager


@pytest.fixture(scope="module")
def database(request):
    database = DbManager(
        db=os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "test.db"))

    def fin():
        database.close()

    request.addfinalizer(fin)

    return database


@pytest.fixture(scope="module")
def test_file():
    test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "test.ogg")

    return test_file


@pytest.fixture(scope="class")
def app(request):
    db = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                      "testapp.db")
    library_db = DbManager(
        db=os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "test.db"))

    def fin():
        library_db.close()

    request.addfinalizer(fin)

    request.cls.db = db
    request.cls.library_db = library_db
