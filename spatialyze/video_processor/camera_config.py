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


def ar(l: tuple):
    return np.array(l, dtype=np.float32)


# def camera_config(
#     camera_id: str,
#     frame_id: str,
#     frame_num: int,
#     filename: str,
#     camera_translation: "Float3",
#     camera_rotation: "Float4",
#     camera_intrinsic: "Float33",
#     ego_translation: "Float3",
#     ego_rotation: "Float4",
#     timestamp: datetime,
#     camera_heading: float,
#     ego_heading: float,
#     location: str,
#     road_direction: float = 0,
# ):
#     _frame = CameraConfig()
#     _frame.camera_id = camera_id
#     _frame.frame_id = frame_id
#     _frame.filename = filename
#     _frame.timestamp = timestamp
#     _frame.location = location
#     _frame._data = np.array(
#         [
#             frame_num,
#             *camera_translation,
#             *camera_rotation,
#             *itertools.chain(*camera_intrinsic),
#             *ego_translation,
#             *ego_rotation,
#             camera_heading,
#             ego_heading,
#             road_direction,
#         ],
#         dtype=np.float32,
#     )
#     return _frame


# class CameraConfig:
#     camera_id: str
#     # TODO: remove
#     frame_id: str | None
#     # TODO: remove
#     filename: str | None
#     timestamp: datetime
#     location: str
#     _data: "npt.NDArray[np.float32]"

#     @property
#     def frame_num(self) -> int:
#         return int(self._data[0].item())

#     @property
#     def camera_translation(self) -> Float3:
#         x, y, z = self._data[1:4].tolist()
#         return x, y, z

#     @property
#     def camera_rotation(self) -> "Quaternion":
#         return Quaternion(self._data[4:8]).unit

#     @property
#     def camera_intrinsic(self) -> Float33:
#         return self._data[8:17].reshape((3, 3)).tolist()

#     @property
#     def ego_translation(self) -> Float3:
#         x, y, z = self._data[17:20].tolist()
#         return x, y, z

#     @property
#     def ego_rotation(self) -> "Quaternion":
#         return Quaternion(self._data[20:24]).unit

#     @property
#     def camera_heading(self) -> float:
#         return self._data[24].item()

#     @property
#     def ego_heading(self) -> float:
#         return self._data[25].item()

#     @property
#     def road_direction(self) -> float:
#         return self._data[26].item()

#     def __iter__(self):
#         return iter(
#             [
#                 self.camera_id,
#                 self.frame_id,
#                 self.frame_num,
#                 self.filename,
#                 self.camera_translation,
#                 self.camera_rotation,
#                 self.camera_intrinsic,
#                 self.ego_translation,
#                 self.ego_rotation,
#                 self.timestamp,
#                 self.camera_heading,
#                 self.ego_heading,
#                 self.location,
#                 self.road_direction,
#             ]
#         )
