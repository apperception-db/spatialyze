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
import os
import time
from dataclasses import dataclass
from typing import NamedTuple, Tuple

import numpy as np
import numpy.typing as npt
import plpygis
import postgis
import psycopg2
import psycopg2.sql
import shapely
import shapely.geometry
import shapely.wkb

from spatialyze.database import database

from ...camera_config import CameraConfig
from .utils import ROAD_TYPES, Float2, Float3, Float22, line_to_polygon_intersection

logger = logging.getLogger(__name__)

data_path = "/home/yongming/workspace/research/apperception/v1.0-mini/"
input_video_dir = os.path.join(data_path, "sample_videos/")
input_video_name = "CAM_FRONT_n008-2018-08-27.mp4"
input_date = input_video_name.split("_")[-1][:-4]
test_img = "samples/CAM_FRONT/n008-2018-08-01-15-52-19-0400__CAM_FRONT__1533153253912404.jpg"

POLYGON_CONTAIN_QUERY = psycopg2.sql.SQL(
    """
SELECT
    p.elementid,
    p.elementpolygon,
    p.segmenttypes,
    ARRAY_AGG(s.segmentline)::geometry[],
    ARRAY_AGG(s.heading)::real[],
    COUNT(DISTINCT p.elementpolygon),
    COUNT(DISTINCT p.segmenttypes)
FROM segmentpolygon AS p
    LEFT OUTER JOIN segment AS s USING (elementid)
WHERE ST_Contains(
        p.elementpolygon,
        {ego_translation}::geometry
    )
    AND NOT p.__RoadType__roadsection__
    AND p.location = {location}
GROUP BY p.elementid;
"""
)

POLYGON_DWITHIN_QUERY = psycopg2.sql.SQL(
    """
SELECT
    p.elementid,
    p.elementpolygon,
    p.segmenttypes,
    ARRAY_AGG(s.segmentline)::geometry[],
    ARRAY_AGG(s.heading)::real[],
    COUNT(DISTINCT p.elementpolygon),
    COUNT(DISTINCT p.segmenttypes)
FROM segmentpolygon AS p
    LEFT OUTER JOIN segment AS s USING (elementid)
WHERE ST_DWithin(
        p.elementpolygon,
        {start_segment}::geometry,
        {view_distance}
    )
    AND NOT p.__RoadType__roadsection__
    AND p.location = {location}
GROUP BY p.elementid;
"""
)


class RoadSegmentWithHeading(NamedTuple):
    id: "str"
    polygon: "postgis.Polygon"
    road_types: "list[str]"
    segmentline: "list[shapely.geometry.LineString]"
    heading: "list[float]"


class Segment(NamedTuple):
    id: "str"
    polygon: "postgis.Polygon"
    road_type: "str"
    segmentline: "list[shapely.geometry.LineString]"
    heading: "list[float]"


class AnnotatedSegment(NamedTuple):
    id: "str"
    polygon: "postgis.Polygon"
    road_type: "str"
    segmentline: "list[shapely.geometry.LineString]"
    heading: "list[float]"
    contain: "bool"


class SegmentLine(NamedTuple):
    line: "shapely.geometry.LineString"
    heading: "float"


@dataclass
class RoadPolygonInfo:
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
    polygon: "shapely.geometry.Polygon"
    segment_lines: "list[shapely.geometry.LineString]"
    road_type: str
    segment_headings: "list[float]"
    contains_ego: bool
    ego_config: "CameraConfig"
    fov_lines: "Tuple[Float22, Float22]"

    def __post_init__(self):
        if len(self.segment_lines) == 0:
            return

        start_segment_map: "dict[Float2, Tuple[shapely.geometry.LineString, float]]" = {}
        ends: "set[Float2]" = set()
        for line, heading in zip(self.segment_lines, self.segment_headings):
            start = line.coords[0]
            end = line.coords[1]
            start_segment_map[start] = (line, heading)
            ends.add(end)

        starts: "list[Float2]" = [start for start in start_segment_map if start not in ends]
        assert len(starts) == 1, len(starts)

        sorted_lines: "list[shapely.geometry.LineString]" = []
        sorted_headings: "list[float]" = []
        start: "Float2" = starts[0]
        while start in start_segment_map:
            line, heading = start_segment_map[start]
            sorted_lines.append(line)
            sorted_headings.append(heading)

            start: "Float2" = line.coords[1]

        self.segment_lines = sorted_lines
        self.segment_headings = sorted_headings


