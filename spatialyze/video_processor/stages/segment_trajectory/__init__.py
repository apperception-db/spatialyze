import datetime
from dataclasses import dataclass
from typing import Any, Dict, NamedTuple, Union

import postgis
import shapely.geometry as sg

from ...types import DetectionId, Float3
from ..detection_estimation.segment_mapping import RoadPolygonInfo
from ..stage import Stage


class PolygonAndId(NamedTuple):
    id: "str"
    polygon: "sg.Polygon"


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


SegmentTrajectoryMetadatum = Dict[int, SegmentPoint]


class SegmentTrajectory(Stage[SegmentTrajectoryMetadatum]):
    @classmethod
    def encode_json(cls, o: "Any"):
        if isinstance(o, ValidSegmentPoint):
            return {
                "detection_id": tuple(o.detection_id),
                "car_loc3d": o.car_loc3d,
                "timestamp": str(o.timestamp),
                "segment_line": None if o.segment_line is None else o.segment_line.to_ewkb(),
                # "segment_line_wkb": o.segment_line.wkb_hex,
                "segment_heading": o.segment_heading,
                "road_polygon_info": o.road_polygon_info,
                "obj_id": o.obj_id,
                "type": o.type,
                "next": None if o.next is None else tuple(o.next.detection_id),
                "prev": None if o.prev is None else tuple(o.prev.detection_id),
            }
        if isinstance(o, InvalidSegmentPoint):
            return {
                "detection_id": tuple(o.detection_id),
                "car_loc3d": o.car_loc3d,
                "timestamp": str(o.timestamp),
                "obj_id": o.obj_id,
                "type": o.type,
                "next": None if o.next is None else tuple(o.next.detection_id),
                "prev": None if o.prev is None else tuple(o.prev.detection_id),
            }
        if isinstance(o, RoadPolygonInfo):
            return {
                "id": o.id,
                "polygon": str(o.polygon),
                # "polygon_wkb": o.polygon.wkb_hex,
                "segment_lines": [*map(str, o.segment_lines)],
                "road_type": o.road_type,
                "segment_headings": o.segment_headings,
                "contains_ego": o.contains_ego,
                "ego_config": o.ego_config,
                "fov_lines": o.fov_lines,
            }

        if isinstance(o, PolygonAndId):
            return {
                "id": o.id,
                "polygon": str(o.polygon),
            }
