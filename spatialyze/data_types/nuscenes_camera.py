from typing import NamedTuple

import numpy.typing as npt


class NuscenesCamera(NamedTuple):
    token: "str"
    sample_token: "str"
    timestamp: "int"
    is_key_frame: "bool"
    filename: "str"
    sample_timestamp: "int"
    camera_translation: "npt.NDArray"
    camera_rotation: "npt.NDArray"
    camera_intrinsic: "list[list[float]]"
    ego_translation: "list[float]"
    ego_rotation: "list[float]"
    scene_name: "str"
    channel: "str"
    location: "str"
    ego_heading: "float"
    camera_heading: "float"
    frame_order: "int"