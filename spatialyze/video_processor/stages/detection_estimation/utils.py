import datetime
import logging
import math
from typing import TYPE_CHECKING, List, NamedTuple, Tuple

import numpy as np
import numpy.typing as npt
import shapely.geometry

from spatialyze.database import database

if TYPE_CHECKING:
    from ...camera_config import CameraConfig
    from .detection_estimation import DetectionInfo
    from .optimized_segment_mapping import RoadPolygonInfo
    from .segment_mapping import CameraPolygonMapping


logger = logging.getLogger(__name__)

Float2 = Tuple[float, float]
Float3 = Tuple[float, float, float]
Float22 = Tuple[Float2, Float2]


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


def time_elapse(current_time, elapsed_time):
    return current_time + datetime.timedelta(seconds=elapsed_time)


def compute_area(polygon) -> float:
    return shapely.geometry.box(*polygon).area


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
    point: "shapely.geometry.Point", line: "shapely.geometry.LineString"
) -> "shapely.geometry.Point":
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
    polygon: "shapely.geometry.Polygon | List[Float2] | List[Float3]", line: "Float22"
):
    """
    line: represented by 2 points
    Find the line segment that can possibly intersect with the polygon
    """
    try:
        polygon = shapely.geometry.Polygon(polygon)
        minx, miny, maxx, maxy = polygon.bounds
    except BaseException:
        assert isinstance(polygon, tuple) or isinstance(polygon, list)
        assert len(polygon) <= 2
        if len(polygon) == 2:
            try:
                a, b = shapely.geometry.LineString(polygon).boundary.geoms
                minx = min(a.x, b.x)
                maxx = max(a.x, b.x)
                miny = min(a.y, b.y)
                maxy = max(a.y, b.y)
            except BaseException:
                assert polygon[0] == polygon[1]
                minx = polygon[0][0]
                maxx = polygon[0][0]
                miny = polygon[0][1]
                maxy = polygon[0][1]
        else:
            minx = polygon[0][0]
            maxx = polygon[0][0]
            miny = polygon[0][1]
            maxy = polygon[0][1]

    line = shapely.geometry.LineString(line)
    bounding_box = shapely.geometry.box(minx, miny, maxx, maxy)
    a, b = line.boundary.geoms
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


def intersection_between_line_and_trajectory(line, trajectory: "List[Float3]"):
    """Find the intersection between a line and a trajectory."""
    # trajectory_to_polygon = shapely.geometry.Polygon(trajectory)
    # TODO: should use a different function than _construct_extended_line
    extended_line = _construct_extended_line(trajectory, line)
    if len(trajectory) == 1:
        intersection = extended_line.intersection(shapely.geometry.Point(trajectory[0]))
    else:
        intersection = extended_line.intersection(shapely.geometry.LineString(trajectory))
    if not isinstance(intersection, shapely.geometry.LineString) or intersection.is_empty:
        return tuple()
    elif isinstance(intersection, shapely.geometry.LineString):
        return tuple(intersection.coords)


def line_to_polygon_intersection(
    polygon: "shapely.geometry.Polygon", line: "Float22"
) -> "List[Float2]":
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


def min_car_speed(road_type):
    return max_car_speed(road_type) / 2


### HELPER FUNCTIONS ###
def get_ego_trajectory(video: str, sorted_ego_config: "list[CameraConfig]"):
    assert sorted_ego_config is not None
    return [trajectory_3d(config.ego_translation, config.timestamp) for config in sorted_ego_config]


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


def detection_to_img_segment(
    car_loc2d: "Float2",
    cam_polygon_mapping: "list[CameraPolygonMapping]",
):
    """Get the image segment that contains the detected car."""
    maximum_mapping: "CameraPolygonMapping | None" = None
    maximum_mapping_area: float = 0.0
    point = shapely.geometry.Point(car_loc2d)

    for mapping in cam_polygon_mapping:
        cam_segment, road_segment_info = mapping
        p_cam_segment = shapely.geometry.Polygon(cam_segment)
        segment_type = road_segment_info.road_type
        if p_cam_segment.contains(point) and segment_type in SEGMENT_TO_MAP:
            area = p_cam_segment.area
            if area > maximum_mapping_area:
                maximum_mapping = mapping
                maximum_mapping_area = area

    return maximum_mapping


