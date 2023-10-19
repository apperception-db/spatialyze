from typing import TypeVar

from ..video import Video
from .data_types import skip
from .stream import Stream

T = TypeVar("T")


class PruneFrames(Stream[T]):
    def __init__(self, prunner: Stream[bool], stream: Stream[T]):
        self.prunner = prunner
        self.stream_ = stream

    def _stream(self, video: Video):
        for prune, frame in zip(self.prunner.stream(video), self.stream_.stream(video)):
            if prune is True and frame != skip:
                yield frame
            else:
                yield skip
