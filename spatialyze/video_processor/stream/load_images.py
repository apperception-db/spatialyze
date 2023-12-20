import cv2
import numpy.typing as npt

from ..video.video import Video
from .data_types import Skip, skip
from .stream import Stream


class LoadImages(Stream[npt.NDArray]):
    def __init__(self, frames: Stream[str]):
        self.frames = frames

    def _stream(self, video: Video):
        for filename in self.frames.stream(video):
            if isinstance(filename, Skip):
                yield skip
                continue

            yield cv2.imread(filename)
        self.end()
