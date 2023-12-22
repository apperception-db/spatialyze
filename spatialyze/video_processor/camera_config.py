from dataclasses import dataclass
from datetime import datetime

import numpy as np
from pyquaternion import Quaternion

Float3 = tuple[float, float, float]
Float4 = tuple[float, float, float, float]
Float33 = tuple[Float3, Float3, Float3]


@dataclass
class CameraConfig:
    camera_id: str
    frame_id: str
    frame_num: int
    filename: str
    camera_translation: Float3
    camera_rotation: Quaternion
    camera_intrinsic: Float33
    ego_translation: Float3
    ego_rotation: Quaternion
    timestamp: datetime
    camera_heading: float
    ego_heading: float
    location: str
    road_direction: float = 0


def camera_config(
    camera_id: str,
    frame_id: str,
    frame_num: int,
    filename: str,
    camera_translation: "Float3",
    camera_rotation: "Float4",
    camera_intrinsic: "Float33",
    ego_translation: "Float3",
    ego_rotation: "Float4",
    timestamp: datetime,
    camera_heading: float,
    ego_heading: float,
    location: str,
    road_direction: float = 0,
):
    return CameraConfig(
        camera_id,
        frame_id,
        frame_num,
        filename,
        np.array(camera_translation, dtype=np.float32).tolist(),
        Quaternion(np.array(camera_rotation, dtype=np.float32)).unit,
        ar(camera_intrinsic).tolist(),
        ar(ego_translation).tolist(),
        Quaternion(ar(ego_rotation)).unit,
        timestamp,
        ar((camera_heading,))[0].item(),
        ar((ego_heading,))[0].item(),
        location,
        road_direction,
    )


def ar(li: tuple):
    return np.array(li, dtype=np.float32)
