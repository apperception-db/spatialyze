from typing import NamedTuple

from ..camera_config import CameraConfig
from ..stages.segment_trajectory import SegmentPoint
from ..stages.segment_trajectory.from_tracking_3d import SegmentTrajectoryMetadatum
from ..stages.tracking_3d.tracking_3d import Metadatum as Tracking3DMetadatum
from ..stages.tracking_3d.tracking_3d import Tracking3DResult
from .associate_segment_mapping import associate_segment_mapping


class TrackPoint(NamedTuple):
    tracking_result: "Tracking3DResult"
    ego_info: "CameraConfig"
    segment_mapping: "SegmentPoint | None"


def get_tracks(
    sortmeta: "list[Tracking3DMetadatum]",
    ego_meta: "list[CameraConfig]",
    segment_mapping_meta: "list[SegmentTrajectoryMetadatum] | None" = None,
) -> "dict[int, list[TrackPoint]]":
    trajectories: "dict[int, list[TrackPoint]]" = {}
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
                TrackPoint(tracking_result, associated_ego_info, associated_segment_mapping)
            )

    for trajectory in trajectories.values():
        last = len(trajectory) - 1
        for i, t in enumerate(trajectory):
            if i > 0:
                t[0].prev = trajectory[i - 1][0]
            if i < last:
                t[0].next = trajectory[i + 1][0]
    return trajectories
