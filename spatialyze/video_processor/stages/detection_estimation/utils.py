import datetime
import math
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import numpy.typing as npt
import shapely
import shapely.geometry
import shapely.wkb

from ...types import Float2, Float3, Float22

if TYPE_CHECKING:
    from .detection_estimation import DetectionInfo
    from .segment_mapping import RoadPolygonInfo


SAME_DIRECTION = "same_direction"
OPPOSITE_DIRECTION = "opposite_direction"

SEGMENT_TO_MAP = ("lane", "lanesection", "intersection", "lanegroup")
ROAD_TYPES = ["road", "lane", "lanesection", "roadsection", "intersection", "lanegroup"]


class trajectory_3d(NamedTuple):
    coordinates: "Float3"
    timestamp: "datetime.datetime"


class temporal_speed(NamedTuple):
    speed: float
    timestamp: "datetime.datetime"


def mph_to_mps(mph: "float"):
    return mph * 0.44704


MAX_CAR_SPEED = {
    "lane": 25.0,
    # TODO: if we decide to map to smallest polygon,
    # 'lanegroup' would mean street parking spots.
    "lanegroup": 25.0,
    "road": 25.0,
    "lanesection": 25.0,
    "roadSection": 25.0,
    "intersection": 25.0,
    "highway": 55.0,
    "residential": 25.0,
}
MAX_CAR_SPEED.update({k: mph_to_mps(v) for k, v in MAX_CAR_SPEED.items()})


def time_elapse(current_time: datetime.datetime, elapsed_time: float):
    return current_time + datetime.timedelta(seconds=elapsed_time)


def compute_distance(loc1, loc2) -> float:
    return shapely.geometry.Point(loc1).distance(shapely.geometry.Point(loc2))


def relative_direction(vec1, vec2):
    return (vec1[0] * vec2[0] + vec1[1] * vec2[1]) / math.sqrt(
        vec1[0] ** 2 + vec1[1] ** 2
    ) / math.sqrt(vec2[0] ** 2 + vec2[1] ** 2) > 0


def car_move(car_loc, car_heading, car_speed, duration):
    """Return the location of the car after duration in seconds"""
    return (
        car_loc[0] + car_speed * duration * math.cos(math.radians(car_heading)),
        car_loc[1] + car_speed * duration * math.sin(math.radians(car_heading)),
    )


def project_point_onto_linestring(
    point: "shapely.geometry.Point",
    line: "shapely.geometry.LineString",
) -> "shapely.geometry.Point | None":
    x: "npt.NDArray[np.float64]" = np.array(point.coords[0])
    assert x.dtype == np.dtype(np.float64)

    u: "npt.NDArray[np.float64]" = np.array(line.coords[0])
    assert u.dtype == np.dtype(np.float64)
    v: "npt.NDArray[np.float64]" = np.array(line.coords[len(line.coords) - 1])
    assert v.dtype == np.dtype(np.float64)

    if np.allclose(u, v):
        return None

    n = v - u
    assert n.dtype == np.dtype(np.float64)
    n /= np.linalg.norm(n, 2)

    P = u + n * np.dot(x - u, n)
    return shapely.geometry.Point(P)


