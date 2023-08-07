""" Goal to map the road segment to the frame segment
    Now only get the segment of type lane and intersection
    except for the segment that contains the ego camera

Usage example:
    from optimization_playground.segment_mapping import map_imgsegment_roadsegment
    from apperception.utils import fetch_camera_config

    test_config = fetch_camera_config(test_img, database)
    mapping = map_imgsegment_roadsegment(test_config)
"""

import array
import logging
import math
import os
import sys
import time
from typing import Any, Dict, List, NamedTuple, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
import postgis
import psycopg2
from plpygis import Geometry
from shapely.geometry import LineString, Polygon

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir, os.pardir)))
from ...camera_config_copy import CameraConfig, camera_config

# from pyquaternion import Quaternion
pd.get_option("display.max_columns")

from apperception.database import database
from apperception.utils import fetch_camera_config
from utils import line_to_polygon_intersection

logger = logging.getLogger(__name__)

data_path = "/work/apperception/data/raw/nuScenes/full-dataset-v1.0/Mini"
test_img = "samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657120612404.jpg"

# MOCK_TRAJECTORY_1 = [(298.8204497922415, 682.4423743486885), (299.01599470019426, 681.809949218556), (298.84759481366257, 681.85149661344), (298.6919255951989, 681.6866275986694), (298.60381011120813, 681.4493967920732), (298.42896747734795, 681.3603075471352), (298.2936272334375, 681.2875447204339), (298.2792960009025, 680.9857008407138), (298.1676737409123, 680.9061962779896), (298.1963681137194, 680.5110190170635), (297.9270259545102, 680.5305590579048), (297.9031450004973, 680.3688164288551), (297.74679045690846, 679.8231511807479), (297.312683057346, 679.5672499076597), (296.933810981047, 679.559164703847), (296.49426098416717, 679.2710874319289), (295.6211840094654, 679.1856025584883), (295.61063284014233, 678.9014764997723), (294.8472961085618, 678.7154868443403), (294.40778126511043, 678.3218983931034), (294.10961113699153, 678.1424142651194), (293.84414071495934, 677.6865118519075), (292.9714994761993, 678.0922683477786), (292.62945183058844, 678.047430904155), (292.3347257021459, 678.0398718089325), (291.97349677954986, 677.8375487641749), (288.7943909540342, 674.3797060521931), (288.6113929720154, 674.6248752054382), (289.11977818175427, 674.4098887148981), (288.96542335632887, 674.1376215374632), (288.85207228797594, 673.8924856708603), (287.9946531852927, 673.5190807589261), (287.00766142159915, 673.0709557446194), (287.3442435674221, 672.7352650093495), (286.41801748679586, 672.3197481934112), (286.0137550019988, 671.6940659773), (285.32366514459494, 671.4348843237848), (284.4664262140017, 671.0763391220203), (283.8370665096726, 670.8599487379197), (283.32577928633947, 670.7254535578525), (281.9396942549785, 670.4962652789942), (281.0218403008221, 670.1541167331719), (279.09368203637484, 668.0403705609059), (278.91850157230994, 667.9262445841136), (278.91753775149573, 667.698395307403), (277.8243164296866, 667.2447373639897), (277.18794086906803, 667.0793728275644), (277.1006503756107, 666.7804427390524), (274.5655869871619, 666.2287707443397), (273.71155807767013, 665.9773128095453), (272.69810030431734, 665.6503421281109)]
# MOCK_TRAJECTORY_1 = [(297.31, 679.57)]
MOCK_TRAJECTORY_1 = [
    (283.0846066442669, 666.7491273579125),
    (285.172896432793, 667.3038603361285),
    (285.6108780172807, 667.4816783130578),
    (286.49231848729215, 667.8555318810955),
    (286.69873408200885, 668.1557005634678),
    (286.7617734958426, 668.3446583223605),
    (287.75997918450804, 668.6727805588818),
    (288.32674979865317, 669.1139685639446),
    (288.7870219205495, 669.4723289966488),
    (289.33505400698033, 670.0422566701948),
    (290.0360237030085, 670.5852782887335),
    (290.62674451555125, 670.9126038126167),
    (291.11704157755133, 671.4289645524376),
    (291.64552685759844, 671.9710014355088),
    (292.0976260152118, 672.1924095331576),
    (292.63248887319617, 672.731433281764),
    (293.51859303073593, 673.1853287882683),
    (293.39652752177375, 673.5675115914381),
    (294.11481695395264, 674.0023711893672),
    (294.7081375389355, 674.46143835816),
    (295.09236330112896, 674.6479405591296),
    (295.6775535942427, 675.1078831818027),
    (296.1442299254093, 675.5772944619898),
    (296.4367590687299, 675.7935008132264),
    (296.98141357738336, 676.2140190500216),
    (297.50015259460827, 676.6209191360615),
    (297.77507763274656, 676.8293630555318),
    (298.05147755824004, 677.3445639128774),
    (298.62927259499463, 677.5957762726077),
    (298.8549349741779, 677.9629937846075),
    (299.2451216171339, 678.3526666318148),
    (299.7266493791718, 678.7050339080585),
    (299.8578164297705, 678.8966794448899),
    (300.007765482301, 679.1142470556196),
    (300.2842760723128, 679.2194852575636),
    (300.3830088096315, 679.2876952100654),
    (300.6268683857484, 679.3898072086934),
    (300.17824696644306, 680.5210956148387),
    (299.78409993939874, 681.351686684353),
    (299.8011120576228, 681.699853465654),
    (287.08564229362344, 673.0073214932926),
    (286.2671291994167, 672.2976610775422),
    (281.1492066279918, 666.7140135468263),
    (281.02454404579873, 666.4158229224672),
]
# MOCK_TRAJECTORY_2 = [(282.9198062410776, 666.8771682241056), (284.82963010644744, 667.3685658356914), (286.77025240171463, 667.8136039571395), (286.8415711739299, 667.9670526295672), (287.02206073763307, 668.2051947116763), (287.67476602070843, 668.5298403313111), (287.93440944460036, 668.7116001253639), (288.8486777007578, 669.0522740063348), (288.8489708146264, 669.3348655452115), (289.6817801221807, 669.564602432988), (289.93378389470126, 670.1310806226695), (290.9137638496881, 670.6745284760257), (291.1209884777474, 670.9706783315573), (291.46541877260984, 671.1166974068747)]
# MOCK_TRAJECTORY_2 = [(288.85, 669.33,)]
MOCK_TRAJECTORY_2 = [
    (298.63457985964493, 681.767738325874),
    (298.2382593594731, 681.2722349144998),
    (298.3039282879353, 680.9238801074249),
    (297.6293759465963, 680.7990400168155),
    (297.1944988936091, 680.2758597213607),
    (297.0627254905734, 680.1894140902444),
    (296.6016402400178, 680.3271301974929),
    (296.2998082299628, 680.1496631473874),
    (293.9346735159379, 678.593169987175),
    (293.8356598335076, 678.2343003460653),
    (293.41934652178776, 678.1410114143184),
    (292.99794806485886, 677.565048635977),
    (292.2810387002316, 677.1262247046877),
    (291.527286650631, 677.0116614549413),
    (290.1083316317138, 675.986276421192),
    (288.3807663609664, 674.5653261034836),
    (288.1401162244675, 674.2312819842657),
    (287.264766202083, 673.6911847346877),
    (286.6788095262505, 673.1260958921275),
    (285.899106808267, 672.077772083972),
    (285.032833143835, 671.521062758076),
    (284.8763784447907, 671.2255417540454),
    (284.49054852461546, 670.5726813821084),
    (283.8683540473013, 669.9580284054523),
    (283.6303330766203, 669.6013834258588),
    (282.34977543060177, 668.9386741157831),
    (281.7512921433899, 668.328294226094),
    (281.11403486591996, 668.1135729672671),
    (280.61957617954664, 667.8012709672904),
    (280.0421201249558, 667.4168029870596),
    (278.7340459957884, 667.451875402771),
    (286.296485069503, 667.7184843732431),
    (287.3393035121849, 668.2484634407851),
    (287.7642995690597, 668.5847349908024),
    (288.3413290666149, 668.7588743343475),
    (289.32515639606646, 669.8266097072657),
    (289.5682065713635, 670.157956378832),
    (291.35631318481023, 671.3196672951502),
    (291.5771823146549, 671.6266175304976),
    (292.9646614036655, 673.0961976714054),
    (293.63206145801774, 673.6087375026345),
    (294.3252749134875, 674.1582064034811),
    (294.70264974063696, 674.3369314828236),
    (295.3141715168099, 674.824857526736),
    (295.83724784828956, 675.3493689155653),
]