class CameraPolygonMapping(NamedTuple):
    cam_segment: "list[npt.NDArray[np.floating]]"
    road_polygon_info: "RoadPolygonInfo"


def hex_str_to_linestring(hex: "str"):
    return shapely.geometry.LineString(shapely.wkb.loads(bytes.fromhex(hex)))


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


def road_polygon_contains(ego_config: "CameraConfig") -> "list[RoadSegmentWithHeading]":
    point = postgis.Point(*ego_config.ego_translation[:2])
    query = POLYGON_CONTAIN_QUERY.format(
        ego_translation=psycopg2.sql.Literal(point),
        location=psycopg2.sql.Literal(ego_config.location),
    )

    results = database.execute(query)
    assert all(r[5:] == (1, 1) for r in results)

    output = [*map(make_road_polygon_with_heading, results)]
    assert len(output) > 0
    for row in output:
        types, line, heading = row[2:5]
        assert line is not None
        assert types is not None
        assert heading is not None
    return output


def find_polygon_dwithin(
    start_segment: "AnnotatedSegment", ego_config: "CameraConfig", view_distance: "float | int" = 50
) -> "list[RoadSegmentWithHeading]":
    _, start_segment_polygon, _, _, _, _ = start_segment
    query = POLYGON_DWITHIN_QUERY.format(
        start_segment=psycopg2.sql.Literal(start_segment_polygon),
        view_distance=psycopg2.sql.Literal(view_distance),
        location=psycopg2.sql.Literal(ego_config.location),
    )

    results = database.execute(query)
    assert all(r[5:] == (1, 1) for r in results)

    output = [*map(make_road_polygon_with_heading, results)]
    for row in output:
        types, line, heading = row[2:5]
        assert line is not None
        assert types is not None
        assert heading is not None
    return output


def reformat_return_polygon(segments: "list[RoadSegmentWithHeading]") -> "list[Segment]":
    def _(x: "RoadSegmentWithHeading") -> "Segment":
        i, polygon, types, lines, headings = x
        return Segment(
            i,
            polygon,
            # TODO: fix this hack: all the useful types are 'lane', 'lanegroup',
            # 'intersection' which are always at the last position
            types[-1],
            lines,
            [*map(math.degrees, headings)],
        )

    return list(map(_, segments))


def annotate_contain(segments: "list[Segment]", contain: bool = False) -> "list[AnnotatedSegment]":
    return [AnnotatedSegment(*s, contain) for s in segments]


def construct_search_space(
    ego_config: "CameraConfig", view_distance: float = 50.0
) -> "list[AnnotatedSegment]":
    """
    ego_config: current config of a camera
    view_distance: in meters, default 50 because scenic standard
    return: set(road_polygon)
    """
    all_contain_polygons = reformat_return_polygon(road_polygon_contains(ego_config))
    all_contain_polygons = annotate_contain(all_contain_polygons, contain=True)
    start_segment = all_contain_polygons[0]

    polygons_within_distance = reformat_return_polygon(
        find_polygon_dwithin(start_segment, ego_config, view_distance)
    )
    polygons_within_distance = annotate_contain(polygons_within_distance, contain=False)

    ids: "set[str]" = set()
    polygons: "list[AnnotatedSegment]" = []
    for p in all_contain_polygons + polygons_within_distance:
        if p.id not in ids:
            ids.add(p.id)
            polygons.append(p)

    assert any(p.contain for p in polygons)
    return polygons


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


def intersection(fov_line: Tuple[Float22, Float22], segmentpolygon: "shapely.geometry.Polygon"):
    """
    return: intersection point: tuple[tuple]
    """
    left_fov_line, right_fov_line = fov_line
    left_intersection = line_to_polygon_intersection(segmentpolygon, left_fov_line)
    right_intersection = line_to_polygon_intersection(segmentpolygon, right_fov_line)
    return left_intersection + right_intersection


def in_frame(transformed_point: "npt.NDArray", frame_size: Tuple[int, int]):
    return (
        transformed_point[0] > 0
        and transformed_point[0] < frame_size[0]
        and transformed_point[1] < frame_size[1]
        and transformed_point[1] > 0
    )


def in_view(
    road_point: "Float2", ego_translation: "Float3", fov_lines: Tuple[Float22, Float22]
) -> bool:
    """
    return if the road_point is on the left of the left fov line and
                                on the right of the right fov line
    """
    left_fov_line, right_fov_line = fov_lines
    Ax, Ay = ego_translation[:2]
    Mx, My = road_point
    left_fov_line_x, left_fov_line_y = left_fov_line[1]
    right_fov_line_x, right_fov_line_y = right_fov_line[1]
    return (left_fov_line_x - Ax) * (My - Ay) - (left_fov_line_y - Ay) * (Mx - Ax) <= 0 and (
        right_fov_line_x - Ax
    ) * (My - Ay) - (right_fov_line_y - Ay) * (Mx - Ax) >= 0


