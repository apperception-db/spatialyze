from collections.abc import Iterator
from typing import ParamSpec, TypeVar, Callable

from .data_types import Skip
from .stream import Stream
from ..video import Video

T = TypeVar("T")
P = ParamSpec("P")


def reusable(cls: Callable[P, Stream[T]] | type[Stream[T]]) -> Callable[P, Stream[T]] | type[Stream[T]]:
    class ReusableStream(Stream[T]):
        children_count: int
        children_progress: list[int]

        def __init__(self, *args, **kwargs):
            for arg in args + tuple(kwargs.values()):
                if isinstance(arg, ReusableStream):
                    arg.children_progress.append(0)

            self.stream = cls(*args, **kwargs)
            self.children_count = 0
            self.children_progress = []
            self.front = 0
            self.results: list[T | Skip | None] = []

            self._video: Video | None = None
            self._stream: Iterator[T | Skip] | None = None

        def stream(self, video: Video):
            if self._video is None or self._video is None:
                self._video = video
                self._stream = iter(self.stream.stream(video))
                self.results.append(next(self._stream))
            assert self._video == video

            idx = self._assign_stream_idx()
            while True:
                while len(self.results) <= self.children_progress[idx]:
                    self.results.append(next(self._stream))

                yield self.results[self.children_progress[idx]]
                self.children_progress[idx] += 1

                self._free_memory()

        def _assign_stream_idx(self):
            idx = self.children_count
            self.children_count += 1
            assert len(self.children_progress) >= self.children_count, (len(self.children_progress), self.children_count)
            return idx

        def _free_memory(self):
            _min_progress = min(self.children_progress)
            while self.front < _min_progress:
                self.results[self.front] = None
                self.front += 1

        def __repr__(self):
            return f"Reusable({cls.__name__})"

    return ReusableStream
