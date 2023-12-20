from collections.abc import Iterable

from bitarray import bitarray

from ..video import Video
from .data_types import Skip, skip
from .stream import Stream


class Prefilter(Stream[bool]):
    def __init__(self, keep: bitarray):
        self.keep = keep

    def _stream(self, video: Video) -> Iterable[bool | Skip]:
        for k in self.keep:
            yield True if k else skip
        self.end()