SegmentPolygonWithHeading = Tuple[
    str,
    postgis.polygon.Polygon,
    postgis.linestring.LineString,
    Union[List[str], None],
    Union[float, None],
]

SINGLE_SEGMENT_QUERY = """
select
    segmentpolygon.elementid,
    segmentpolygon.elementpolygon,
    segment.segmentline,
    segmentpolygon.segmenttypes,
    segment.heading
from segmentpolygon
left outer join segment on segmentpolygon.elementid = segment.elementid
where segmentpolygon.elementid = '{segmentid}';
"""

SEGMENT_CONTAIN_QUERY = """
SELECT
    segmentpolygon.elementid,
    segmentpolygon.elementpolygon,
    segment.segmentline,
    segmentpolygon.segmenttypes,
    segment.heading
FROM segmentpolygon
    LEFT OUTER JOIN segment
        ON segmentpolygon.elementid = segment.elementid
WHERE ST_Contains(
    segmentpolygon.elementpolygon,
    {ego_translation}::geometry
);
"""

SEGMENT_DWITHIN_QUERY = """
SELECT
    segmentpolygon.elementid,
    segmentpolygon.elementpolygon,
    segment.segmentline,
    segmentpolygon.segmenttypes,
    segment.heading
FROM segmentpolygon
    LEFT OUTER JOIN segment
        ON segmentpolygon.elementid = segment.elementid
WHERE ST_DWithin(
        elementpolygon,
        {start_segment}::geometry,
        {view_distance}
    ) AND
    segmentpolygon.segmenttypes in (
        ARRAY[\'lane\'],
        ARRAY[\'intersection\'],
        ARRAY[\'laneSection\'],
    );"""

