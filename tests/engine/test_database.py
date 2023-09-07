import pickle

from spatialyze.database import Database
import psycopg2
import psycopg2.errors
import os
import pytest

TABLES = [
    ("Cameras", 1),
    # "General_Bbox",
    ("Item_General_Trajectory", 1),
]


def test_reset():
    d = Database(psycopg2.connect(
        dbname="mobilitydb",
        user="docker",
        host="localhost",
        port=os.environ["AP_PORT_RESET"],
        password="docker",
    ))

    with open('./data/nuscenes/processed/cameras.pkl', 'rb') as f:
        cameras = pickle.load(f)
    with open('./data/nuscenes/processed/annotations.pkl', 'rb') as f:
        annotaions = pickle.load(f)
    key = [cameras.keys()][0]
    d.load_nuscenes(
        {key: annotaions[key]},
        {key: cameras[key]},
    )

    for t, c in TABLES:
        assert d.sql(f"select count(*) from {t}")[0][0] == c

    d.reset()
    for t, _ in TABLES:
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
