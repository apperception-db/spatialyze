from spatialyze.database import Database
from spatialyze.utils import ingest_road
import duckdb
import os
import pytest


@pytest.mark.parametrize("table, count", [
    ("segmentpolygon", 3072),
    ("segment", 11410),
    ("lanesection", 1180),
    ("lane", 1180),
    ("lane_lanesection", 1180),
    ("lanegroup", 966),
    ("lanegroup_lane", 1180),
    ("opposite_lanegroup", 744),
    ("road", 926),
    ("road_lanegroup", 966),
    ("road_roadsection", 594),
    ("roadsection", 594),
    ("roadsection_lanesection", 1180),
    ("intersection", 332),
])
def test_simple_ops(table: str, count: int):
    dbfile = '/tmp/__spatialyze__road_1.duckdb'
    if os.path.exists(dbfile):
        os.remove(dbfile)
    with duckdb.connect(dbfile) as conn:
        d1 = Database(conn)
        d1.reset()
        ingest_road(d1, "./data/scenic/road-network/boston-seaport")
        assert d1.execute(f"select count(*) from {table}") == [(count,)]


def test_incomplete_road_network():
    dbfile = '/tmp/__spatialyze__road_2.duckdb'
    if os.path.exists(dbfile):
        os.remove(dbfile)
    with duckdb.connect(dbfile) as conn:
        d2 = Database(conn)
        ingest_road(d2, "./data/viva/road-network")

        assert d2.execute("select count(*) from lane") == [(8,)]
        assert d2.execute("select count(*) from intersection") == [(1,)]
        assert d2.execute("select count(*) from segmentpolygon") == [(9,)]
