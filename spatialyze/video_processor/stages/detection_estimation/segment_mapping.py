""" Goal to map the road segment to the frame segment
    Now only get the segment of type lane and intersection
    except for the segment that contains the ego camera

Usage example:
    from optimization_playground.segment_mapping import map_imgsegment_roadsegment
    from spatialyze.utils import fetch_camera_config

    test_config = fetch_camera_config(test_img, database)
    mapping = map_imgsegment_roadsegment(test_config)
"""

import array
import logging
import math
import time
from typing import NamedTuple, Tuple

import numpy as np
import postgis
import psycopg2.sql as sql
import shapely.geometry as sg
import shapely.wkb as swkb

from ....database import database
from ...camera_config import CameraConfig
from ...types import DetectionId, obj_detection
from .utils import ROAD_TYPES, Float22

logger = logging.getLogger(__name__)


SQL_ROAD_TYPES = ",".join("__RoadType__" + rt + "__" for rt in ROAD_TYPES)


MAX_POLYGON_CONTAIN_QUERY = sql.SQL(
    f"""
    WITH
    AvailablePolygon AS (
        SELECT *
        FROM SegmentPolygon as p
        WHERE
            p.location = {{location}}
            AND ST_Contains(
                p.elementpolygon,
                {{ego_translation}}::geometry
            )
    ),
    max_contain AS (
        SELECT MAX(ST_Area(elementpolygon)) max_segment_area
        FROM AvailablePolygon
    )
    SELECT
        p.elementid,
        p.elementpolygon::geometry,
        ARRAY_AGG(s.segmentline)::geometry[],
        ARRAY_AGG(s.heading)::real[],
        {SQL_ROAD_TYPES}
    FROM max_contain, AvailablePolygon AS p
        LEFT OUTER JOIN segment AS s USING (elementid)
    WHERE ST_Area(p.elementpolygon) = max_contain.max_segment_area
    GROUP BY p.elementid, p.elementpolygon, {SQL_ROAD_TYPES};"""
)

USEFUL_TYPES = ["lane", "lanegroup", "intersection"]


class RoadPolygonInfo(NamedTuple):
    """
    id: unique polygon id
    polygon: tuple of (x, y) coordinates
    segment_line: list of tuple of (x, y) coordinates
    segment_type: road segment type
    segment_headings: list of floats
    contains_ego: whether the segment contains ego camera
    ego_config: ego camfig for the frame we asks info for
    fov_lines: field of view lines
    """

    id: str
    polygon: "sg.Polygon"
    segment_lines: "list[sg.LineString]"
    road_type: str
    segment_headings: "list[float]"
    contains_ego: bool
    ego_config: "CameraConfig"
    fov_lines: "tuple[Float22, Float22]"


class RoadSegmentWithHeading(NamedTuple):
    id: "str"
    polygon: "postgis.Polygon"
    road_types: "list[str]"
    segmentline: "list[sg.LineString]"
    heading: "list[float]"


class Segment(NamedTuple):
    id: "str"
    polygon: "postgis.Polygon"
    road_type: "str"
    segmentline: "list[sg.LineString]"
    heading: "list[float]"


def reformat_return_polygon(segments: "list[RoadSegmentWithHeading]") -> "list[Segment]":
    def _(x: "RoadSegmentWithHeading") -> "Segment":
        i, polygon, types, lines, headings = x
        type = types[-1]
        for t in types:
            if t in USEFUL_TYPES:
                type = t
                break
        return Segment(
            i,
            polygon,
            type,
            lines,
            [*map(math.degrees, headings)],
        )

    return list(map(_, segments))


def intersection(fov_line: Tuple[Float22, Float22], segmentpolygon: "sg.Polygon"):
    """
    return: intersection point: tuple[tuple]
    """
    left_fov_line, right_fov_line = fov_line
    # left_intersection = line_to_polygon_intersection(segmentpolygon, left_fov_line)
    # right_intersection = line_to_polygon_intersection(segmentpolygon, right_fov_line)
    # return left_intersection + right_intersection
    return []


def is_roadsection(segmenttypes: "list[int]"):
    for t, v in zip(ROAD_TYPES, segmenttypes):
        if t == "roadsection" and v:
            return True
    return False


