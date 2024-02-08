import datetime

from mobilitydb import TFloatInst, TFloatSeq, TGeomPointInst, TGeomPointSeq
from postgis import Point
from psycopg2.sql import SQL, Literal

from ...database import Database
from ..types import Float3
from ..utils.prepare_trajectory import Trajectory
from .infer_heading import infer_heading


def insert_trajectory(
    database: "Database",
    trajectory: Trajectory,
    # road_types: "list[str]",
    # roadpolygon_list: "list[list[tuple[float, float]]]"
):
    (
        item_id,
        camera_id,
        object_type,
        postgres_timestamps,
        pairs,
        itemHeading_list,
    ) = trajectory

    points: list[tuple[Float3, datetime.datetime]] = []
    headings: list[tuple[float, datetime.datetime]] = []
    prevTimestamp: datetime.datetime | None = None
    prevPoint: Float3 | None = None
    tuples: list[tuple[Literal, Literal, Literal, Literal, Point, Literal, Literal]] = []
    for idx, timestamp, current_point, curItemHeading in zip(
        range(len(postgres_timestamps)),
        postgres_timestamps,
        pairs,
        itemHeading_list,
    ):
        # if prevTimestamp == timestamp:
        #     continue
        assert prevTimestamp != timestamp, (prevTimestamp, timestamp)

        # Construct trajectory
        points.append((current_point, timestamp))
        curItemHeading = infer_heading(curItemHeading, prevPoint, current_point)
        if curItemHeading is not None:
            headings.append((curItemHeading, timestamp))
        # roadTypes.append(f"{cur_road_type}@{timestamp}")
        # polygon_point = ', '.join(join(cur_point, ' ') for cur_point in list(
        #     zip(*cur_roadpolygon.exterior.coords.xy)))
        # roadPolygons.append(f"Polygon (({polygon_point}))@{timestamp}")
        tuples.append(
            (
                Literal(item_id),
                Literal(camera_id),
                Literal(object_type),
                Literal(idx),
                Point(*current_point),
                Literal(timestamp),
                Literal(curItemHeading),
            )
        )
        prevTimestamp = timestamp
        prevPoint = current_point

    tpoints = tgeoms(points)
    theadings = tfloats(headings) if len(headings) > 0 else None
    obj = item_id, camera_id, object_type, tpoints, theadings
    obj = SQL(",").join(map(Literal, obj))
    insert = SQL("INSERT INTO Item_Trajectory VALUES ({})")
    database.execute(insert.format(obj))
    database._commit()

    obj = SQL(",").join(map(lambda t: SQL("({})").format(SQL(",").join(t)), tuples))
    insert = SQL("INSERT INTO Item_Trajectory2 VALUES {}")
    database.execute(insert.format(obj))
    database._commit()


def tgeoms(points: list[tuple[Float3, datetime.datetime]]):
    return TGeomPointSeq(
        [TGeomPointInst(Point(*p), t) for p, t in points],
        upper_inc=True,
        lower_inc=True,
        interp="Linear",
    )


def tfloats(floats: list[tuple[float, datetime.datetime]]):
    return TFloatSeq(
        [TFloatInst(f, t) for f, t in floats],
        upper_inc=True,
        lower_inc=True,
        interp="Linear",
    )