def _construct_extended_line(
    polygon: "shapely.geometry.Polygon | list[Float2] | list[Float3]",
    line: "Float22",
):
    """
    line: represented by 2 points
    Find the line segment that can possibly intersect with the polygon
    """
    try:
        polygon = shapely.geometry.Polygon(polygon)
        minx, miny, maxx, maxy = list(polygon.bounds)
    except BaseException:
        assert isinstance(polygon, tuple) or isinstance(polygon, list)
        assert len(polygon) <= 2
        if len(polygon) == 2:
            try:
                boundary = shapely.geometry.LineString(polygon).boundary
                assert hasattr(boundary, "geoms")
                a, b = getattr(boundary, "geoms")
                minx, maxx = sorted([a.x, b.x])
                miny, maxy = sorted([a.y, b.y])
            except BaseException:
                assert polygon[0] == polygon[1]
                minx, miny = polygon[0][0], polygon[0][1]
                maxx, maxy = minx, miny
        else:
            minx, miny = polygon[0][0], polygon[0][1]
            maxx, maxy = minx, miny

    _line = shapely.geometry.LineString(line)
    bounding_box = shapely.geometry.box(minx, miny, maxx, maxy)
    _boundary = _line.boundary
    assert hasattr(_boundary, "geoms")
    a, b = getattr(_boundary, "geoms")
    if a.x == b.x:  # vertical line
        extended_line = shapely.geometry.LineString([(a.x, miny), (a.x, maxy)])
    elif a.y == b.y:  # horizonthal line
        extended_line = shapely.geometry.LineString([(minx, a.y), (maxx, a.y)])
    else:
        # linear equation: y = k*x + m
        slope = (b.y - a.y) / (b.x - a.x)
        y_intercept = a.y - slope * a.x

        y0 = slope * minx + y_intercept
        y1 = slope * maxx + y_intercept
        x0 = (miny - y_intercept) / slope
        x1 = (maxy - y_intercept) / slope
        points_on_boundary_lines = [
            shapely.geometry.Point(minx, y0),
            shapely.geometry.Point(maxx, y1),
            shapely.geometry.Point(x0, miny),
            shapely.geometry.Point(x1, maxy),
        ]
        points_sorted_by_distance = sorted(points_on_boundary_lines, key=bounding_box.distance)
        extended_line = shapely.geometry.LineString(points_sorted_by_distance[:2])
    return extended_line


def line_to_polygon_intersection(
    polygon: "shapely.geometry.Polygon",
    line: "Float22",
) -> "list[Float2]":
    """Find the intersection between a line and a polygon."""
    try:
        extended_line = _construct_extended_line(polygon, line)
        intersection = extended_line.intersection(polygon.buffer(0))
    except BaseException:
        return []
    if intersection.is_empty:
        return []
    elif isinstance(intersection, shapely.geometry.LineString):
        return list(intersection.coords)
    elif isinstance(intersection, shapely.geometry.MultiLineString):
        all_intersections = []
        for intersect in intersection.geoms:
            assert isinstance(intersect, shapely.geometry.LineString)
            all_intersections.extend(list(intersect.coords))
        return list(all_intersections)
    else:
        raise ValueError("Unexpected intersection type")


### ASSUMPTIONS ###
def max_car_speed(road_type):
    """Maximum speed of a car on the given road type

    For example, the maximum speed of a car on a highway is 65mph,
    and 25mph on a residential road.
    """
    return MAX_CAR_SPEED[road_type]


### HELPER FUNCTIONS ###
def get_ego_speed(ego_trajectory):
    """Get the ego speed based on the ego trajectory."""
    point_wise_temporal_speed = []
    for i in range(len(ego_trajectory) - 1):
        x, y, z = ego_trajectory[i].coordinates
        timestamp = ego_trajectory[i].timestamp
        x_next, y_next, z_next = ego_trajectory[i + 1].coordinates
        timestamp_next = ego_trajectory[i + 1].timestamp
        distance = compute_distance((x, y), (x_next, y_next))
        point_wise_temporal_speed.append(
            temporal_speed(distance / (timestamp_next - timestamp).total_seconds(), timestamp)
        )
    return point_wise_temporal_speed


def get_ego_avg_speed(ego_trajectory):
    """Get the ego average speed based on the ego trajectory."""
    point_wise_ego_speed = get_ego_speed(ego_trajectory)
    return sum([speed.speed for speed in point_wise_ego_speed]) / len(point_wise_ego_speed)


def get_segment_line(road_segment_info: "RoadPolygonInfo", car_loc3d: "Float3"):
    """Get the segment line the location is in."""
    segment_lines = road_segment_info.segment_lines
    segment_headings = road_segment_info.segment_headings

    line_heading = list(zip(segment_lines, segment_headings))
    longest_segment_line, longest_heading = max(line_heading, key=lambda x: x[0].length)
    for segment_line, segment_heading in line_heading:
        if segment_line is None:
            continue

        projection = project_point_onto_linestring(
            shapely.geometry.Point(car_loc3d[:2]), segment_line
        )

        if projection is None:
            continue

        if segment_line.distance(projection) < 1e-8:
            if abs(segment_heading - longest_heading) < 30:
                return segment_line, segment_heading

    return longest_segment_line, longest_heading