SEGMENT_DWITHIN_QUERY_NO_TYPE_CONSTRAINT = """
SELECT
    segmentpolygon.elementid,
    segmentpolygon.elementpolygon,
    segment.segmentline,
    segmentpolygon.segmenttypes,
    segment.heading
FROM segmentpolygon
    LEFT OUTER JOIN segment
        ON segmentpolygon.elementid = segment.elementid
WHERE ST_DWithin(
        elementpolygon,
        {start_segment}::geometry,
        {view_distance}
    );"""

Float2 = Tuple[float, float]
Float3 = Tuple[float, float, float]
Float22 = Tuple[Float2, Float2]
Segment = Tuple[
    str,
    postgis.polygon.Polygon,
    postgis.linestring.LineString,
    Union[str, None],
    Union[float, None],
]
AnnotatedSegment = Tuple[str, postgis.polygon.Polygon, Union[str, None], Union[float, None], bool]


class RoadSegmentInfo(NamedTuple):
    """
    segment_id: unique segment id
    segment_polygon: tuple of (x, y) coordinates
    segment_line: list of tuple of (x, y) coordinates
    segment_type: road segment type
    segment_headings: list of floats
    contains_ego: whether the segment contains ego camera
    ego_config: ego camfig for the frame we asks info for
    fov_lines: field of view lines
    """

    segment_id: int
    segment_polygon: Polygon
    segment_lines: List[Union[LineString, None]]
    segment_type: str
    segment_headings: List[float]
    contains_ego: bool
    ego_config: "CameraConfig"
    fov_lines: "Tuple[Float22, Float22]"


# CameraSegmentMapping = namedtuple('cam_segment_mapping', ['cam_segment', 'road_segment_info'])
class CameraSegmentMapping(NamedTuple):
    cam_segment: "List[npt.NDArray[np.floating]]"
    road_segment_info: "RoadSegmentInfo"


def road_segment_contains(ego_config: "CameraConfig") -> List[SegmentPolygonWithHeading]:
    query = psycopg2.sql.SQL(SEGMENT_CONTAIN_QUERY).format(
        ego_translation=psycopg2.sql.Literal(postgis.point.Point(*ego_config.ego_translation[:2]))
    )

    return database.execute(query)