def get_largest_polygon_containing_point(ego_config: "CameraConfig"):
    point = postgis.Point(*ego_config.ego_translation[:2])
    query = MAX_POLYGON_CONTAIN_QUERY.format(
        ego_translation=sql.Literal(point), location=sql.Literal(ego_config.location)
    )

    results = database.execute(query)
    if len(results) > 1:
        for result in results:
            segmenttypes = result[4:]
            if not is_roadsection(segmenttypes):
                results = [result]
                break
    assert len(results) == 1, (ROAD_TYPES, [r[4:] for r in results])
    result = results[0]
    assert len(result) == 4 + len(ROAD_TYPES), (len(results), len(ROAD_TYPES) + 4)

    output = make_road_polygon_with_heading(result)

    types, line, heading = output[2:5]
    assert line is not None
    assert types is not None
    assert heading is not None
    road_polygon = reformat_return_polygon([output])[0]
    polygonid, roadpolygon, roadtype, segmentlines, segmentheadings = road_polygon
    fov_lines = get_fov_lines(ego_config)

    polygon = swkb.loads(roadpolygon.to_ewkb(), hex=True)
    assert isinstance(polygon, sg.Polygon)
    return RoadPolygonInfo(
        polygonid, polygon, segmentlines, roadtype, segmentheadings, True, ego_config, fov_lines
    )


def map_detections_to_segments(detections: "list[obj_detection]", ego_config: "CameraConfig"):
    tokens = [*map(lambda x: x.detection_id.obj_order, detections)]
    points = [postgis.Point(d.car_loc3d[0], d.car_loc3d[1]) for d in detections]

    location = ego_config.location

    convex_points = np.array([[d.car_loc3d[0], d.car_loc3d[1]] for d in detections])

    out = sql.SQL(
        f"""
    WITH
    Point AS (
        SELECT *
        FROM UNNEST(
            {{tokens}},
            {{points}}::geometry(Point)[]
        ) AS _point (token, point)
    ),
    AvailablePolygon AS (
        SELECT *
        FROM SegmentPolygon
        WHERE location = {{location}}
        AND ST_Intersects(SegmentPolygon.elementPolygon, ST_ConvexHull({{convex}}::geometry(MultiPoint)))
        AND (SegmentPolygon.__RoadType__intersection__
        OR SegmentPolygon.__RoadType__lane__
        OR SegmentPolygon.__RoadType__lanegroup__
        OR SegmentPolygon.__RoadType__lanesection__)
        AND NOT SegmentPolygon.__RoadType__roadsection__
    ),
    MinPolygon AS (
        SELECT token, MIN(ST_Area(Polygon.elementPolygon)) as size
        FROM Point AS p
        JOIN AvailablePolygon AS Polygon
            ON ST_Contains(Polygon.elementPolygon, p.point)
        GROUP BY token
    ),
    MinPolygonId AS (
        SELECT token, MIN(elementId) as elementId
        FROM Point AS p
        JOIN MinPolygon USING (token)
        JOIN AvailablePolygon as Polygon
            ON ST_Contains(Polygon.elementPolygon, p.point)
            AND ST_Area(Polygon.elementPolygon) = MinPolygon.size
        GROUP BY token
    )
    SELECT
        p.token,
        AvailablePolygon.elementid,
        AvailablePolygon.elementpolygon,
        ARRAY_AGG(Segment.segmentline)::geometry[],
        ARRAY_AGG(Segment.heading)::real[],
        {SQL_ROAD_TYPES}
    FROM Point AS p
    JOIN MinPolygonId USING (token)
    JOIN AvailablePolygon USING (elementId)
    JOIN Segment USING (elementId)
    GROUP BY
        AvailablePolygon.elementid,
        p.token,
        AvailablePolygon.elementpolygon,
        {SQL_ROAD_TYPES};
    """
    ).format(
        tokens=sql.Literal(tokens),
        points=sql.Literal(points),
        convex=sql.Literal(postgis.MultiPoint(map(tuple, convex_points))),
        location=sql.Literal(location),
    )
    result = database.execute(out)
    return result


