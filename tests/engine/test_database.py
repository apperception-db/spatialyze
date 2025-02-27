import pickle

from spatialyze.database import Database, CAMERA_TABLE, TRAJECTORY_TABLE
import duckdb
import os
import pytest

TABLES = [
    (CAMERA_TABLE, 229),
    # "General_Bbox",
    (TRAJECTORY_TABLE, 3934),
]


def test_reset():
    with duckdb.connect('/tmp/reset.duckdb') as conn:
        d = Database(conn)

        with open('./data/nuscenes/processed/cameras.pkl', 'rb') as f:
            cameras = pickle.load(f)
        with open('./data/nuscenes/processed/annotations.pkl', 'rb') as f:
            annotations = pickle.load(f)
        key = [k for k in cameras if k.scene == "scene-0103" and k.channel == 'CAM_FRONT'][0]
        d.reset(commit=True)
        d.load_nuscenes(
            {key: annotations[key]},
            {key: cameras[key]},
        )

        for t, c in TABLES:
            assert d.execute(f"select count(*) from {t}")[0][0] == c

        d.reset()
        for t, _ in TABLES:
            assert d.sql("select * from " + t).empty


def test_execute_update_and_query():
    with duckdb.connect('/tmp/sql.duckdb') as conn:
        d = Database(conn)

        d.update("create table if not exists t1 (c1 text, c2 int)")
        d.update("insert into t1 values ('test1', 3), ('test2', 4)")
        d._commit()
        results = d.execute("select * from t1")
        assert results == [("test1", 3), ("test2", 4)], "should return correct tuples"

        with pytest.raises(duckdb.DataError):
            d.update("zxcvasdfqwer")

        results = d.execute("select * from t1")
        assert results == [("test1", 3), ("test2", 4)], "should execute another query after failed executions"

        with pytest.raises(duckdb.DataError):
            d.execute("zxcvasdfqwer")

        results = d.execute("select * from t1")
        assert results == [("test1", 3), ("test2", 4)], "should execute another query after failed executions"
