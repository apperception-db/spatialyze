from spatialyze.database import Database
from spatialyze.utils import ingest_road
import psycopg2
import os
import pytest


d1 = Database(psycopg2.connect(
    dbname="mobilitydb",
    user="docker",
    host="localhost",
    port=os.environ["AP_PORT_ROAD_1"],
    password="docker",
))
ingest_road(d1, "./data/scenic/road-network")

d2 = Database(psycopg2.connect(
    dbname="mobilitydb",
    user="docker",
    host="localhost",
    port=os.environ["AP_PORT_ROAD_2"],
    password="docker",
))
ingest_road(d2, "./data/scenic/road-network/boston-seaport")


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
def test_simple_ops(table, count):
    assert d1.execute(f"select count(*) from {table}") == [(count,)]
    assert d2.execute(f"select count(*) from {table}") == [(count,)]


@pytest.mark.parametrize("database", [d1, d2])
def test_location(database):
    assert database.execute("select location, count(*) from segmentpolygon group by location") == [('boston-seaport', 3072)]