def find_segment_dwithin(
    start_segment: "AnnotatedSegment", view_distance=100
) -> "List[SegmentPolygonWithHeading]":
    _, start_segment_polygon, _, _, _, _ = start_segment
    query = psycopg2.sql.SQL(SEGMENT_DWITHIN_QUERY_NO_TYPE_CONSTRAINT).format(
        start_segment=psycopg2.sql.Literal(start_segment_polygon),
        view_distance=psycopg2.sql.Literal(view_distance),
    )

    return database.execute(query)


def reformat_return_segment(segments: "List[SegmentPolygonWithHeading]") -> "List[Segment]":
    def _(x: "SegmentPolygonWithHeading") -> Segment:
        i, polygon, line, types, heading = x
        return (
            i,
            polygon,
            line,
            types[0] if types is not None else None,
            math.degrees(heading) if heading is not None else None,
        )

    return list(map(_, segments))


def annotate_contain(segments: "List[Segment]", contain: bool = False) -> "List[AnnotatedSegment]":
    return [s + (contain,) for s in segments]


class HashableAnnotatedSegment:
    val: "AnnotatedSegment"

    def __init__(self, val: "AnnotatedSegment"):
        self.val = val

    def __hash__(self):
        h1 = hash(self.val[0])
        h2 = hash(self.val[1].wkt_coords)
        h3 = hash(self.val[2].wkt_coords) if self.val[2] else ""
        # h4 = hash(self.val[3:])
        return hash((h1, h2, h3))

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HashableAnnotatedSegment):
            return False
        return self.val == __o.val


def construct_search_space(
    ego_config: "CameraConfig", view_distance: float = 50.0
) -> "List[AnnotatedSegment]":
    """
    road segment: (elementid, elementpolygon, segmenttype, heading, contains_ego?)
    view_distance: in meters, default 50 because scenic standard
    return: set(road_segment)
    """
    all_contain_segment = reformat_return_segment(road_segment_contains(ego_config))
    all_contain_segment = annotate_contain(all_contain_segment, contain=True)
    start_segment = all_contain_segment[0]

    segment_within_distance = reformat_return_segment(
        find_segment_dwithin(start_segment, view_distance)
    )
    segment_within_distance = annotate_contain(segment_within_distance, contain=False)

    return [
        s.val
        for s in {
            # To remove duplicates
            *map(HashableAnnotatedSegment, all_contain_segment),
            *map(HashableAnnotatedSegment, segment_within_distance),
        }
    ]


def get_fov_lines(ego_config: "CameraConfig", ego_fov: float = 70.0) -> Tuple[Float22, Float22]:
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


def intersection(fov_line: Tuple[Float22, Float22], segmentpolygon: Polygon):
    """
    return: intersection point: tuple[tuple]
    """
    left_fov_line, right_fov_line = fov_line
    left_intersection = line_to_polygon_intersection(segmentpolygon, left_fov_line)
    right_intersection = line_to_polygon_intersection(segmentpolygon, right_fov_line)
    return left_intersection + right_intersection


def in_frame(transformed_point: np.array, frame_size: Tuple[int, int]):
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

        point -= config.ego_translation
        point = np.dot(config.ego_rotation.inverse.rotation_matrix, point)

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


def construct_mapping(
    decoded_road_segment: "List[Float2]",
    frame_size: Tuple[int, int],
    fov_lines: Tuple[Float22, Float22],
    segmentid: str,
    segmentline: LineString,
    segmenttype: str,
    segmentheading: float,
    contains_ego: bool,
    ego_config: "CameraConfig",
) -> "Union[CameraSegmentMapping, None]":
    """
    Given current road segment
    determine whether add it to the mapping
     - segment that contains the ego
     - segment that is larger than 100 pixel x pixel
    """
    if segmenttype is None:
        return
    ego_translation = ego_config.ego_translation[:2]

    deduced_cam_segment = list(map(world2pixel_factory(ego_config), decoded_road_segment))
    assert len(deduced_cam_segment) == len(decoded_road_segment)
    if contains_ego:
        keep_cam_segment_point = deduced_cam_segment
        keep_road_segment_point = decoded_road_segment
    else:
        keep_cam_segment_point: "List[npt.NDArray[np.floating]]" = []
        keep_road_segment_point: "List[Float2]" = []
        for current_cam_point, current_road_point in zip(deduced_cam_segment, decoded_road_segment):
            if in_frame(current_cam_point, frame_size) and in_view(
                current_road_point, ego_translation, fov_lines
            ):
                keep_cam_segment_point.append(current_cam_point)
                keep_road_segment_point.append(current_road_point)

    if contains_ego or (
        len(keep_cam_segment_point) > 2 and Polygon(tuple(keep_cam_segment_point)).area > 200
    ):
        return CameraSegmentMapping(
            keep_cam_segment_point,
            RoadSegmentInfo(
                segmentid,
                Polygon(keep_road_segment_point),
                [segmentline],
                segmenttype,
                [segmentheading],
                contains_ego,
                ego_config,
                fov_lines,
            ),
        )


