import numpy as np

from .data_types.camera import Camera
from .data_types.camera_config import CameraConfig as _CameraConfig
from .database import Database
from .database import database as default_database
from .geospatial_video import GeospatialVideo
from .predicate import BoolOpNode, CameraTableNode, ObjectTableNode, PredicateNode, lit
from .road_network import RoadNetwork
from .utils.F.road_segment import road_segment
from .video_processor.payload import Payload
from .video_processor.pipeline import Pipeline
from .video_processor.stages.decode_frame.decode_frame import DecodeFrame
from .video_processor.stages.depth_estimation import DepthEstimation
from .video_processor.stages.detection_2d.object_type_filter import ObjectTypeFilter
from .video_processor.stages.detection_2d.yolo_detection import YoloDetection
from .video_processor.stages.detection_3d.from_detection_2d_and_depth import (
    FromDetection2DAndDepth,
)
from .video_processor.stages.detection_3d.from_detection_2d_and_road import (
    FromDetection2DAndRoad,
)
from .video_processor.stages.detection_estimation import DetectionEstimation
from .video_processor.stages.in_view.in_view import InView
from .video_processor.stages.tracking_2d.strongsort import StrongSORT
from .video_processor.stages.tracking_3d.from_tracking_2d_and_depth import (
    FromTracking2DAndDepth,
)
from .video_processor.stages.tracking_3d.from_tracking_2d_and_road import (
    FromTracking2DAndRoad,
)
from .video_processor.stages.tracking_3d.tracking_3d import Metadatum as T3DMetadatum
from .video_processor.stages.tracking_3d.tracking_3d import Tracking3D
from .video_processor.utils.format_trajectory import format_trajectory
from .video_processor.utils.get_tracks import get_tracks
from .video_processor.utils.insert_trajectory import insert_trajectory
from .video_processor.video import Video


class World:
    def __init__(
        self,
        database: "Database | None" = None,
        predicates: "list[PredicateNode] | None" = None,
        videos: "list[GeospatialVideo] | None" = None,
        geogConstructs: "list[RoadNetwork] | None" = None,
    ):
        self._database = database or default_database
        self._predicates = predicates or []
        self._videos = videos or []
        self._geogConstructs = geogConstructs or []
        self._objectCounts = 0
        # self._cameraCounts = 0

    @property
    def predicates(self) -> "PredicateNode":
        if len(self._predicates) == 0:
            return lit(True)
        if len(self._predicates) == 1:
            return self._predicates[0]
        return BoolOpNode("and", self._predicates)

    def filter(self, predicate: "PredicateNode") -> "World":
        self._predicates.append(predicate)
        return self

    def addVideo(self, video: "GeospatialVideo") -> "World":
        self._videos.append(video)
        return self

    def addGeogConstructs(self, geogConstructs: "RoadNetwork") -> "World":
        self._geogConstructs.append(geogConstructs)
        return self

    def object(self, index: "int | None" = None):
        if index is not None:
            return ObjectTableNode(index)

        node = ObjectTableNode(self._objectCounts)
        self._objectCounts += 1
        return node

    def camera(self) -> "CameraTableNode":
        return CameraTableNode()

    def geogConstruct(self, type: "str"):
        return road_segment(type)

    def saveVideos(self, addBoundingBoxes: "bool" = False):
        # TODO: execute and save videos
        objects = _execute(self)
        return objects

    def getObjects(self):
        # TODO: execute and return movable objects
        # TODO: should always execute object tracker
        objects = _execute(self)
        return objects


def _execute(world: "World", optimization=True):
    database = world._database

    # add geographic constructs
    # drop_tables(database)
    # create_tables(database)
    # for gc in world._geogConstructs:
    #     gc.ingest(database)
    # analyze predicates to generate pipeline
    objtypes_filter = ObjectTypeFilter(predicate=world.predicates)
    if optimization:
        pipeline = Pipeline(
            [
                DecodeFrame(),
                InView(distance=50, predicate=world.predicates),
                YoloDetection(),
                objtypes_filter,
                FromDetection2DAndRoad(),
                *(
                    [DetectionEstimation()]
                    if all(t in ["car", "truck"] for t in objtypes_filter.types)
                    else []
                ),
                StrongSORT(),
                FromTracking2DAndRoad(),
            ]
        )
    else:
        pipeline = Pipeline(
            [
                DecodeFrame(),
                YoloDetection(),
                DepthEstimation(),
                FromDetection2DAndDepth(),
                StrongSORT(),
                FromTracking2DAndDepth(),
            ]
        )

    qresults: "dict[str, list[tuple]]" = {}
    vresults: "dict[str, list[T3DMetadatum]]" = {}
    for v in world._videos:
        # reset database
        database.reset()

        # execute pipeline
        video = Video(v.video, v.camera)
        keep = v.keep
        output = pipeline.run(Payload(video, keep))
        track_result = StrongSORT.get(output)
        assert track_result is not None
        tracking3d = Tracking3D.get(output)
        assert tracking3d is not None
        vresults[v.video] = tracking3d
        tracks = get_tracks(tracking3d, v.camera)

        for oid, track in tracks.items():
            trajectory = format_trajectory("", oid, track)
            if trajectory:
                insert_trajectory(database, *trajectory[0])

        _camera_configs: "list[_CameraConfig]" = [
            _CameraConfig(
                frame_id=cc.frame_id or str(idx),
                frame_num=idx,
                filename=cc.filename or "",
                camera_translation=np.array(cc.camera_translation),
                camera_rotation=np.array(cc.camera_rotation.q),
                camera_intrinsic=cc.camera_intrinsic,
                ego_translation=cc.ego_translation,
                ego_rotation=[*cc.ego_rotation.q],
                timestamp=str(cc.timestamp),
                cameraHeading=cc.camera_heading,
                egoHeading=cc.ego_heading,
            )
            for idx, cc in enumerate(v.camera)
        ]

        camera = Camera(_camera_configs, v.camera[0].camera_id)
        database.insert_cam(camera)

        qresults[v.video] = database.predicate(world.predicates)
    return qresults, vresults