def time_to_exit_current_segment(
    detection_info: "DetectionInfo",
    current_time: datetime.datetime,
    car_loc: Float3,
    # car_trajectory=None,
    # is_ego=False,
):
    """Return the time that the car exit the current segment

    Assumption:
    car heading is the same as road heading
    car drives at max speed if no trajectory is given
    """
    # if is_ego:
    #     current_polygon_info = detection_info.ego_road_polygon_info
    #     polygon = current_polygon_info.polygon
    # else:
    current_polygon_info = detection_info.road_polygon_info
    polygon = current_polygon_info.polygon

    # if car_trajectory:
    #     for point in car_trajectory:
    #         if point.timestamp > current_time and not shapely.geometry.Polygon(polygon).contains(
    #             shapely.geometry.Point(point.coordinates[:2])
    #         ):
    #             return point.timestamp, point.coordinates[:2]
    #     return None, None
    if detection_info.road_type == "intersection" or (
        detection_info.segment_heading is None and detection_info.road_type != "intersection"
    ):
        return None, None
    segmentheading = detection_info.segment_heading + 90
    _car_loc = shapely.geometry.Point(car_loc[:2])
    car_vector = (math.cos(math.radians(segmentheading)), math.sin(math.radians(segmentheading)))
    car_heading_point = (_car_loc.x + car_vector[0], _car_loc.y + car_vector[1])
    # car_heading_line = shapely.geometry.LineString([_car_loc, car_heading_point])
    car_heading_line = (
        (float(_car_loc.x), float(_car_loc.y)),
        (float(car_heading_point[0]), float(car_heading_point[1])),
    )
    intersection = line_to_polygon_intersection(polygon, car_heading_line)
    if len(intersection) == 2:
        intersection_1_vector = (intersection[0][0] - _car_loc.x, intersection[0][1] - _car_loc.y)
        relative_direction_1 = relative_direction(car_vector, intersection_1_vector)
        intersection_2_vector = (intersection[1][0] - _car_loc.x, intersection[1][1] - _car_loc.y)
        relative_direction_2 = relative_direction(car_vector, intersection_2_vector)
        distance1 = compute_distance(_car_loc, intersection[0])
        distance2 = compute_distance(_car_loc, intersection[1])
        if relative_direction_1:
            # logger.info(f'relative_dierction_1 {distance1} {current_time} {max_car_speed(current_polygon_info.road_type)}')
            return (
                time_elapse(
                    current_time, distance1 / max_car_speed(current_polygon_info.road_type)
                ),
                intersection[0],
            )
        elif relative_direction_2:
            # logger.info(f'relative_direction_2 {distance2} {current_time}')
            return (
                time_elapse(
                    current_time, distance2 / max_car_speed(current_polygon_info.road_type)
                ),
                intersection[1],
            )
        else:
            # logger.info("wrong car moving direction")
            return None, None
    return None, None


def get_car_exits_view_frame_num(
    detection_info: "DetectionInfo",
    ego_views: "list[shapely.geometry.Polygon]",
    max_frame_num: int,
    fps: int | float = 20,
):
    car_heading = detection_info.segment_heading
    road_type = detection_info.road_type
    car_loc = detection_info.car_loc3d[:2]
    if car_heading is None or road_type == "intersection":
        return None

    assert max_frame_num < len(ego_views)
    assert detection_info.detection_id.frame_idx < max_frame_num
    start_frame_num = detection_info.detection_id.frame_idx
    car_speed = max_car_speed(road_type)
    car_heading += 90
    frame_idx = detection_info.detection_id.frame_idx
    while frame_idx + 1 < max_frame_num:
        next_frame_num = frame_idx + 1
        next_ego_view = ego_views[next_frame_num]
        next_ego_view = next_ego_view
        duration = (next_frame_num - start_frame_num) / fps
        next_car_loc = car_move(car_loc, car_heading, car_speed, duration)
        if not next_ego_view.contains(shapely.geometry.Point(next_car_loc[:2])):
            return max(frame_idx, start_frame_num + 1)
        frame_idx = next_frame_num
    return max_frame_num