def world2pixel_factory(config: "CameraConfig"):
    def world2pixel(point3d: "Float2") -> "npt.NDArray[np.floating]":
        point = np.copy((*point3d, 0))

        point -= config.camera_translation
        point = np.dot(config.camera_rotation.inverse.rotation_matrix, point)

        view = np.array(config.camera_intrinsic)
        viewpad = np.eye(4)
        viewpad[: view.shape[0], : view.shape[1]] = view

        point = point.reshape((3, 1))
        point = np.concatenate((point, np.ones((1, 1))))
        point = np.dot(viewpad, point)
        point = point[:3, :]

        point = point / point[2:3, :].repeat(3, 0).reshape(3, 1)
        return point[:2, :]

    return world2pixel


def world2pixel_all(points3d: "list[Float2]", config: "CameraConfig"):
    n = len(points3d)
    points = np.concatenate([np.array(points3d), np.zeros((n, 1))], axis=1)
    assert points.shape == (n, 3)
    points -= config.camera_translation
    assert points.shape == (n, 3)
    points = config.camera_rotation.inverse.rotation_matrix @ points.T
    assert points.shape == (3, n)

    intrinsic = np.array(config.camera_intrinsic)
    assert intrinsic.shape == (3, 3), intrinsic.shape

    points = intrinsic @ points
    assert points.shape == (3, n)

    points = points / points[2:3, :]
    return points.T[:, :2]


def construct_mapping(
    decoded_road_polygon_points: "list[Float2]",
    frame_size: Tuple[int, int],
    fov_lines: Tuple[Float22, Float22],
    segmentid: str,
    segmentlines: "list[shapely.geometry.LineString]",
    segmenttype: str,
    segmentheadings: "list[float]",
    contains_ego: bool,
    ego_config: "CameraConfig",
) -> "CameraPolygonMapping | None":
    """
    Given current road segment
    determine whether add it to the mapping
     - segment that contains the ego
     - segment that is larger than 100 pixel x pixel
    """
    if segmenttype is None or segmenttype == "None":
        return

    ego_translation = ego_config.ego_translation

    # deduced_cam_segment = list(map(worl2pixel_factory(ego_config), decoded_road_segment))
    deduced_cam_polygon_points = world2pixel_all(decoded_road_polygon_points, ego_config)
    # assert np.allclose(np.array(deduced_cam_segment).reshape((len(decoded_road_segment), 2)), deduced_cam_segment2)
    assert len(deduced_cam_polygon_points) == len(decoded_road_polygon_points)
    if contains_ego:
        keep_cam_polygon_points = deduced_cam_polygon_points
        keep_road_polygon_points = decoded_road_polygon_points
    else:
        keep_cam_polygon_points: "list[npt.NDArray[np.floating]]" = []
        keep_road_polygon_points: "list[Float2]" = []
        for current_cam_point, current_road_point in zip(
            deduced_cam_polygon_points, decoded_road_polygon_points
        ):
            if in_frame(current_cam_point, frame_size) and in_view(
                current_road_point, ego_translation, fov_lines
            ):
                keep_cam_polygon_points.append(current_cam_point)
                keep_road_polygon_points.append(current_road_point)
    ret = None
    if contains_ego or (
        len(keep_cam_polygon_points) > 2
        and shapely.geometry.Polygon(tuple(keep_cam_polygon_points)).area > 100
    ):
        ret = CameraPolygonMapping(
            keep_cam_polygon_points,
            RoadPolygonInfo(
                segmentid,
                shapely.geometry.Polygon(keep_road_polygon_points),
                segmentlines,
                segmenttype,
                segmentheadings,
                contains_ego,
                ego_config,
                fov_lines,
            ),
        )
    return ret


