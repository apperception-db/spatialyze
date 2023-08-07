import math
import time

from spatialyze.database import Database, database
from spatialyze.utils import join

from ..camera_config import CameraConfig
from ..payload import Payload
from ..pipeline import Pipeline
from ..stages.decode_frame.parallel_decode_frame import ParallelDecodeFrame
from ..stages.detection_2d.yolo_detection import YoloDetection
from ..stages.detection_3d.from_detection_2d_and_road import FromDetection2DAndRoad
from ..stages.detection_estimation import DetectionEstimation
from ..stages.segment_trajectory.construct_segment_trajectory import SegmentPoint
from ..stages.segment_trajectory.from_tracking_3d import (
    FromTracking3D,
    SegmentTrajectoryMetadatum,
)
from ..stages.tracking_2d.strongsort import StrongSORT
from ..stages.tracking_3d.from_tracking_2d_and_road import (
    FromTracking2DAndRoad as From2DAndRoad_3d,
)
from ..stages.tracking_3d.tracking_3d import Metadatum as Tracking3DMetadatum
from ..stages.tracking_3d.tracking_3d import Tracking3DResult
from ..types import Float3
from ..video.video import Video
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


def associate_segment_mapping(
    tracking_result: "Tracking3DResult",
    segment_mapping_meta: "list[SegmentTrajectoryMetadatum] | None",
):
    if segment_mapping_meta is None:
        return None
    return segment_mapping_meta[tracking_result.frame_idx].get(tracking_result.object_id)


def get_tracks(
    sortmeta: "list[Tracking3DMetadatum]",
    ego_meta: "list[CameraConfig]",
    segment_mapping_meta: "list[SegmentTrajectoryMetadatum] | None",
    base=None,
) -> "dict[str, list[tuple[Tracking3DResult, CameraConfig, SegmentPoint | None]]]":
    trajectories: "dict[str, list[tuple[Tracking3DResult, CameraConfig, SegmentPoint | None]]]" = {}
    for i in range(len(sortmeta)):
        frame = sortmeta[i]
        for obj_id, tracking_result in frame.items():
            if obj_id not in trajectories:
                trajectories[obj_id] = []
            associated_ego_info = ego_meta[i]
            associated_segment_mapping = associate_segment_mapping(
                tracking_result, segment_mapping_meta
            )
            trajectories[obj_id].append(
                (tracking_result, associated_ego_info, associated_segment_mapping)
            )

    for trajectory in trajectories.values():
        last = len(trajectory) - 1
        for i, t in enumerate(trajectory):
            if i > 0:
                t[0].prev = trajectory[i - 1][0]
            if i < last:
                t[0].next = trajectory[i + 1][0]
    return trajectories


def infer_heading(
    curItemHeading: "int | None", prevPoint: "Float3 | None", current_point: "Float3"
):
    if curItemHeading is not None:
        return math.degrees(curItemHeading)
    if prevPoint is None:
        return None
    x1, y1, z1 = prevPoint
    x2, y2, z2 = current_point
    # 0 is north (y-axis) and counter clockwise
    return math.degrees(math.atan2(y2 - y1, x2 - x1)) - 90


def format_trajectory(
    video_name: "str",
    obj_id: "str",
    track: "list[tuple[Tracking3DResult, CameraConfig, SegmentPoint | None]]",
    base=None,
):
    timestamps: "list[str]" = []
    pairs: "list[Float3]" = []
    itemHeadings: "list[int]" = []
    translations: "list[Float3]" = []
    camera_id = None
    object_type = None
    # road_types: "list[str]" = []
    # roadpolygons: "list[list[Float2]]" = []
    ### TODO (fge): remove investigation code
    info_found = []
    # if obj_id in investigation_ids:
    #     print(f"obj_id, {obj_id}:", [e[1].filename for e in track])
    for tracking_result_3d, ego_info, segment_mapping in track:
        if ego_info:
            if (
                "sweeps/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657125362404.jpg"
                in ego_info.filename
            ):
                info_found.append(
                    [
                        obj_id,
                        tracking_result_3d.bbox_left,
                        tracking_result_3d.bbox_top,
                        tracking_result_3d.bbox_w,
                        tracking_result_3d.bbox_h,
                    ]
                )
            camera_id = ego_info.camera_id
            object_type = tracking_result_3d.object_type
            timestamps.append(ego_info.timestamp)
            pairs.append(tracking_result_3d.point)
            if not segment_mapping or (segment_mapping.segment_type == "intersection"):
                itemHeadings.append(None)
            else:
                itemHeadings.append(segment_mapping.segment_heading)
            translations.append(ego_info.ego_translation)
            # road_types.append(segment_mapping.road_polygon_info.road_type if base else detection_info.road_type)
            # roadpolygons.append(None if base else detection_info.road_polygon_info.polygon)
    if len(timestamps) == 0 or camera_id is None or object_type is None:
        return None
    # if obj_id in investigation_ids:
    #     print(f"pairs for obj {obj_id}:", [(e[0], e[1]) for e in pairs])
    #     print(f"itemHeadings for obj {obj_id}:", itemHeadings)

    return (
        video_name + "_obj_" + str(obj_id),
        camera_id,
        object_type,
        timestamps,
        pairs,
        itemHeadings,
        translations,
    ), info_found


def insert_trajectory(
    database: "Database",
    item_id: str,
    camera_id: str,
    object_type: str,
    postgres_timestamps: "list[str]",
    pairs: "list[Float3]",
    itemHeading_list: "list[int]",
    translation_list: "list[Float3]",
    # road_types: "list[str]",
    # roadpolygon_list: "list[list[tuple[float, float]]]"
):
    traj_centroids: "list[str]" = []
    translations: "list[str]" = []
    itemHeadings: "list[str]" = []
    prevTimestamp: "str | None" = None
    prevPoint: "Float3 | None" = None
    for timestamp, current_point, curItemHeading, current_trans in zip(
        postgres_timestamps, pairs, itemHeading_list, translation_list
    ):
        if prevTimestamp == timestamp:
            continue
        prevTimestamp = timestamp

        # Construct trajectory
        traj_centroids.append(f"POINT Z ({join(current_point, ' ')})@{timestamp}")
        translations.append(f"POINT Z ({join(current_point, ' ')})@{timestamp}")
        curItemHeading = infer_heading(curItemHeading, prevPoint, current_point)
        if curItemHeading is not None:
            itemHeadings.append(f"{curItemHeading}@{timestamp}")
        # roadTypes.append(f"{cur_road_type}@{timestamp}")
        # polygon_point = ', '.join(join(cur_point, ' ') for cur_point in list(
        #     zip(*cur_roadpolygon.exterior.coords.xy)))
        # roadPolygons.append(f"Polygon (({polygon_point}))@{timestamp}")
        prevPoint = current_point

    # Insert the item_trajectory separately
    item_headings = (
        f"tfloat 'Interp=Stepwise;{{[{', '.join(itemHeadings)}]}}'" if itemHeadings else "null"
    )
    insert_trajectory = f"""
    INSERT INTO Item_General_Trajectory (itemId, cameraId, objectType, trajCentroids,
    translations, itemHeadings)
    VALUES (
        '{item_id}',
        '{camera_id}',
        '{object_type}',
        tgeompoint '{{[{', '.join(traj_centroids)}]}}',
        tgeompoint '{{[{', '.join(translations)}]}}',
        {item_headings}
    );
    """

    database.execute(insert_trajectory)
    database._commit()


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
