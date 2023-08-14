import datetime
import math
from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np
import numpy.typing as npt
import postgis
import psycopg2
import psycopg2.sql
from plpygis import Geometry
from shapely.geometry import Point
from shapely.ops import nearest_points

from spatialyze.database import database

from ...camera_config import CameraConfig
from ...payload import Payload
from ...types import DetectionId, Float3
from ..detection_estimation.detection_estimation import DetectionInfo, trajectory_3d
from ..detection_estimation.segment_mapping import RoadPolygonInfo
from ..detection_estimation.utils import get_segment_line, project_point_onto_linestring

test_segment_query = """
SELECT
    segmentpolygon.elementid,
    segmentpolygon.elementpolygon,
    segment.segmentline,
    segmentpolygon.segmenttypes,
    segment.heading
FROM segmentpolygon
    LEFT OUTER JOIN segment
        ON segmentpolygon.elementid = segment.elementid
WHERE segmentpolygon.elementid = '{segment_id}';
"""


segment_closest_query = """
WITH
AvailablePolygon AS (
    SELECT *
    FROM SegmentPolygon
    WHERE location = {location}
),
min_distance AS (
SELECT
    MIN(ST_Distance(AvailablePolygon.elementpolygon, {point}::geometry)) distance
FROM AvailablePolygon
    LEFT OUTER JOIN segment
        ON AvailablePolygon.elementid = segment.elementid
WHERE ST_Distance(AvailablePolygon.elementpolygon, {point}::geometry) > 0
    {heading_filter}
)
SELECT
    AvailablePolygon.elementid,
    AvailablePolygon.elementpolygon,
    segment.segmentline,
    AvailablePolygon.segmenttypes,
    segment.heading
FROM min_distance, AvailablePolygon
LEFT OUTER JOIN segment
        ON AvailablePolygon.elementid = segment.elementid
WHERE ST_Distance(AvailablePolygon.elementpolygon, {point}::geometry) = min_distance.distance;
"""


segment_contain_vector_query = """
WITH
AvailablePolygon AS (
    SELECT *
    FROM SegmentPolygon
    WHERE location = {location}
),
min_contain AS (
SELECT
    MIN(ST_Area(AvailablePolygon.elementpolygon)) min_segment_area
FROM AvailablePolygon
    LEFT OUTER JOIN segment
        ON AvailablePolygon.elementid = segment.elementid
WHERE ST_Contains(
    AvailablePolygon.elementpolygon,
    {point}::geometry
    )
    {heading_filter}
)
SELECT
    AvailablePolygon.elementid,
    AvailablePolygon.elementpolygon,
    segment.segmentline,
    AvailablePolygon.segmenttypes,
    segment.heading
FROM min_contain, AvailablePolygon
LEFT OUTER JOIN segment
        ON AvailablePolygon.elementid = segment.elementid
WHERE ST_Area(AvailablePolygon.elementpolygon) = min_contain.min_segment_area;
"""


HEADING_FILTER = """
AND cos(radians(
        facingRelative({point_heading}::real,
                      degrees(segment.heading)::real))
        ) > 0
"""


SegmentQueryResult = Tuple[str, postgis.Polygon, postgis.LineString, List[str], float]


class PolygonAndId(NamedTuple):
    id: "int"
    polygon: "shapely.geometry.Polygon"


@dataclass
class ValidSegmentPoint:
    detection_id: "DetectionId"
    car_loc3d: "Float3"
    timestamp: "datetime.datetime"
    segment_type: "str"
    segment_line: "postgis.LineString"
    segment_heading: "float"
    road_polygon_info: "RoadPolygonInfo | PolygonAndId"
    obj_id: "int | None" = None
    type: "str | None" = None
    next: "SegmentPoint | None" = None
    prev: "SegmentPoint | None" = None


@dataclass
class InvalidSegmentPoint:
    detection_id: "DetectionId"
    car_loc3d: "Float3"
    timestamp: "datetime.datetime"
    obj_id: "int | None" = None
    type: "str | None" = None
    next: "SegmentPoint | None" = None
    prev: "SegmentPoint | None" = None


