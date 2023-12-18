from typing import TypeVar

from ..video import Video=
from .data_types import Skip, skip=
from .stream import Stream

T = TypeVar("T")


class PruneFrames(Stream[T]):
    def __init__(self, pruner: Stream[bool], stream: Stream[T]):
        self.pruner = pruner
        self.stream_ = stream

    def _stream(self, video: Video):
        for prune, frame in zip(self.pruner.stream(video), self.stream_.stream(video)):
            if prune is True and not isinstance(frame, Skip):
                yield frame
            else:
                yield skip
