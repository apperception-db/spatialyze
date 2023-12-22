import datetime
from typing import NamedTuple

from ..camera_config import CameraConfig
from ..stream.strongsort import TrackingResult
from ..types import Float3


class Trajectory(NamedTuple):
    obj_id: int
    camera_id: str
    object_type: str
    timestamps: list[datetime.datetime]
    pairs: list[Float3]
    itemHeadings: list[float | None]


def prepare_trajectory(
    video_name: "str",
    obj_id: "int",
    track: "list[TrackingResult]",
    configs: list[CameraConfig],
) -> Trajectory | None:
    timestamps: "list[datetime.datetime]" = []
    pairs: "list[Float3]" = []
    itemHeadings: "list[float | None]" = [None] * len(track)
    translations: "list[Float3]" = []
    camera_id = None
    object_type = None
    for tracking_result in track:
        config = configs[tracking_result.detection_id.frame_idx]
        camera_id = config.camera_id
        object_type = tracking_result.object_type
        timestamps.append(config.timestamp)
        bbox = tracking_result.bbox
        point = (bbox[6:9] + bbox[9:12]) / 2
        x, y, z = map(float, point.tolist())
        pairs.append((x, y, z))
        # itemHeadings.append(None)
        translations.append(config.ego_translation)
    if len(timestamps) == 0 or camera_id is None or object_type is None:
        return None

    return Trajectory(
        # video_name + "_obj_" + str(obj_id),
        obj_id,
        camera_id,
        object_type,
        timestamps,
        pairs,
        itemHeadings,
    )