SegmentPoint = Union[ValidSegmentPoint, InvalidSegmentPoint]


def construct_new_road_segment_info(result: "list[SegmentQueryResult]"):
    """Construct new road segment info based on query result.

    This Function constructs the new the road segment info
    based on the query result that finds the correct road segment that contains
    the calibrated trajectory point.
    """
    kept_segment = (None, None)
    road_segment_info = None
    for road_segment in result:
        segmentid, segmentpolygon, segmentline, segmenttype, segmentheading = road_segment
        segmenttype = (segmenttype[0] if segmenttype is not None else None,)
        segmentheading = math.degrees(segmentheading) if segmentheading is not None else None
        segmentid = segmentid.split("_")[0]
        assert segmentline
        segmentline = Geometry(segmentline.to_ewkb()).shapely
        if segmentid == kept_segment[0]:
            assert road_segment_info is not None
            road_segment_info.segment_lines.append(segmentline)
            road_segment_info.segment_headings.append(segmentheading)
        else:
            if kept_segment[0] is not None:
                if kept_segment[1] is not None:
                    continue
        segmentpolygon = Geometry(segmentpolygon.to_ewkb()).shapely
        road_segment_info = RoadPolygonInfo(
            segmentid,
            segmentpolygon,
            [segmentline],
            segmenttype,
            [segmentheading],
            None,
            False,
            None,
        )
        kept_segment = (segmentid, segmenttype)
    assert road_segment_info is not None
    return road_segment_info


def find_middle_segment(
    current_segment: "ValidSegmentPoint", next_segment: "ValidSegmentPoint", payload: "Payload"
):
    current_time = current_segment.timestamp
    next_time = next_segment.timestamp

    current_segment_polygon = current_segment.road_polygon_info.polygon
    next_segment_polygon = next_segment.road_polygon_info.polygon

    assert not current_segment_polygon.intersects(next_segment_polygon), (
        current_segment.road_polygon_info.id,
        next_segment.road_polygon_info.id,
    )

    # current_center_point = current_segment.road_segment_info.segment_polygon.centroid
    # next_center_point = next_segment.road_segment_info.segment_polygon.centroid
    # connected_center = LineString([current_center_point, next_center_point])
    # current_intersection = connected_center.intersection(current_segment_polygon).coords[0]
    # next_intersection = connected_center.intersection(next_segment_polygon).coords[0]
    p1, p2 = nearest_points(current_segment_polygon, next_segment_polygon)

    middle_idx = (current_segment.detection_id.frame_idx + next_segment.detection_id.frame_idx) // 2
    assert middle_idx != current_segment.detection_id.frame_idx
    assert middle_idx != next_segment.detection_id.frame_idx

    middle_camera_config = payload.video._camera_configs[middle_idx]
    assert middle_camera_config is not None

    middle_time = middle_camera_config.timestamp

    loc1: "npt.NDArray[np.float64]" = np.array([p1.x, p1.y])
    assert loc1.dtype == np.dtype(np.float64)
    loc2: "npt.NDArray[np.float64]" = np.array([p2.x, p2.y])
    assert loc2.dtype == np.dtype(np.float64)
    locdiff = loc2 - loc1

    progress = (middle_time - current_time) / (next_time - current_time)
    intersection_center: "list[float]" = (loc1 + locdiff * progress).tolist()
    assert isinstance(intersection_center, list)
    assert len(intersection_center) == 2

    locations = set(f.location for f in payload.video._camera_configs)
    assert len(locations) == 1, locations
    location = [*locations][0]

    assert not current_segment_polygon.contains(Point(intersection_center))
    contain_query = psycopg2.sql.SQL(segment_contain_vector_query).format(
        point=psycopg2.sql.Literal(postgis.point.Point(intersection_center)),
        heading_filter=psycopg2.sql.SQL("AND True"),
        location=psycopg2.sql.Literal(location),
    )
    result = database.execute(contain_query)
    if not result:
        closest_query = psycopg2.sql.SQL(segment_closest_query).format(
            point=psycopg2.sql.Literal(postgis.point.Point(intersection_center)),
            heading_filter=psycopg2.sql.SQL("AND True"),
            location=psycopg2.sql.Literal(location),
        )
        result = database.execute(closest_query)
    # TODO: function update_current_road_segment_info does not exist
    # new_road_segment_info = update_current_road_segment_info(result)
    new_road_segment_info = construct_new_road_segment_info(result)

    new_segment_line, new_heading = get_segment_line(new_road_segment_info, intersection_center)
    timestamp = current_time + (next_time - current_time) / 2
    middle_segment = ValidSegmentPoint(
        DetectionId(middle_idx, None),
        (*intersection_center, 0.0),
        timestamp,
        new_segment_line,
        new_heading,
        new_road_segment_info,
    )
    return middle_segment


