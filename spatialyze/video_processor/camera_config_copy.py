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
    cameraId: str,
    frameNum: int,
    fileName: str,
    cameraTranslation: "Float3",
    cameraRotation: "Float4",
    cameraIntrinsic: "Float33",
    egoTranslation: "Float3",
    egoRotation: "Float4",
    timestamp: datetime,
    cameraHeading: float,
    egoHeading: float,
):
    _frame = CameraConfig()
    _frame.camera_id = cameraId
    _frame.filename = fileName
    _frame.timestamp = timestamp
    _frame._data = np.array(
        [
            frameNum,
            *cameraTranslation,
            *cameraRotation,
            *itertools.chain(*cameraIntrinsic),
            *egoTranslation,
            *egoRotation,
            cameraHeading,
            egoHeading,
        ],
        dtype=np.float32,
    )
    return _frame


class CameraConfig:
    camera_id: str
    # TODO: remove
    frame_id: Optional[str]
    # TODO: remove
    filename: Optional[str]
    timestamp: datetime
    _data: "npt.NDArray[np.float32]"

    @property
    def frame_num(self) -> float:
        return self._data[0].item()

    @property
    def camera_translation(self) -> Float3:
        return tuple(self._data[1:4].tolist())

    @property
    def camera_rotation(self) -> "Quaternion":
        return Quaternion(self._data[4:8]).unit

    @property
    def camera_intrinsic(self) -> Float33:
        return self._data[8:17].reshape((3, 3)).tolist()

    @property
    def ego_translation(self) -> Float3:
        return tuple(self._data[17:20].tolist())

    @property
    def ego_rotation(self) -> "Quaternion":
        return Quaternion(self._data[20:24]).unit

    @property
    def camera_heading(self) -> float:
        return self._data[24].item()

    @property
    def ego_heading(self) -> float:
        return self._data[25].item()

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
            ]
        )


def interpolate(f1: CameraConfig, f2: CameraConfig, timestamp: datetime):
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
    _frame._data = (f2._data - f1._data) * ratio + f1._data

    return _frame