def map_imgsegment_roadsegment(
    ego_config: "CameraConfig", frame_size: "Tuple[int, int]" = (1600, 900)
) -> "list[CameraPolygonMapping]":
    """Construct a mapping from frame segment to road segment

    Given an image, we know that different roads/lanes belong to different
    road segment in the road network. We want to find a mapping
    from the road/lane/intersection to the real world road segment so that
    we know which part of the image belong to which part of the real world

    Return List[namedtuple(cam_segment_mapping)]: each tuple looks like this
    (polygon in frame that represents a portion of lane/road/intersection,
     roadSegmentInfo)
    """
    fov_lines = get_fov_lines(ego_config)
    start_time = time.time()
    search_space = construct_search_space(ego_config, view_distance=100)
    mapping: "dict[str, CameraPolygonMapping]" = dict()

    def not_in_view(point: "Float2"):
        return not in_view(point, ego_config.ego_translation, fov_lines)

    for road_polygon in search_space:
        polygonid, roadpolygon, roadtype, segmentlines, segmentheadings, contains_ego = road_polygon
        assert segmentlines is not None
        assert segmentheadings is not None

        assert all(isinstance(line, shapely.geometry.LineString) for line in segmentlines)

        p = plpygis.Geometry(roadpolygon.to_ewkb())
        assert isinstance(p, plpygis.Polygon)
        XYs: "Tuple[array.array[float], array.array[float]]" = p.exterior.shapely.xy
        assert isinstance(XYs, tuple)
        assert isinstance(XYs[0], array.array), type(XYs[0])
        assert isinstance(XYs[1], array.array), type(XYs[1])
        assert isinstance(XYs[0][0], float), type(XYs[0][0])
        assert isinstance(XYs[1][0], float), type(XYs[1][0])
        polygon_points = list(zip(*XYs))
        roadpolygon = shapely.geometry.Polygon(polygon_points)

        decoded_road_polygon_points = polygon_points
        if not contains_ego:
            if all(map(not_in_view, polygon_points)):
                continue

            intersection_points = intersection(fov_lines, roadpolygon)
            decoded_road_polygon_points += intersection_points

        current_mapping = construct_mapping(
            decoded_road_polygon_points,
            frame_size,
            fov_lines,
            polygonid,
            segmentlines,
            roadtype,
            segmentheadings,
            contains_ego,
            ego_config,
        )

        if current_mapping is not None:
            mapping[polygonid] = current_mapping

    logger.info(f"total mapping time: {time.time() - start_time}")
    return [*mapping.values()]


# def visualization(test_img_path: str, test_config: Dict[str, Any], mapping: Tuple):
#     """
#     visualize the mapping from camera segment to road segment
#     for testing only
#     """
#     from moviepy.editor import VideoClip
#     from moviepy.video.io.bindings import mplfig_to_npimage
#     frame = cv2.imread(test_img_path)
#     fig, axs = plt.subplots()
#     axs.set_aspect('equal', 'datalim')
#     x_ego, y_ego = test_config['egoTranslation'][:2]
#     axs.plot(x_ego, y_ego, color='green', marker='o', markersize=5)
#     colormap = plt.cm.get_cmap('hsv', len(mapping))
#     i = 0
#     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#     display_video = cv2.VideoWriter('in_videw_test_display.avi',fourcc, 1, (1600, 900))
#     for cam_segment, road_segment_info in mapping:
#         color = colormap(i)
#         xs = [point[0] for point in road_segment_info.segment_polygon.exterior.coords]
#         ys = [point[1] for point in road_segment_info.segment_polygon.exterior.coords]
#         segmenttype = road_segment_info.segment_type
#         axs.fill(xs, ys, alpha=0.5, fc=color, ec='none')
#         axs.text(np.mean(np.array(xs)), np.mean(np.array(ys)),
#                 segmenttype if segmenttype else '')
#         current_plt = mplfig_to_npimage(fig)
#         i += 1

#         fov_lines = road_segment_info.fov_lines
#         axs.plot([p[0] for p in fov_lines[0]], [p[1] for p in fov_lines[0]], color='red', marker='o', markersize=2)
#         axs.plot([p[0] for p in fov_lines[1]], [p[1] for p in fov_lines[1]], color='red', marker='o', markersize=2)

#         display_frame = frame.copy()
#         cv2.polylines(display_frame, [np.array(cam_segment, np.int32).reshape((-1, 1, 2))], True, (0, 255, 0), 2)
#         display_frame[:current_plt.shape[0], :current_plt.shape[1]] = current_plt
#         display_video.write(display_frame)

#     display_video.release()

# if __name__ == '__main__':
#     test_img_path = os.path.join(data_path, test_img)
#     test_config = fetch_camera_config(
#         test_img,
#         database)
#     test_config = camera_config(**test_config)
#     mapping = map_imgsegment_roadsegment(test_config)
#     visualization(test_img_path, test_config, mapping)
