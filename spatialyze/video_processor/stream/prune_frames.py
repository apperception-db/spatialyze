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
        count = 0
        total = 0
        for prune, frame in zip(self.prunner.stream(video), self.stream_.stream(video)):
            total += 1
            if prune is True and frame != skip:
                count += 1
                yield frame
            else:
                yield skip
        print(f"Kept {count} of {total} frames")
