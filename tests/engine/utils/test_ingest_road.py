from spatialyze.database import Database
from spatialyze.utils import ingest_road
import psycopg2
import os
import pytest
import json


@pytest.mark.parametrize("table, count", [
    ("segmentpolygon", 3072),
    ("segment", 11410),
    # ("lanesection", 1180),
    ("lane", 1180),
    # ("lane_lanesection", 1180),
    # ("lanegroup", 966),
    # ("lanegroup_lane", 1180),
    # ("opposite_lanegroup", 744),
    ("road", 926),
    # ("road_lanegroup", 966),
    # ("road_roadsection", 594),
    ("roadsection", 594),
    # ("roadsection_lanesection", 1180),
    ("intersection", 332),
])
def test_simple_ops(table: str, count: int):
    d1 = Database(psycopg2.connect(
        dbname="postgres",
        user="postgres",
        host="localhost",
        port=os.environ["AP_PORT_ROAD_1"],
        password="postgres",
    ))
    d1.reset()
    ingest_road(d1, "./data/scenic/road-network/boston-seaport")
    assert d1.execute(f"select count(*) from {table}") == [(count,)]


def test_incomplete_road_network():
    d2 = Database(psycopg2.connect(
        dbname="postgres",
        user="postgres",
        host="localhost",
        port=os.environ["AP_PORT_ROAD_2"],
        password="postgres",
    ))
    ingest_road(d2, "./data/viva/road-network")

    assert d2.execute("select count(*) from lane") == [(8,)]
    assert d2.execute("select count(*) from intersection") == [(1,)]
    assert d2.execute("select count(*) from segmentpolygon") == [(9,)]


def test_full_road_network():
    d1 = Database(psycopg2.connect(
        dbname="postgres",
        user="postgres",
        host="localhost",
        port=os.environ["AP_PORT_ROAD_1"],
        password="postgres",
    ))
    d1.reset()
    ingest_road(d1, "./data/scenic/road-network/boston-seaport")

    name_idx_columns = [
        ("segmentpolygon", "elementId", "elementId, ST_AsHexWKB(elementPolygon), location"),
        ("segment", "segmentId", "segmentId, elementId, ST_AsHexWKB(startPoint), ST_AsHexWKB(endPoint), ST_AsHexWKB(segmentLine), heading"),
        ("lane", "id", "id"),
        ("road", "id", "id, forwardLane, backwardLane"),
        ("roadsection", "id", "id, forwardLanes, backwardLanes"),
        ("intersection", "id", "id, road"),
    ]

    for name, idx, columns in name_idx_columns:
        res = d1.execute(f"select {columns} from {name} order by {idx}")
        filename = f"./data/scenic/road-network-export/{name}.jsonl"
        if os.environ.get('GENERATE_ENGINE_TEST_RESULTS', False):
            with open(filename, "w") as f:
                for r in res:
                    f.write(json.dumps(r) + "\n")
        
        with open(filename, "r") as f:
            expected = f.readlines()
            assert len(res) == len(expected)