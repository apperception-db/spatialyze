import time

from ...database import database
from ..payload import Payload
from ..pipeline import Pipeline
from ..stages.decode_frame.parallel_decode_frame import ParallelDecodeFrame
from ..stages.detection_2d.yolo_detection import YoloDetection
from ..stages.detection_3d.from_detection_2d_and_road import FromDetection2DAndRoad
from ..stages.detection_estimation import DetectionEstimation
from ..stages.segment_trajectory.from_tracking_3d import FromTracking3D
from ..stages.tracking_2d.strongsort import StrongSORT
from ..stages.tracking_3d.from_tracking_2d_and_road import (
    FromTracking2DAndRoad as From2DAndRoad_3d,
)
from ..video.video import Video
from .format_trajectory import format_trajectory
from .get_tracks import get_tracks
from .insert_trajectory import insert_trajectory
from .query_analyzer import PipelineConstructor


def construct_base_pipeline():
    pipeline = Pipeline()
    pipeline.add_filter(filter=ParallelDecodeFrame())
    pipeline.add_filter(filter=YoloDetection())

    pipeline.add_filter(filter=FromDetection2DAndRoad())
    pipeline.add_filter(filter=StrongSORT())  # 2 Frame p Second
    pipeline.add_filter(filter=From2DAndRoad_3d())
    pipeline.add_filter(filter=FromTracking3D())

    return pipeline


def construct_pipeline(world, base):
    pipeline = construct_base_pipeline()
    if base:
        return pipeline
    pipeline.stages.insert(3, DetectionEstimation())
    if world.kwargs.get("predicate"):
        PipelineConstructor().add_pipeline(pipeline)(world.kwargs.get("predicate"))
    return pipeline


def associate_detection_info(tracking_result, detection_info_meta):
    for detection_info in detection_info_meta[tracking_result.frame_idx]:
        if detection_info.detection_id == tracking_result.detection_id:
            return detection_info


def process_pipeline(
    video_name: "str", frames: "Video", pipeline: "Pipeline", base, insert_traj: "bool" = True
):
    output = pipeline.run(Payload(frames))
    if insert_traj:
        metadata = output.metadata
        ego_meta = frames.interpolated_frames

        sortmeta = From2DAndRoad_3d.get(metadata)
        assert sortmeta is not None

        segment_trajectory_mapping = FromTracking3D.get(metadata)
        tracks = get_tracks(sortmeta, ego_meta, segment_trajectory_mapping, base)
        investigation = []
        start = time.time()
        for obj_id, track in tracks.items():
            trajectory, info_found = format_trajectory(video_name, obj_id, track, base)
            investigation.extend(info_found)
            if trajectory:
                # print("Inserting trajectory")
                insert_trajectory(database, *trajectory)
        trajectory_ingestion_time = time.time() - start
        print("Time taken to insert trajectories:", trajectory_ingestion_time)
        print("info found", investigation)