# def fix_segment_line(
#     fov_lines: Tuple[Float22, Float22],
#     road_segment_info: "RoadSegmentInfo",
#     frame_size: Tuple[int, int],):
#     assert (len(road_segment_info.segment_lines) ==
#             len(road_segment_info.segment_headings))
#     ego_config = road_segment_info.ego_config
#     ego_translation = ego_config.ego_translation[:2]
#     for i in range(len(road_segment_info.segment_lines)):
#         segment_line_points = tuple(road_segment_info.segment_lines[i].coords)
#         assert len(segment_line_points) == 2
#         transformed_segment_line_points = (world2pixel_factory(ego_config)(segment_line_points[0]),
#                                            world2pixel_factory(ego_config)(segment_line_points[1]))
#         in_views = [in_view(segment_line_points[0], ego_translation, fov_lines),
#                     in_view(segment_line_points[1], ego_translation, fov_lines)]
#         in_frames = [in_frame(transformed_segment_line_points[0], frame_size),
#                      in_frame(transformed_segment_line_points[1], frame_size)]
#         if not in_views[0] or not in_frames[0]:
#             if in_views[1] and in_frames[1]:


def map_imgsegment_roadsegment(
    ego_config: "CameraConfig", frame_size: "Tuple[int, int]" = (1600, 900)
) -> List[CameraSegmentMapping]:
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
    mapping = dict()

    def not_in_view(point: "Float2"):
        return not in_view(point, ego_config.ego_translation, fov_lines)

    count = 0
    for road_segment in search_space:
        (
            segmentid,
            segmentpolygon,
            segmentline,
            segmenttype,
            segmentheading,
            contains_ego,
        ) = road_segment
        segmentline = Geometry(segmentline.to_ewkb()).shapely if segmentline else None
        if segmentid in mapping:
            mapping[segmentid].road_segment_info.segment_lines.append(segmentline)
            mapping[segmentid].road_segment_info.segment_headings.append(segmentheading)
            continue
        XYs: "Tuple[array.array[float], array.array[float]]" = Geometry(
            segmentpolygon.to_ewkb()
        ).exterior.shapely.xy
        assert isinstance(XYs, tuple)
        assert isinstance(XYs[0], array.array), type(XYs[0])
        assert isinstance(XYs[1], array.array), type(XYs[1])
        assert isinstance(XYs[0][0], float), type(XYs[0][0])
        assert isinstance(XYs[1][0], float), type(XYs[1][0])
        segmentpolygon_points = list(zip(*XYs))
        segmentpolygon = Polygon(segmentpolygon_points)
        decoded_road_segment = segmentpolygon_points

        if not contains_ego:
            road_filter = all(map(not_in_view, segmentpolygon_points))
            if road_filter:
                count += 1
                continue

            intersection_points = intersection(fov_lines, segmentpolygon)
            decoded_road_segment += intersection_points

        current_mapping = construct_mapping(
            decoded_road_segment,
            frame_size,
            fov_lines,
            segmentid,
            segmentline,
            segmenttype,
            segmentheading,
            contains_ego,
            ego_config,
        )
        if current_mapping is not None:
            mapping[segmentid] = current_mapping

    print(f"total mapping time: {time.time() - start_time}")
    # for val in mapping.values():
    #     fix_segment_line(val.road_segment_info)
    return mapping.values()


