from dataclasses import dataclass
from typing import Tuple

import numpy.typing as npt

Float3 = Tuple[float, float, float]
Float33 = Tuple[Float3, Float3, Float3]
Float4 = Tuple[float, float, float, float]


@dataclass(frozen=True)
class CameraConfig:
    frame_id: str
    frame_num: int
    filename: str
    camera_translation: npt.NDArray  # float[3]
    camera_rotation: npt.NDArray  # float[4]
    camera_intrinsic: Float33  # float[3][3]
    ego_translation: Float3  # float[3]
    ego_rotation: Float4  # float[4]
    timestamp: str
    cameraHeading: float
    egoHeading: float
