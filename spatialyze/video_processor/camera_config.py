import itertools
from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import numpy.typing as npt
from pyquaternion import Quaternion

Float3 = Tuple[float, float, float]
Float4 = Tuple[float, float, float, float]
Float33 = Tuple[Float3, Float3, Float3]


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
    _frame = CameraConfig()
    _frame.camera_id = camera_id
    _frame.frame_id = frame_id
    _frame.filename = filename
    _frame.timestamp = timestamp
    _frame.location = location
    _frame._data = np.array(
        [
            frame_num,
            *camera_translation,
            *camera_rotation,
            *itertools.chain(*camera_intrinsic),
            *ego_translation,
            *ego_rotation,
            camera_heading,
            ego_heading,
            road_direction,
        ],
        dtype=np.float32,
    )
    return _frame


def has_config(config: "CameraConfig"):
    return config.filename is not None


class CameraConfig:
    camera_id: str
    # TODO: remove
    frame_id: Optional[str]
    # TODO: remove
    filename: Optional[str]
    timestamp: datetime
    location: str
    _data: "npt.NDArray[np.float32]"

    @property
    def frame_num(self) -> int:
        return int(self._data[0].item())

    @property
    def camera_translation(self) -> Float3:
        x, y, z = self._data[1:4].tolist()
        return x, y, z

    @property
    def camera_rotation(self) -> "Quaternion":
        return Quaternion(self._data[4:8]).unit

    @property
    def camera_intrinsic(self) -> Float33:
        return self._data[8:17].reshape((3, 3)).tolist()

    @property
    def ego_translation(self) -> Float3:
        x, y, z = self._data[17:20].tolist()
        return x, y, z

    @property
    def ego_rotation(self) -> "Quaternion":
        return Quaternion(self._data[20:24]).unit

    @property
    def camera_heading(self) -> float:
        return self._data[24].item()

    @property
    def ego_heading(self) -> float:
        return self._data[25].item()

    @property
    def road_direction(self) -> float:
        return self._data[26].item()

    def __iter__(self):
        return iter(
            [
                self.camera_id,
                self.frame_id,
                self.frame_num,
                self.filename,
                self.camera_translation,
                self.camera_rotation,
                self.camera_intrinsic,
                self.ego_translation,
                self.ego_rotation,
                self.timestamp,
                self.camera_heading,
                self.ego_heading,
                self.location,
                self.road_direction,
            ]
        )


def interpolate(f1: CameraConfig, f2: CameraConfig, timestamp: datetime):
    assert f1.camera_id == f2.camera_id
    assert f1.location == f2.location

    t1 = f1.timestamp
    t2 = f2.timestamp
    total_delta = (t2 - t1).total_seconds()
    delta = (timestamp - t1).total_seconds()

    ratio = delta / total_delta

    _frame = CameraConfig()
    _frame.camera_id = f1.camera_id
    _frame.frame_id = None
    _frame.filename = None
    _frame.timestamp = timestamp
    _frame.location = f1.location
    _frame._data = (f2._data - f1._data) * ratio + f1._data

    return _frame