def detection_to_nearest_segment(
    car_loc3d: "Float3",
    cam_polygon_mapping: "list[CameraPolygonMapping]",
):
    assert len(cam_polygon_mapping) != 0
    point = shapely.geometry.Point(car_loc3d[:2])

    min_distance = float("inf")
    min_mapping = None
    for mapping in cam_polygon_mapping:
        _, road_polygon_info = mapping
        polygon = road_polygon_info.polygon

        distance = polygon.distance(point)
        if distance < min_distance:
            min_distance = distance
            min_mapping = mapping

    assert min_mapping is not None
    return min_mapping


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


def location_calibration(car_loc3d: "Float3", road_segment_info: "RoadPolygonInfo") -> "Float3":
    """Calibrate the 3d location of the car with the road segment
    the car lies in.
    """
    segment_polygon = road_segment_info.polygon
    assert segment_polygon is not None
    segment_lines = road_segment_info.segment_lines
    if segment_lines is None or len(segment_lines) == 0:
        return car_loc3d
    # TODO: project onto multiple linestrings and find the closest one
    projection = project_point_onto_linestring(
        shapely.geometry.Point(car_loc3d[:2]), segment_lines
    ).coords
    return projection[0], projection[1], car_loc3d[2]


def get_largest_polygon_containing_ego(cam_segment_mapping: "List[CameraPolygonMapping]"):
    maximum_mapping: "CameraPolygonMapping | None" = None
    maximum_mapping_area: float = 0.0

    for mapping in cam_segment_mapping:
        _, road_segment_info = mapping
        area = shapely.geometry.Polygon(road_segment_info.polygon).area
        if road_segment_info.contains_ego and area > maximum_mapping_area:
            maximum_mapping = mapping
            maximum_mapping_area = area

    assert maximum_mapping is not None, [c.road_polygon_info.id for c in cam_segment_mapping]
    return maximum_mapping


def time_to_nearest_frame(
    video: str, timestamp: "datetime.datetime"
) -> "Tuple[str, int, datetime.datetime]":
    """Return the frame that is closest to the timestamp"""
    query = f"""
    WITH Cameras_with_diff as (
        SELECT *, abs(extract(epoch from timestamp-\'{timestamp}\')) as diff
        FROM Cameras
        WHERE fileName LIKE '%{video}%'
    )
    SELECT
        fileName,
        frameNum,
        cameras.timestamp
    FROM Cameras_with_diff c1
    WHERE c1.diff = (SELECT MIN(c2.diff) from Cameras_with_diff c2)
    LIMIT 1
    """
    return database.execute(query)[0]


def timestamp_to_nearest_trajectory(trajectory, timestamp):
    """Return the trajectory point that is closest to the timestamp"""
    return min(trajectory, key=lambda x: abs((x.timestamp - timestamp).total_seconds()))


def point_to_nearest_trajectory(point, trajectory):
    """Return the trajectory point that is closest to the point"""
    return min(trajectory, key=lambda x: compute_distance(x.coordinates, point))


def ego_departure(ego_trajectory: "List[trajectory_3d]", current_time: "datetime.datetime"):
    for i in range(len(ego_trajectory)):
        point = ego_trajectory[i]
        if point.timestamp > current_time:
            for j in range(i, len(ego_trajectory)):
                if compute_distance(ego_trajectory[j].coordinates, point.coordinates) < 5:
                    non_stop_point = ego_trajectory[j]
                    break
            if i == j:
                return False, point.timestamp, point.coordinates
            elif j == len(ego_trajectory) - 1:
                return True, ego_trajectory[j].timestamp, ego_trajectory[j].coordinates
            return True, non_stop_point.timestamp, non_stop_point.coordinates
    return False, ego_trajectory[-1].timestamp, ego_trajectory[-1].coordinates


