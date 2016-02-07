from common import utils


def test_make_where_clause():
    params_with_between = {"column": "BETWEEN"}

    assert utils.make_where_clause(params_with_between) == "WHERE column "\
        "BETWEEN :column1 AND :column2"


def test_update_clause_from_dict():
    test_data = {"name": "Flaf"}

    assert utils.update_clause_from_dict(test_data) == "SET name = :name"