def get_detection_polygon_mapping(detections: "list[obj_detection]", ego_config: "CameraConfig"):
    """
    Given a list of detections, return a list of RoadSegmentWithHeading
    """
    # start_time = time.time()
    times = []
    times.append(time.time())
    results = map_detections_to_segments(detections, ego_config)
    times.append(time.time())

    order_ids, mapped_polygons = [r[0] for r in results], [r[1:] for r in results]
    mapped_polygons = [*map(make_road_polygon_with_heading, mapped_polygons)]
    times.append(time.time())
    for row in mapped_polygons:
        types, line, heading = row[2:5]
        assert line is not None
        assert types is not None
        assert heading is not None
    times.append(time.time())
    mapped_polygons = reformat_return_polygon(mapped_polygons)
    times.append(time.time())
    if any(p.road_type == "intersection" for p in mapped_polygons):
        return {}, times
    times.append(time.time())
    fov_lines = get_fov_lines(ego_config)
    times.append(time.time())

    # def not_in_view(point: "Float2"):
    #     return not in_view(point, ego_config.ego_translation, fov_lines)

    mapped_road_polygon_info: "dict[DetectionId, RoadPolygonInfo]" = {}
    for order_id, road_polygon in list(zip(order_ids, mapped_polygons)):
        frame_idx = detections[0].detection_id.frame_idx
        det_id = DetectionId(frame_idx=frame_idx, obj_order=order_id)
        if det_id in mapped_road_polygon_info:
            print("skipped")
            continue
        polygonid, roadpolygon, roadtype, segmentlines, segmentheadings = road_polygon
        assert segmentlines is not None
        assert segmentheadings is not None

        # assert all(isinstance(line, sg.LineString) for line in segmentlines)

        p = swkb.loads(road_polygon.to_ewkb(), hex=True)
        assert isinstance(p, sg.Polygon)
        XYs: "Tuple[array.array[float], array.array[float]]" = p.exterior.xy
        assert isinstance(XYs, tuple)
        assert isinstance(XYs[0], array.array), type(XYs[0])
        assert isinstance(XYs[1], array.array), type(XYs[1])
        assert isinstance(XYs[0][0], float), type(XYs[0][0])
        assert isinstance(XYs[1][0], float), type(XYs[1][0])
        polygon_points = list(zip(*XYs))
        # roadpolygon = sg.Polygon(polygon_points)

        # decoded_road_polygon_points = polygon_points
        # if all(map(not_in_view, polygon_points)):
        #     continue

        # intersection_points = intersection(fov_lines, roadpolygon)
        # decoded_road_polygon_points += intersection_points
        # keep_road_polygon_points: "list[Float2]" = []
        # for current_road_point in decoded_road_polygon_points:
        #     if in_view(current_road_point, ego_config.ego_translation, fov_lines):
        #         keep_road_polygon_points.append(current_road_point)
        if len(polygon_points) > 2:
            # and sg.Polygon(tuple(keep_road_polygon_points)).area > 1):
            mapped_road_polygon_info[det_id] = RoadPolygonInfo(
                polygonid,
                sg.Polygon(polygon_points),
                segmentlines,
                roadtype,
                segmentheadings,
                False,
                ego_config,
                fov_lines,
            )
    times.append(time.time())

    # logger.info(f'total mapping time: {time.time() - start_time}')
    return mapped_road_polygon_info, times


def get_fov_lines(ego_config: "CameraConfig", ego_fov: float = 70.0) -> "Tuple[Float22, Float22]":
    """
    return: two lines representing fov in world coord
            ((lx1, ly1), (lx2, ly2)), ((rx1, ry1), (rx2, ry2))
    """

    # TODO: accuracy improvement: find fov in 3d -> project down to z=0 plane
    ego_heading = ego_config.ego_heading
    x_ego, y_ego = ego_config.ego_translation[:2]
    left_degree = math.radians(ego_heading + ego_fov / 2 + 90)
    left_fov_line = (
        (x_ego, y_ego),
        (x_ego + math.cos(left_degree) * 50, y_ego + math.sin(left_degree) * 50),
    )
    right_degree = math.radians(ego_heading - ego_fov / 2 + 90)
    right_fov_line = (
        (x_ego, y_ego),
        (x_ego + math.cos(right_degree) * 50, y_ego + math.sin(right_degree) * 50),
    )
    return left_fov_line, right_fov_line


def hex_str_to_linestring(hex: "str"):
    return sg.LineString(swkb.loads(bytes.fromhex(hex)))


def make_road_polygon_with_heading(row: "tuple"):
    eid, polygon, lines, headings, *types = row
    assert len(types) == len(ROAD_TYPES), (types, ROAD_TYPES)
    return RoadSegmentWithHeading(
        eid,
        polygon,
        [t for t, v in zip(ROAD_TYPES, types) if v],
        [*map(hex_str_to_linestring, lines[1:-1].split(":"))],
        headings,
    )