def time_to_exit_current_segment(
    detection_info: "DetectionInfo", current_time, car_loc, car_trajectory=None, is_ego=False
):
    """Return the time that the car exit the current segment

    Assumption:
    car heading is the same as road heading
    car drives at max speed if no trajectory is given
    """
    if is_ego:
        current_polygon_info = detection_info.ego_road_polygon_info
        polygon = current_polygon_info.polygon
    else:
        current_polygon_info = detection_info.road_polygon_info
        polygon = current_polygon_info.polygon

    if car_trajectory:
        for point in car_trajectory:
            if point.timestamp > current_time and not shapely.geometry.Polygon(polygon).contains(
                shapely.geometry.Point(point.coordinates[:2])
            ):
                return point.timestamp, point.coordinates[:2]
        return None, None
    if detection_info.road_type == "intersection":
        return None, None
    if detection_info.segment_heading is None and detection_info.road_type != "intersection":
        return None, None
    segmentheading = detection_info.segment_heading + 90
    car_loc = shapely.geometry.Point(car_loc[:2])
    car_vector = (math.cos(math.radians(segmentheading)), math.sin(math.radians(segmentheading)))
    car_heading_point = (car_loc.x + car_vector[0], car_loc.y + car_vector[1])
    car_heading_line = shapely.geometry.LineString([car_loc, car_heading_point])
    intersection = line_to_polygon_intersection(polygon, car_heading_line)
    if len(intersection) == 2:
        intersection_1_vector = (intersection[0][0] - car_loc.x, intersection[0][1] - car_loc.y)
        relative_direction_1 = relative_direction(car_vector, intersection_1_vector)
        intersection_2_vector = (intersection[1][0] - car_loc.x, intersection[1][1] - car_loc.y)
        relative_direction_2 = relative_direction(car_vector, intersection_2_vector)
        distance1 = compute_distance(car_loc, intersection[0])
        distance2 = compute_distance(car_loc, intersection[1])
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


def meetup(
    car1_loc: "Float3 | shapely.geometry.Point",
    car2_loc: "Float3 | shapely.geometry.Point",
    car1_heading,
    car2_heading,
    road_type,
    current_time,
    car1_trajectory: "List[trajectory_3d] | None" = None,
    car2_trajectory: "List[trajectory_3d] | None" = None,
    car1_speed=None,
    car2_speed=None,
):
    """estimate the meetup point as the middle point between car1's loc and car2's loc

    If both trajectories are given, the meetup point is the point where the two trajectories meets
    If one trajectory is given, use that trajectory and other car's speed and direction
    If none trajectory is given, use both cars' speed, or max speed if no speed is given and cars' direction

    For timestamp, it's an estimation based on the trajectory or speed
    Return: (timestamp, meetup_point)

    Assumptions:
        car1 and car2 are driving towards each other, not necessarily the opposite direction
        There shouldn't be a point they intersect, otherwise it's a collision
        If no trajectory, or speed is given, car drives at max speed
        TODO: now I've just implemented the case for ego car to meet another detected car
    """
    car1_loc = shapely.geometry.Point(car1_loc[:2]) if isinstance(car1_loc, tuple) else car1_loc
    assert isinstance(car1_loc, shapely.geometry.Point)
    car2_loc = shapely.geometry.Point(car2_loc[:2]) if isinstance(car2_loc, tuple) else car2_loc
    assert isinstance(car2_loc, shapely.geometry.Point)
    if car1_trajectory is not None and car2_trajectory is None:
        car2_speed = max_car_speed(road_type) if car2_speed is None else car2_speed
        car2_heading += 90
        car2_vector = (
            car2_loc.x + math.cos(math.radians(car2_heading)),
            car2_loc.y + math.sin(math.radians(car2_heading)),
        )
        car2_heading_line = (car2_loc, car2_vector)
        car1_trajectory_points = [
            point.coordinates for point in car1_trajectory if point.timestamp > current_time
        ]
        intersection = intersection_between_line_and_trajectory(
            car2_heading_line, car1_trajectory_points
        )
        if len(intersection) == 1:  # i.e. one car drives towards south, the other towards east
            # logger.info(f"at intersection 1")
            meetup_point = intersection[0]
            time1 = point_to_nearest_trajectory(meetup_point, car1_trajectory)
            distance2 = compute_distance(car2_loc, meetup_point)
            time2 = time_elapse(current_time, distance2 / car2_speed)
            return (min(time1, time2), meetup_point)
        elif len(intersection) == 0:  # i.e. one car drives towards south, the other towards north
            # logger.info(f"at intersection 0")
            meetup_point = shapely.geometry.Point(
                (car1_loc.x + car2_loc.x) / 2, (car1_loc.y + car2_loc.y) / 2
            )
            time1 = point_to_nearest_trajectory(meetup_point, car1_trajectory).timestamp
            if time1 < current_time:
                time1 = current_time
            distance2 = compute_distance(car2_loc, meetup_point)
            time2 = time_elapse(current_time, distance2 / car2_speed)
            if time2 < current_time:
                time2 = current_time
            return (min(time1, time2), meetup_point)


