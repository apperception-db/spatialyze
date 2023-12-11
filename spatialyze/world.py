import numpy as np

from .data_types.camera import Camera
from .data_types.camera_config import CameraConfig as _CameraConfig
from .data_types.query_result import QueryResult
from .database import Database
from .database import database as default_database
from .geospatial_video import GeospatialVideo
from .predicate import BoolOpNode, CameraTableNode, ObjectTableNode, PredicateNode, lit
from .road_network import RoadNetwork
from .utils.F.road_segment import road_segment
from .utils.get_object_list import get_object_list
from .utils.save_video_util import save_video_util
from .video_processor.stages.decode_frame.decode_frame import DecodeFrame
from .video_processor.stages.tracking_2d.deepsort import DeepSORT
from .video_processor.stream.data_types import Skip
from .video_processor.stream.decode_frame import DecodeFrame
from .video_processor.stream.deepsort import DeepSORT, TrackingResult
from .video_processor.stream.exit_frame_sampler import ExitFrameSampler
from .video_processor.stream.from_detection_2d_and_depth import FromDetection2DAndDepth
from .video_processor.stream.from_detection_2d_and_road import FromDetection2DAndRoad
from .video_processor.stream.mono_depth_estimator import MonoDepthEstimator
from .video_processor.stream.object_type_pruner import ObjectTypePruner
from .video_processor.stream.prune_frames import PruneFrames

# stream
from .video_processor.stream.road_visibility_pruner import RoadVisibilityPruner
from .video_processor.stream.yolo import Yolo
from .video_processor.utils.insert_trajectory import insert_trajectory
from .video_processor.utils.prepare_trajectory import prepare_trajectory
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
        self._objects: "dict[str, list[QueryResult]] | None" = None
        self._trackings: "dict[str, list[list[TrackingResult]]] | None" = None
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
        self._objects, self._trackings = None, None
        return self

    def addVideo(self, video: "GeospatialVideo") -> "World":
        self._videos.append(video)
        self._objects, self._trackings = None, None
        return self

    def addGeogConstructs(self, geogConstructs: "RoadNetwork") -> "World":
        self._geogConstructs.append(geogConstructs)
        self._objects, self._trackings = None, None
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

    def saveVideos(self, outputDir: "str", addBoundingBoxes: "bool" = False):
        if self._objects is None or self._trackings is None:
            self._objects, self._trackings = _execute(self)
        return save_video_util(
            self._objects,
            self._trackings,
            outputDir,
            addBoundingBoxes,
        )

    def getObjects(self):
        """
        Returns a list of moveble objects, with each object tuple containing:
        - object id
        - object type
        - trajectory
        - bounding boxes
        - frame IDs
        - camera id
        """
        if self._objects is None or self._trackings is None:
            self._objects, self._trackings = _execute(self)

        return get_object_list(self._objects, self._trackings)


BATCH_SIZE = 2048


def _execute(world: "World", optimization=True):
    database = world._database

    # add geographic constructs
    # drop_tables(database)
    # create_tables(database)
    # for gc in world._geogConstructs:
    #     gc.ingest(database)

    qresults: dict[str, list[QueryResult]] = {}
    vresults: dict[str, list[list[TrackingResult]]] = {}
    for v in world._videos:
        # reset database
        database.reset()

        # analyze predicates to generate video processing plan
        inview = RoadVisibilityPruner(distance=50, predicate=world.predicates)
        decode0 = DecodeFrame()
        decode = PruneFrames(inview, decode0)
        d2ds = Yolo(decode)
        if optimization:
            d2ds = ObjectTypePruner(d2ds, predicate=world.predicates)
            d3ds = FromDetection2DAndRoad(d2ds)
            if all(t in ["car", "truck"] for t in d2ds.types):
                efs = ExitFrameSampler(d3ds)
                d3ds = PruneFrames(efs, d3ds)
        else:
            depths = MonoDepthEstimator(decode)
            d3ds = FromDetection2DAndDepth(d2ds, depths)
        t3ds = DeepSORT(d3ds, decode)

        # execute pipeline
        video = Video(v.video, v.camera)
        output = t3ds.iterate(video)

        tracks_batch: list[list[TrackingResult]] = []
        vresults[v.video] = []
        for track in output:
            assert not isinstance(track, Skip)
            vresults[v.video].append(track)
            if len(tracks_batch) < BATCH_SIZE:
                tracks_batch.append(track)
                continue
            _flush(tracks_batch, video, database)
            tracks_batch = []
        _flush(tracks_batch, video, database)

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
        database.insert_camera(camera)

        qresults[v.video] = database.predicate(world.predicates)
    return qresults, vresults


def _flush(tracks: list[list[TrackingResult]], video: Video, database: Database):
    for track in tracks:
        obj_id = track[0].object_id
        trajectory = prepare_trajectory(video.videofile, obj_id, track, video.camera_configs)
        if trajectory:
            (
                item_id,
                camera_id,
                object_type,
                timestamps,
                pairs,
                itemHeadings,
                translations,
            ) = trajectory
            insert_trajectory(
                database,
                item_id,
                camera_id,
                object_type,
                timestamps,
                pairs,
                itemHeadings,
                translations,
            )
