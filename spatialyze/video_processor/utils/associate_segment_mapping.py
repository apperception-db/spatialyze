from ..stages.segment_trajectory.from_tracking_3d import SegmentTrajectoryMetadatum
from ..stages.tracking_3d.tracking_3d import Tracking3DResult


def associate_segment_mapping(
    tracking_result: "Tracking3DResult",
    segment_mapping_meta: "list[SegmentTrajectoryMetadatum] | None",
):
    if segment_mapping_meta is None:
        return None
    return segment_mapping_meta[tracking_result.frame_idx].get(int(tracking_result.object_id))