def catchup_time(
    car1_loc,
    car2_loc,
    road_type=None,
    car1_trajectory=None,
    car2_trajectory=None,
    car1_speed=None,
    car2_speed=None,
):
    """Return the time that car1 catches up to car2

    Assumption:
        1. car1 and car2 are driving towards the same direction
        2. car1 drives at max speed, car2 drives at min speed
           if no trajectory or speed is given
        3. TODO: assume now ego is the slowest, it won't bypass another car
    """


def in_view(car_loc, ego_loc, view_distance):
    """At this point, we only care about detect cars. So they are in the frame
    in_view means whether the car is recognizable enough
    """
    return compute_distance(car_loc, ego_loc) < view_distance


def time_to_exit_view(
    ego_loc, car_loc, car_heading, ego_trajectory, current_time, road_type, view_distance
):
    """Return the time, and location that the car goes beyond ego's view distance

    Assumption: car drives at max speed
    """
    ego_speed = get_ego_avg_speed(ego_trajectory)
    car_speed = max_car_speed(road_type)
    exit_view_time = time_elapse(
        current_time, (view_distance - compute_distance(ego_loc, car_loc)) / (car_speed - ego_speed)
    )
    return timestamp_to_nearest_trajectory(ego_trajectory, exit_view_time)


def get_car_exits_view_frame_num(
    detection_info: "DetectionInfo",
    ego_views: "list[shapely.geometry.Polygon]",
    max_frame_num: int,
    fps=20,
):
    car_heading = detection_info.segment_heading
    road_type = detection_info.road_type
    car_loc = detection_info.car_loc3d[:2]
    if car_heading is None or road_type == "intersection":
        return None

    return car_exits_view_frame_num(
        car_loc,
        car_heading,
        road_type,
        ego_views,
        detection_info.detection_id.frame_idx,
        max_frame_num,
        fps,
    )


def car_exits_view_frame_num(
    car_loc: "Float2",
    car_heading: "float",
    road_type: "str",
    ego_views: "list[shapely.geometry.Polygon]",
    current_frame_num: "int",
    car_exits_segment_frame_num: "int",
    fps: "int",
):
    assert car_exits_segment_frame_num < len(ego_views)
    assert current_frame_num < car_exits_segment_frame_num
    start_frame_num = current_frame_num
    car_speed = max_car_speed(road_type)
    car_heading += 90
    while current_frame_num + 1 < car_exits_segment_frame_num:
        next_frame_num = current_frame_num + 1
        next_ego_view = ego_views[next_frame_num]
        duration = (next_frame_num - start_frame_num) / fps
        next_car_loc = car_move(car_loc, car_heading, car_speed, duration)
        if not next_ego_view.contains(shapely.geometry.Point(next_car_loc[:2])):
            return max(current_frame_num, start_frame_num + 1)
        current_frame_num = next_frame_num
    return car_exits_segment_frame_num


def relative_direction_to_ego(obj_heading: float, ego_heading: float):
    """Return the relative direction to ego
    Now only support opposite and same direction
    TODO: add driving into and driving away from
    """
    if obj_heading is None:
        return

    relative_heading = abs(obj_heading - ego_heading) % 360
    if (
        math.cos(math.radians(relative_heading)) < 1
        and math.cos(math.radians(relative_heading)) > math.pi / 6
    ):
        return SAME_DIRECTION
    elif (
        math.cos(math.radians(relative_heading)) > -1
        and math.cos(math.radians(relative_heading)) < -math.pi / 6
    ):
        return OPPOSITE_DIRECTION
