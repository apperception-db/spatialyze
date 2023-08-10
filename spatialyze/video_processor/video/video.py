from datetime import datetime
from typing import Iterable

import cv2

from ..camera_config import CameraConfig


class Video(Iterable["CameraConfig"]):
    videofile: str

    def __init__(
        self,
        videofile: str,
        camera_configs: "list[CameraConfig]",
        start: "datetime | None" = None,
    ):
        self.videofile = videofile
        self._camera_configs: "list[CameraConfig]" = camera_configs
        assert all(
            prev.timestamp < next.timestamp
            for prev, next in zip(camera_configs[:-1], camera_configs[1:])
        )
        self._start: "datetime | None" = start
        self._length: "int | None" = None
        self._fps: "float | None" = None
        self._dimension: "tuple[int, int] | None" = None

    @property
    def camera_configs(self):
        return self._camera_configs

    @property
    def interpolated_frames(self):
        # TODO: remove
        return self._camera_configs

    @property
    def fps(self):
        return self._get_props()[1]

    @property
    def dimension(self):
        """
        Returns: (width, height)
        """
        return self._get_props()[2]

    def __getitem__(self, index: "int"):
        return self.interpolated_frames[index]

    def __iter__(self):
        return iter(self.interpolated_frames)

    def __len__(self):
        return self._get_props()[0]

    def _get_props(self):
        if self._length is None or self._fps is None or self._dimension is None:
            cap = cv2.VideoCapture(self.videofile)
            assert cap.isOpened(), self.videofile
            self._length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self._fps = float(cap.get(cv2.CAP_PROP_FPS))
            self._dimension = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )
            cap.release()
            cv2.destroyAllWindows()
        return self._length, self._fps, self._dimension
