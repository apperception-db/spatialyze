from spatialyze.database import Database
from spatialyze.utils.ingest_road import ingest_road, ROAD_TYPES
import duckdb
import os
import pytest
import json


@pytest.mark.parametrize("table, count", [
    ("segmentpolygon", 3072),
    ("segment", 11410),
    # ("lanesection", 1180),
    ("lane", 1180),
    # ("lane_lanesection", 1180),
    ("lanegroup", 966),
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


def test_full_road_network():
    dbfile = '/tmp/__spatialyze__road_3.duckdb'
    if os.path.exists(dbfile):
        os.remove(dbfile)
    with duckdb.connect(dbfile) as conn:
        d3 = Database(conn)
        d3.reset()
        ingest_road(d3, "./data/scenic/road-network/boston-seaport")

        roadtypes = sorted(ROAD_TYPES)
        name_idx_columns = [
            ("segmentpolygon", "elementId", "elementId, ST_AsText(ST_ReducePrecision(elementPolygon, 0.0001)), location, segmentTypes " + ", ".join(f"__RoadType__{rt}__" for rt in roadtypes)),
            ("segment", "segmentId", "segmentId, elementId, ST_AsText(ST_ReducePrecision(startPoint, 0.0001)), ST_AsText(ST_ReducePrecision(endPoint, 0.0001)), ST_AsText(ST_ReducePrecision(segmentLine, 0.0001)), heading"),
            ("lane", "id", "id"),
            ("lanegroup", "id", "id"),
            ("lanesection", "id", "id, laneToLeft, laneToRight, fasterLane, slowerLane isForward"),
            ("road", "id", "id, forwardLane, backwardLane"),
            ("roadsection", "id", "id, forwardLanes, backwardLanes"),
            ("intersection", "id", "id, road"),
        ]

        DIR = "./data/scenic/road-network-test-output"
        if not os.path.exists(DIR):
            os.makedirs(DIR)

        for name, idx, columns in name_idx_columns:
            res = d3.execute(f"select {columns} from {name} order by {idx}")
            print("types", [type(elm) for elm in res[0]])
            res = [
                [elm.hex() if isinstance(elm, bytes) else elm for elm in row]
                for row in res
            ]
            filename = os.path.join(DIR, f"{name}.jsonl")
            if os.environ.get('GENERATE_ENGINE_TEST_RESULTS', False):
                with open(filename, "w") as f:
                    for r in res:
                        f.write(json.dumps(r) + "\n")
            
            with open(filename, "r") as f:
                expected = [json.loads(line) for line in f.readlines()]
                assert res == expected
