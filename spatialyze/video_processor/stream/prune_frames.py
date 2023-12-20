from typing import TypeVar
from types import GeneratorType

from ..utils.exhausted import exhausted
from ..video import Video
from .data_types import Skip, skip
from .stream import Stream

T = TypeVar("T")


class PruneFrames(Stream[T]):
    def __init__(self, pruner: Stream[bool], stream: Stream[T]):
        self.pruner = pruner
        self.stream_ = stream

    def _stream(self, video: Video):
        pruner = self.pruner.stream(video)
        assert isinstance(pruner, GeneratorType)
        stream = self.stream_.stream(video)
        assert isinstance(stream, GeneratorType)
        for prune, frame in zip(pruner, stream):
            if prune is True and not isinstance(frame, Skip):
                yield frame
            else:
                yield skip
        
        assert exhausted(pruner)
        assert exhausted(stream)