def binary_search_segment(
    current_segment: "ValidSegmentPoint",
    next_segment: "ValidSegmentPoint",
    payload: "Payload",
) -> "list[ValidSegmentPoint]":
    if 0 <= next_segment.detection_id.frame_idx - current_segment.detection_id.frame_idx <= 1:
        # same detection or detections on consecutive frame
        return []
    elif current_segment.road_polygon_info.id == next_segment.road_polygon_info.id:
        # detections in between are in the same polygon
        assert current_segment.road_polygon_info == current_segment.road_polygon_info

        if current_segment.segment_line == next_segment.segment_line:
            # detections in between are in the same segment line
            assert current_segment.segment_heading == next_segment.segment_heading

            loc1: "npt.NDArray[np.float64]" = np.array(current_segment.car_loc3d)
            assert loc1.dtype == np.dtype(np.float64)
            loc2: "npt.NDArray[np.float64]" = np.array(next_segment.car_loc3d)
            assert loc2.dtype == np.dtype(np.float64)

            locdiff = loc2 - loc1
            timediff = next_segment.timestamp - current_segment.timestamp

            def interpolate_segment(args: "Tuple[int, CameraConfig]"):
                index, frame = args

                progress = (frame.timestamp - current_segment.timestamp) / timediff
                location = loc1 + locdiff * progress
                assert location.shape == (3,)
                assert location.dtype == np.dtype(np.float64)

                return ValidSegmentPoint(
                    DetectionId(index, None),
                    tuple(location),
                    frame.timestamp,
                    current_segment.segment_line,
                    current_segment.segment_heading,
                    current_segment.road_polygon_info,
                )

            st = current_segment.detection_id.frame_idx + 1
            ed = next_segment.detection_id.frame_idx
            configs_with_index = [*enumerate(payload.video._camera_configs)]
            return [*map(interpolate_segment, configs_with_index[st:ed])]
        else:
            # detections in between are in different segment line
            # TODO: interpolate all the detections between
            # TODO: need to know what are the segment lines in between
            return []

    elif current_segment.road_polygon_info.polygon.intersects(
        next_segment.road_polygon_info.polygon
    ):
        # both polygons are next to each other
        # TODO: remove because we still need to fill in approximate locations
        # of frames in between
        # TODO: interpolate between 2 consecutive segments
        # TODO: need to know what are the segment lines in between for both polygon
        return []
    else:
        middle_segment = find_middle_segment(current_segment, next_segment, payload)
        # import code; code.interact(local=vars())

        before = binary_search_segment(current_segment, middle_segment, payload)
        after = binary_search_segment(middle_segment, next_segment, payload)

        return before + [middle_segment] + after


def complete_segment_trajectory(road_segment_trajectory: "list[ValidSegmentPoint]", payload: "Payload"):
    completed_segment_trajectory: "list[ValidSegmentPoint]" = [road_segment_trajectory[0]]

    for current_segment, next_segment in zip(
        road_segment_trajectory[:-1], road_segment_trajectory[1:]
    ):
        completed_segment_trajectory.extend(
            binary_search_segment(current_segment, next_segment, payload)
        )
        completed_segment_trajectory.append(next_segment)

    return completed_segment_trajectory


