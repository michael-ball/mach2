def make_where_clause(params, join_operator="AND"):
    """Create a where clause from the param.

    Args:
        params : A dict where key is the column and the value a comparison
            operator
        join_operator: string to join comparisons. Should be "AND" or "OR"
    """

    where_items = []
    where_clause = None

    try:
        for (column, operator) in params.items():
            condition_subphrase = ""

            if operator == "BETWEEN":
                condition_subphrase = " ".join(("%s", operator,
                                                ":%s1 AND :%s2"))

                where_items.append(condition_subphrase % (column, column,
                                                          column))
            else:
                condition_subphrase = " ".join(("%s", operator, ":%s"))

                where_items.append(condition_subphrase % (column, column))

        where_statement = None
        if len(where_items) > 1:
            # surround join operator with spaces
            join_string = "".join((" ", join_operator, " "))
            where_statement = join_string.join(where_items)
        else:
            where_statement = where_items[0]

        where_clause = " ".join(("WHERE", where_statement))
    except AttributeError:
        pass

    return where_clause


def update_clause_from_dict(data):
    """Create an update clause

    Args:
        data: A dict of the new value and the column name as key
    """

    update_items = []
    set_statement = None
    update_clause = None

    try:
        for key in data.keys():
            update_items.append("%s = :%s" % (key, key))

        if len(update_items) > 1:
            update_clause = ", ".join(update_items)
        else:
            update_clause = update_items[0]

        set_statement = " ".join(("SET", update_clause))
    except AttributeError:
        pass

    return set_statement
