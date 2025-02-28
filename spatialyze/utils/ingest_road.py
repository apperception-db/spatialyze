import json
import os
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from spatialyze.database import Database


# TODO: use ..data_types.table.Table to define tables and insert items

CREATE_POLYGON_SQL = """
CREATE TABLE IF NOT EXISTS SegmentPolygon(
    elementId TEXT,
    elementPolygon geometry,
    location TEXT,
    PRIMARY KEY (elementId)
);
"""

CREATE_SEGMENT_SQL = """
CREATE SEQUENCE seq_segmentId START 1;
CREATE TABLE IF NOT EXISTS Segment(
    segmentId INT,
    elementId TEXT,
    startPoint geometry,
    endPoint geometry,
    segmentLine geometry,
    heading real,
    PRIMARY KEY (segmentId)
);
"""

CREATE_LANESECTION_SQL = """
CREATE TABLE IF NOT EXISTS LaneSection(
    id Text,
    laneToLeft Text,
    laneToRight Text,
    fasterLane Text,
    slowerLane Text,
    isForward boolean,
    PRIMARY KEY (id)
);
"""

CREATE_LANE_SQL = """
CREATE TABLE IF NOT EXISTS Lane(
    id Text,
    PRIMARY KEY (id)
);
"""

CREATE_LANE_LANESEC_SQL = """
CREATE TABLE IF NOT EXISTS Lane_LaneSection(
    laneId TEXT,
    laneSectionId TEXT,
    FOREIGN KEY (laneId)
        REFERENCES Lane (id),
    FOREIGN KEY (laneSectionId)
        REFERENCES LaneSection (id)
);
"""

CREATE_LANEGROUP_SQL = """
CREATE TABLE IF NOT EXISTS LaneGroup(
    id Text,
    PRIMARY KEY (id)
);
"""

CREATE_LANEGROUP_LANE_SQL = """
CREATE TABLE IF NOT EXISTS LaneGroup_Lane(
    laneGroupId TEXT,
    laneId TEXT,
    FOREIGN KEY (laneGroupId)
        REFERENCES LaneGroup (id),
    FOREIGN KEY (laneId)
        REFERENCES Lane (id)
);
"""

CREATE_OPPOSITE_LANEGROUP_SQL = """
CREATE TABLE IF NOT EXISTS Opposite_LaneGroup(
    laneGroupId TEXT,
    oppositeId TEXT,
    FOREIGN KEY (laneGroupId)
        REFERENCES LaneGroup (id),
    FOREIGN KEY (oppositeId)
        REFERENCES LaneGroup (id)
);
"""

CREATE_ROAD_SQL = """
CREATE TABLE IF NOT EXISTS Road(
    id Text,
    forwardLane Text,
    backwardLane Text,
    PRIMARY KEY (id)
);
"""

CREATE_ROAD_LANEGROUP_SQL = """
CREATE TABLE IF NOT EXISTS Road_LaneGroup(
    roadId TEXT,
    laneGroupId TEXT,
    FOREIGN KEY (roadId)
        REFERENCES Road (id),
    FOREIGN KEY (laneGroupId)
        REFERENCES LaneGroup (id)
);
"""

CREATE_ROAD_ROADSECTION_SQL = """
CREATE TABLE IF NOT EXISTS Road_RoadSection(
    roadId TEXT,
    roadSectionId TEXT,
    FOREIGN KEY (roadId)
        REFERENCES Road (id),
    FOREIGN KEY (roadSectionId)
        REFERENCES RoadSection (id)
);
"""

CREATE_ROADSECTION_SQL = """
CREATE TABLE IF NOT EXISTS RoadSection(
    id TEXT,
    forwardLanes text[],
    backwardLanes text[],
    PRIMARY KEY (id)
);
"""

CREATE_ROADSEC_LANESEC_SQL = """
CREATE TABLE IF NOT EXISTS RoadSection_LaneSection(
    roadSectionId TEXT,
    laneSectionId TEXT,
    FOREIGN KEY (roadSectionId)
        REFERENCES RoadSection (id),
    FOREIGN KEY (laneSectionId)
        REFERENCES LaneSection (id)
);
"""

CREATE_INTERSECTION_SQL = """
CREATE TABLE IF NOT EXISTS Intersection(
    id TEXT,
    road TEXT,
    PRIMARY KEY (id)
);
"""