def visualization(test_img_path: str, test_config: Dict[str, Any], mapping: Tuple):
    """
    visualize the mapping from camera segment to road segment
    for testing only
    """
    # frame = cv2.imread(test_img_path)
    fig, axs = plt.subplots()
    axs.set_aspect("equal", "datalim")
    x_ego, y_ego = test_config.ego_translation[:2]
    axs.plot(x_ego, y_ego, color="green", marker="o", markersize=5)
    colormap = plt.cm.get_cmap("hsv", len(mapping))
    i = 0
    mock_trajectory_1 = MOCK_TRAJECTORY_1
    [axs.plot(p[0], p[1], color="green", marker="o", markersize=5) for p in mock_trajectory_1]
    mock_trajectory_2 = MOCK_TRAJECTORY_2
    [axs.plot(p[0], p[1], color="red", marker="o", markersize=5) for p in mock_trajectory_2]
    lane_id = 0
    for _, road_segment_info in mapping:
        color = colormap(i)
        xs = [point[0] for point in road_segment_info.segment_polygon.exterior.coords]
        ys = [point[1] for point in road_segment_info.segment_polygon.exterior.coords]
        segmentid = road_segment_info.segment_id
        segmenttype = road_segment_info.segment_type
        segmentlines = road_segment_info.segment_lines
        print(segmentid, segmenttype + str(lane_id) if segmenttype is not None else "None")
        axs.fill(xs, ys, alpha=0.5, fc=color, ec="none")
        axs.text(np.mean(np.array(xs)), np.mean(np.array(ys)), segmenttype[0] + str(lane_id))
        lane_id += 1
        if segmentlines is not None:
            [
                axs.plot(
                    [p[0] for p in tuple(segmentline.coords)],
                    [p[1] for p in tuple(segmentline.coords)],
                    color="black",
                    marker="o",
                    markersize=2,
                )
                for segmentline in segmentlines
                if segmentline is not None
            ]
        i += 1

        fov_lines = road_segment_info.fov_lines
        axs.plot(
            [p[0] for p in fov_lines[0]],
            [p[1] for p in fov_lines[0]],
            color="red",
            marker="o",
            markersize=2,
        )
        axs.plot(
            [p[0] for p in fov_lines[1]],
            [p[1] for p in fov_lines[1]],
            color="red",
            marker="o",
            markersize=2,
        )


def visualize_single_segment(segmentids, road_segment_info=None):
    fig, axs = plt.subplots()
    axs.set_aspect("equal", "datalim")
    colormap = plt.cm.get_cmap("hsv", len(segmentids))
    i = 0
    for segmentid in segmentids:
        road_segment_info = None
        result = database.execute(SINGLE_SEGMENT_QUERY.format(segmentid=segmentid))
        if road_segment_info is None:
            for test_segment in result:
                segmentid, segmentpolygon, segmentline, segmenttype, segmentheading = test_segment
                segmentline = Geometry(segmentline.to_ewkb()).shapely if segmentline else None
                if road_segment_info is not None:
                    road_segment_info.segment_lines.append(segmentline)
                    road_segment_info.segment_headings.append(segmentheading)
                    continue
                segmentpolygon = Geometry(segmentpolygon.to_ewkb()).shapely
                road_segment_info = RoadSegmentInfo(
                    segmentid,
                    segmentpolygon,
                    [segmentline],
                    segmenttype,
                    [segmentheading],
                    None,
                    False,
                    None,
                )
        xs = [point[0] for point in road_segment_info.segment_polygon.exterior.coords]
        ys = [point[1] for point in road_segment_info.segment_polygon.exterior.coords]
        segmentid = road_segment_info.segment_id
        segmenttype = road_segment_info.segment_type
        segmentlines = road_segment_info.segment_lines
        print(segmentid, segmenttype)
        color = colormap(i)
        axs.fill(xs, ys, alpha=0.5, fc=color, ec="none")
        axs.text(np.mean(np.array(xs)), np.mean(np.array(ys)), segmenttype)
        if segmentlines is not None:
            [
                axs.plot(
                    [p[0] for p in tuple(segmentline.coords)],
                    [p[1] for p in tuple(segmentline.coords)],
                    color="black",
                    marker="o",
                    markersize=2,
                )
                for segmentline in segmentlines
                if segmentline is not None
            ]
        i += 1
    plt.show()


if __name__ == "__main__":
    test_img_path = os.path.join(data_path, test_img)
    test_config = fetch_camera_config(test_img, database)
    test_config = camera_config(**test_config)
    mapping = map_imgsegment_roadsegment(test_config)
