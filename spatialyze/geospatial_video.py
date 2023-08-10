import json
from typing import Any

from .video_processor.camera_config import CameraConfig, camera_config


class GeospatialVideo:
    def __init__(self, video: "str", camera: "list[CameraConfig] | str") -> None:
        self.video = video
        if isinstance(camera, str):
            with open(camera, "r") as f:
                camera_configs = json.load(f)
                assert isinstance(camera_configs, list), camera_configs
                self.camera = [_camera_config(c) for c in camera_configs]
        else:
            self.camera = camera


def _camera_config(c: "Any"):
    assert isinstance(c, list), c
    assert len(c) == 13, c
    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13 = c
    return camera_config(c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, 0)