def _remove_suffix(uid: str) -> "str | None":
    if uid is None:
        return None

    split = uid.split("_")
    assert len(split) == 2, f"cannot remove suffix: {uid}"
    return split[0]


def drop_tables(database: "Database"):
    tablenames = [
        "segment",
        "lane_lanesection",
        "roadsection_lanesection",
        "lanegroup_lane",
        "opposite_lanegroup",
        "road_lanegroup",
        "road_roadsection",
        "lanesection",
        "lane",
        "lanegroup",
        "road",
        "roadsection",
        "intersection",
        "segmentpolygon",
    ]
    for tablename in tablenames:
        database.update(f'DROP TABLE IF EXISTS "{tablename}" CASCADE;', commit=True)
    
    database.update('DROP SEQUENCE IF EXISTS seq_segmentId CASCADE;', commit=True)


def index_factory(database: "Database"):
    def index(table: "str", field: "str", gist: "bool" = False, commit: "bool" = False):
        name = f"{table}__{field}__idx"
        use_gist = " USING RTREE" if gist else ""
        database.update(
            f"CREATE INDEX IF NOT EXISTS {name} ON {table}{use_gist}({field});", commit=commit
        )

    return index


def create_tables(database: "Database"):
    index = index_factory(database)

    database.update(CREATE_POLYGON_SQL, commit=False)
    index("SegmentPolygon", "elementId")
    index("SegmentPolygon", "location")
    index("SegmentPolygon", "elementPolygon", gist=True)

    database.update(CREATE_SEGMENT_SQL, commit=False)
    index("Segment", "elementId")
    index("Segment", "startPoint")
    index("Segment", "endPoint")
    index("Segment", "segmentLine")
    index("Segment", "heading")

    database.update(CREATE_LANE_SQL, commit=False)
    index("Lane", "id")

    database.update(CREATE_ROAD_SQL, commit=False)
    index("Road", "id")

    database.update(CREATE_INTERSECTION_SQL, commit=False)
    index("Intersection", "id")

    database.update(CREATE_LANESECTION_SQL, commit=False)
    index("LaneSection", "id")

    database.update(CREATE_ROADSECTION_SQL, commit=False)
    index("RoadSection", "id")

    database.update(CREATE_LANEGROUP_SQL, commit=False)
    index("LaneGroup", "id")

    database.update(CREATE_LANE_LANESEC_SQL, commit=False)
    index("Lane_LaneSection", "laneId")
    index("Lane_LaneSection", "laneSectionId")

    database.update(CREATE_LANEGROUP_LANE_SQL, commit=False)
    index("LaneGroup_Lane", "laneId")
    index("LaneGroup_Lane", "laneGroupId")

    database.update(CREATE_OPPOSITE_LANEGROUP_SQL, commit=False)
    index("Opposite_LaneGroup", "oppositeId")
    index("Opposite_LaneGroup", "laneGroupId")

    database.update(CREATE_ROAD_LANEGROUP_SQL, commit=False)
    index("Road_LaneGroup", "roadId")
    index("Road_LaneGroup", "laneGroupId")

    database.update(CREATE_ROAD_ROADSECTION_SQL, commit=False)
    index("Road_RoadSection", "roadId")
    index("Road_RoadSection", "roadSectionId")

    database.update(CREATE_ROADSEC_LANESEC_SQL, commit=False)
    index("RoadSection_LaneSection", "laneSectionId")
    index("RoadSection_LaneSection", "roadSectionId")

    database._commit()


def insert_polygon(database: "Database", polygons: "list[dict]"):
    ids = set([p["id"].split("_")[0] for p in polygons if len(p["id"].split("_")) == 1])

    values = []
    for poly in polygons:
        i = poly["id"]
        if len(i.split("_")) != 1:
            assert i.split("_")[0] in ids
            continue
        values.append(
            f"""(
                '{poly['id']}',
                '{poly['polygon']}',
                '{poly['location']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO SegmentPolygon (
                elementId,
                elementPolygon,
                location
            )
            VALUES {','.join(values)};
            """
        )


