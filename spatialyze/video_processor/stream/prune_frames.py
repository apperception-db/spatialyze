from typing import TypeVar

from ..video import Video
from .data_types import skip
from .reusable import reusable
from .stream import Stream

T = TypeVar("T")


@reusable
class PruneFrames(Stream[T]):
    def __init__(self, prunner: Stream[bool], stream: Stream[T]):
        self.prunner = prunner
        self._stream = stream

    def stream(self, video: Video):
        for prune, frame in zip(self.prunner.stream(video), self._stream.stream(video)):
            if prune is True and frame != skip:
                yield frame
            else:
                yield skip
