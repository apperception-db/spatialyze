from spatialyze.database import Database
from spatialyze.utils import import_tables
import psycopg2
import os
import pytest

TABLE_NAMES = [
    "Cameras",
    # "General_Bbox",
    "Item_General_Trajectory",
]


def test_reset():
    d = Database(psycopg2.connect(
        dbname="mobilitydb",
        user="docker",
        host="localhost",
        port=os.environ["AP_PORT_RESET"],
        password="docker",
    ))

    import_tables(d, './data/scenic/database')
    for t in TABLE_NAMES:
        assert not d.sql(f"select * from {t} limit 1").empty

    d.reset()
    for t in TABLE_NAMES:
        assert d.sql("select * from " + t).empty


def test_execute_update_and_query():
    d = Database(psycopg2.connect(
        dbname="mobilitydb",
        user="docker",
        host="localhost",
        port=os.environ["AP_PORT_SQL"],
        password="docker",
    ))

    d.update("create table if not exists t1 (c1 text, c2 int)")
    d.update("insert into t1 values ('test1', 3), ('test2', 4)")
    d._commit()
    results = d.execute("select * from t1")
    assert results == [("test1", 3), ("test2", 4)], "should return correct tuples"

    with pytest.raises(psycopg2.errors.DatabaseError):
        d.update("zxcvasdfqwer")

    results = d.execute("select * from t1")
    assert results == [("test1", 3), ("test2", 4)], "should execute another query after failed executions"

    with pytest.raises(psycopg2.errors.DatabaseError):
        d.execute("zxcvasdfqwer")

    results = d.execute("select * from t1")
    assert results == [("test1", 3), ("test2", 4)], "should execute another query after failed executions"