def insert_segment(database: "Database", segments: "list[dict]"):
    ids = set(
        [s["polygonId"].split("_")[0] for s in segments if len(s["polygonId"].split("_")) == 1]
    )

    values = []
    for seg in segments:
        i = seg["polygonId"]
        if len(i.split("_")) != 1:
            assert i.split("_")[0] in ids
            continue
        values.append(
            f"""(
                nextval('seq_segmentId'),
                '{seg['polygonId']}',
                '{seg['start']}',
                '{seg['end']}',
                '{seg['heading']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Segment (
                segmentId,
                elementId,
                startPoint,
                endPoint,
                heading
            )
            VALUES {','.join(values)};
            """
        )
    database.update(
        """
    UPDATE Segment
    SET segmentLine = ST_MakeLine(startPoint, endPoint)
    WHERE startPoint IS NOT NULL and endPoint IS NOT NULL;
    """
    )

    index_factory(database)("Segment", "segmentLine", gist=True)


def insert_lanesection(database: "Database", laneSections: "list[dict]"):
    values = []
    for lanesec in laneSections:
        values.append(
            f"""(
                '{_remove_suffix(lanesec['id'])}',
                '{_remove_suffix(lanesec['laneToLeft'])}',
                '{_remove_suffix(lanesec['laneToRight'])}',
                '{lanesec['fasterLane']}',
                '{lanesec['slowerLane']}',
                '{lanesec['isForward']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO LaneSection (
                id,
                laneToLeft,
                laneToRight,
                fasterLane,
                slowerLane,
                isForward
            )
            VALUES {','.join(values)};
            """
        )


def insert_lane(database: "Database", lanes: "list[dict]"):
    values = []
    for lane in lanes:
        values.append(
            f"""(
                '{lane['id']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Lane (
                id
            )
            VALUES {','.join(values)};
            """
        )


def insert_lane_lanesec(database: "Database", lane_lanesec: "list[dict]"):
    values = []
    for ll in lane_lanesec:
        values.append(
            f"""(
                '{ll['lane']}',
                '{_remove_suffix(ll['laneSec'])}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Lane_LaneSection (
                laneId,
                laneSectionId
            )
            VALUES {','.join(values)};
            """
        )


def insert_lanegroup(database: "Database", laneGroups: "list[dict]"):
    values = []
    for lg in laneGroups:
        values.append(f"('{lg['id']}')")

    if len(values):
        database.update(
            f"""
            INSERT INTO LaneGroup (id)
            VALUES {','.join(values)};
            """
        )


def insert_lanegroup_lane(database: "Database", lanegroup_lane: "list[dict]"):
    values = []
    for ll in lanegroup_lane:
        values.append(
            f"""(
                '{ll['laneGroup']}',
                '{ll['lane']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO LaneGroup_Lane (
                laneGroupId,
                laneId
            )
            VALUES {','.join(values)};
            """
        )


def insert_opposite_lanegroup(database: "Database", opposite_lanegroup: "list[dict]"):
    values = []
    for oppo in opposite_lanegroup:
        values.append(
            f"""(
                '{oppo['lane']}',
                '{oppo['opposite']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Opposite_LaneGroup (
                laneGroupId,
                oppositeId
            )
            VALUES {','.join(values)};
            """
        )


def insert_road(database: "Database", roads: "list[dict]"):
    values = []
    for road in roads:
        values.append(
            f"""(
                '{road['id']}',
                '{road['forwardLanes']}',
                '{road['backwardLanes']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Road (
                id,
                forwardLane,
                backwardLane
            )
            VALUES {','.join(values)};
            """
        )


def insert_road_lanegroup(database: "Database", road_lanegroup: "list[dict]"):
    values = []
    for rl in road_lanegroup:
        values.append(
            f"""(
                '{rl['road']}',
                '{rl['laneGroup']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Road_LaneGroup (
                roadId,
                laneGroupId
            )
            VALUES {','.join(values)};
            """
        )


def insert_road_roadsec(database: "Database", road_roadsec: "list[dict]"):
    values = []
    for rr in road_roadsec:
        values.append(
            f"""(
                '{rr['road']}',
                '{_remove_suffix(rr['roadSec'])}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Road_RoadSection (
                roadId,
                roadSectionId
            )
            VALUES {','.join(values)};
            """
        )


