def make_where_clause(params):
    """Create a where clause for each key-value pair in a dict, joined
       by AND.

    Parameters
    ----------
    params : dict
        A dict of keys and values
    """

    where_items = []
    where_clause = None

    try:
        for key in params.keys():
            where_items.append("%s=:%s" % (key, key))

        where_statement = None
        if len(where_items) > 1:
            where_statement = " AND ".join(where_items)
        else:
            where_statement = where_items[0]

        where_clause = " ".join(("WHERE", where_statement))
    except AttributeError:
        pass

    return where_clause


def update_clause_from_dict(data):
    """Create an update clause from a dictionary

    Parameters
    __________
    data: dict
        A dict of the new value and the column name as key
    """

    update_items = []
    set_statement = None
    update_clause = None

    try:
        for key in data.keys():
            update_items.append("%s = :%s", (key, key))

        if len(update_items) > 1:
            update_clause = ", ".join(update_items)
        else:
            update_clause = update_items[0]

        set_statement = " ".join(("SET", update_clause))
    except AttributeError:
        pass

    return set_statement
