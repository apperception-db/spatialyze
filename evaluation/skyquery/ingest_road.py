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

CREATE_LANE_SQL = """
CREATE TABLE IF NOT EXISTS Lane(
    id Text,
    PRIMARY KEY (id),
    FOREIGN KEY(id)
        REFERENCES SegmentPolygon(elementId)
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
        "lane",
        "segmentpolygon",
    ]

    for tablename in tablenames:
        database.update(f'DROP TABLE IF EXISTS "{tablename}" CASCADE;', commit=True)


def index_factory(database: "Database"):
    def index(table: "str", field: "str", gist: "bool" = False, commit: "bool" = False):
        name = f"{table}__{field}__idx"
        use_gist = " USING GiST" if gist else ""
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

    database.update(CREATE_LANE_SQL, commit=False)
    index("Lane", "id")

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


ROAD_TYPES = {"lane"}


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
            SET segmentTypes = ARRAY_APPEND(segmentTypes, '{road_type}')
            WHERE elementId IN (SELECT id FROM {road_type});"""
        )
        # print("added type:", road_type)

    for road_type in road_types:
        index("SegmentPolygon", f"__RoadType__{road_type}__")
        # print("index created:", road_type)
    database._commit()


INSERT: "dict[str, Callable[[Database, list[dict]], None]]" = {
    # primitives
    "polygon": insert_polygon,
    # basics
    "lane": insert_lane,
}


def ingest_location(database: "Database", directory: "str", location: "str"):
    # print("Location:", location)
    filenames = os.listdir(directory)

    assert set(filenames) == set([k + ".json" for k in INSERT.keys()]), (
        sorted(filenames),
        sorted([k + ".json" for k in INSERT.keys()]),
    )

    for d, fn in INSERT.items():
        with open(os.path.join(directory, d + ".json"), "r") as f:
            data = json.load(f)

        # print("Ingesting", d)
        fn(database, [{"location": location, **d} for d in data])


def ingest_road(database: "Database", directory: str):
    drop_tables(database)
    create_tables(database)

    filenames = os.listdir(directory)

    if all(os.path.isdir(os.path.join(directory, f)) for f in filenames):
        for d in filenames:
            if d == "boston-old":
                continue

            # print(d)
            ingest_location(database, os.path.join(directory, d), d)
    else:
        assert all(os.path.isfile(os.path.join(directory, f)) for f in filenames)
        ingest_location(database, directory, "boston-seaport")

    # print("adding segment types")
    add_segment_type(database, ROAD_TYPES)

    database.reset()


if __name__ == "__main__":
    import sys

    from spatialyze.database import database

    ingest_road(database, sys.argv[1])