def insert_roadsection(database: "Database", roadSections: "list[dict]"):
    values = []
    for roadsec in roadSections:
        fl = f"{[*map(_remove_suffix, roadsec['forwardLanes'])]}::text[]"
        bl = f"{[*map(_remove_suffix, roadsec['backwardLanes'])]}::text[]"

        values.append(
            f"""(
                '{_remove_suffix(roadsec['id'])}',
                ARRAY{fl},
                ARRAY{bl}
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO RoadSection (
                id,
                forwardLanes,
                backwardLanes
            )
            VALUES {','.join(values)};
            """
        )


def insert_roadsec_lanesec(database: "Database", roadsec_lanesec: "list[dict]"):
    values = []
    for rl in roadsec_lanesec:
        values.append(
            f"""(
                '{_remove_suffix(rl['roadSec'])}',
                '{_remove_suffix(rl['laneSec'])}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO RoadSection_LaneSection (
                roadSectionId,
                laneSectionId
            )
            VALUES {','.join(values)};
            """
        )


def insert_intersection(database: "Database", intersections: "list[dict]"):
    values = []
    for intersec in intersections:
        values.append(
            f"""(
                '{_remove_suffix(intersec['id'])}',
                '{intersec['road']}'
            )"""
        )

    if len(values):
        database.update(
            f"""
            INSERT INTO Intersection (
                id,
                road
            )
            VALUES {','.join(values)};
            """
        )


ROAD_TYPES = {"road", "lane", "lanesection", "roadsection", "intersection", "lanegroup"}


def add_segment_type(database: "Database", road_types: "set[str]"):
    index = index_factory(database)

    database.update("ALTER TABLE SegmentPolygon ADD segmentTypes text[];")
    # print("altered table")

    for road_type in road_types:
        database.update(f"ALTER TABLE SegmentPolygon ADD __RoadType__{road_type}__ boolean;")
        database.update(
            f"""UPDATE SegmentPolygon
            SET __RoadType__{road_type}__ = EXISTS(
                SELECT * from {road_type}
                WHERE {road_type}.id = SegmentPolygon.elementId
            )"""
        )
        database.update(
            f"""UPDATE SegmentPolygon
            SET segmentTypes = LIST_APPEND(segmentTypes, '{road_type}')
            WHERE EXISTS (SELECT * FROM {road_type} WHERE id = elementId);"""
        )
        # print("added type:", road_type)

    for road_type in road_types:
        index("SegmentPolygon", f"__RoadType__{road_type}__")
        # print("index created:", road_type)
    database._commit()


INSERT: "dict[str, Callable[[Database, list[dict]], None]]" = {
    # primitives
    "polygon": insert_polygon,
    "segment": insert_segment,
    # basics
    "lane": insert_lane,
    "road": insert_road,
    "laneGroup": insert_lanegroup,
    # sections
    "laneSection": insert_lanesection,
    "roadSection": insert_roadsection,
    "intersection": insert_intersection,
    # relations
    "lane_LaneSec": insert_lane_lanesec,
    "laneGroup_Lane": insert_lanegroup_lane,
    "laneGroup_opposite": insert_opposite_lanegroup,
    "road_laneGroup": insert_road_lanegroup,
    "road_roadSec": insert_road_roadsec,
    "roadSec_laneSec": insert_roadsec_lanesec,
}


def ingest_location(database: "Database", directory: "str", location: "str"):
    # print("Location:", location)
    filenames = os.listdir(directory)

    assert set(filenames) <= set([k + ".json" for k in INSERT.keys()]), (
        sorted(filenames),
        sorted([k + ".json" for k in INSERT.keys()]),
    )

    for d, fn in INSERT.items():
        try:
            with open(os.path.join(directory, d + ".json"), "r") as f:
                data = json.load(f)

            # print("Ingesting", d)
            fn(database, [{"location": location, **d} for d in data])
        except FileNotFoundError:
            print("File not found:", d)


def ingest_road(database: "Database", directory: str):
    drop_tables(database)
    create_tables(database)

    filenames = os.listdir(directory)
    assert all(os.path.isfile(os.path.join(directory, f)) for f in filenames)
    ingest_location(database, directory, "boston-seaport")

    # print("adding segment types")
    add_segment_type(database, ROAD_TYPES)

    # database.reset()