def calibrate(
    trajectory_3d: "list[trajectory_3d]",
    detection_infos: "list[DetectionInfo]",
    frame_indices: "list[int]",
    payload: "Payload",
) -> "list[ValidSegmentPoint]":
    """Calibrate the trajectory to the road segments.

    Given a trajectory and the corresponding detection infos, map the trajectory
    to the correct road segments.
    The returned value is a list of SegmentTrajectoryPoint.
    """
    road_segment_trajectory: "list[ValidSegmentPoint]" = []
    for i in range(len(trajectory_3d)):
        current_point3d, timestamp = trajectory_3d[i]
        current_point = current_point3d[:2]
        detection_info = detection_infos[i]
        frame_idx = frame_indices[i]
        current_road_segment_heading = detection_info.segment_heading
        current_segment_line = detection_info.segment_line
        current_road_segment_info = detection_info.road_polygon_info
        if i != len(trajectory_3d) - 1:
            next_point = trajectory_3d[i + 1][0][:2]
            if current_road_segment_heading is not None:
                current_point_heading = math.atan2(
                    next_point[1] - current_point[1], next_point[0] - current_point[0]
                )
                current_point_heading = math.degrees(current_point_heading)

                relative_heading = (
                    abs(current_road_segment_heading + 90 - current_point_heading) % 360
                )

            if current_road_segment_heading is None or math.cos(math.radians(relative_heading)) > 0:
                road_segment_trajectory.append(
                    ValidSegmentPoint(
                        detection_info.detection_id,
                        current_point3d,
                        timestamp,
                        current_segment_line,
                        current_road_segment_heading,
                        current_road_segment_info,
                        frame_idx,
                    )
                )
                continue

        locations = set(f.location for f in payload.video._camera_configs)
        assert len(locations) == 1, locations
        location = [*locations][0]

        ### project current_point to the segment line of the previous point
        ### and then find the segment that  contains the projected point
        ### however this requires querying for road segment once for each point to be calibrated
        if len(road_segment_trajectory) == 0:
            heading_filter = psycopg2.sql.SQL(HEADING_FILTER).format(
                point_heading=psycopg2.sql.Literal(current_point_heading - 90)
            )
            query = psycopg2.sql.SQL(segment_closest_query).format(
                point=psycopg2.sql.Literal(postgis.point.Point(current_point)),
                heading_filter=heading_filter,
                location=psycopg2.sql.Literal(location),
            )
        else:
            prev_calibrated_point = road_segment_trajectory[-1]
            prev_segment_line = prev_calibrated_point.segment_line
            prev_segment_heading = prev_calibrated_point.segment_heading
            projection = project_point_onto_linestring(Point(current_point), prev_segment_line)
            current_point3d = (projection.x, projection.y, 0.0)
            heading_filter = psycopg2.sql.SQL(HEADING_FILTER).format(
                point_heading=psycopg2.sql.Literal(prev_segment_heading - 90)
            )
            query = psycopg2.sql.SQL(segment_contain_vector_query).format(
                point=psycopg2.sql.Literal(postgis.point.Point((projection.x, projection.y))),
                heading_filter=heading_filter,
                location=psycopg2.sql.Literal(location),
            )
        result = database.execute(query)
        if len(result) == 0:
            closest_query = psycopg2.sql.SQL(segment_closest_query).format(
                point=psycopg2.sql.Literal(postgis.point.Point(current_point)),
                heading_filter=heading_filter,
                location=psycopg2.sql.Literal(location),
            )
            result = database.execute(closest_query)
        assert len(result) > 0
        new_road_segment_info = construct_new_road_segment_info(result)
        new_segment_line, new_heading = get_segment_line(current_road_segment_info, current_point3d)
        road_segment_trajectory.append(
            ValidSegmentPoint(
                detection_info.detection_id,
                current_point3d,
                timestamp,
                new_segment_line,
                new_heading,
                new_road_segment_info,
                frame_idx,
            )
        )
    return complete_segment_trajectory(road_segment_trajectory, payload)
