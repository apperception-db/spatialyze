from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

from ..video.video import Video
from .data_types import Skip

T = TypeVar("T")


class Stream(Generic[T], ABC):
    _stream_count: int
    _stream_progress: list[int]

    _front: int
    _results: list[T | Skip | None]
    _video: Video | None
    _iter_stream: Iterator[T | Skip] | None

    _visited: bool
    _ended: bool

    def __new__(cls, *args, **kwargs):
        instance = super(Stream, cls).__new__(cls)
        for arg in args + tuple(kwargs.values()):
            if isinstance(arg, Stream):
                arg._stream_progress.append(0)
        instance._stream_count = 0
        instance._stream_progress = []
        instance._front = 0
        instance._results = []
        instance._video = None
        instance._iter_stream = None
        return instance

    def iterate(self, video: Video) -> Iterable[T | Skip]:
        self._initialize_stream(video)
        self._initialize_stream_progress()
        return self.stream(video)

    def execute(self, video: Video) -> list[T | Skip]:
        return list(self.iterate(video))

    def stream(self, video: Video) -> Iterable[T | Skip]:
        assert self._video == video, self._video
        assert self._iter_stream is not None

        idx = self._assign_stream_idx()
        try:
            while True:
                while len(self._results) <= self._stream_progress[idx]:
                    self._results.append(next(self._iter_stream))

                result = self._results[self._stream_progress[idx]]
                assert result is not None
                yield result
                self._stream_progress[idx] += 1

                self._free_memory()
        except StopIteration:
            return

    def ended(self):
        if not self._ended:
            # raise Exception('not ended')
            return False
        for attr in dir(self):
            stream = getattr(self, attr)
            if isinstance(stream, Stream):
                if not stream.ended():
                    # raise Exception('not ended')
                    return False
        return True

    def end(self):
        self._ended = True

    def _initialize_stream(self, video: Video):
        self._stream_progress = []
        self._stream_count = 0
        self._video = video
        self._iter_stream = iter(self._stream(video))
        self._results = []
        self._front = -1
        self._visited = False
        self._ended = False
        for attr in dir(self):
            stream = getattr(self, attr)
            if isinstance(stream, Stream):
                stream._initialize_stream(video)

    def _initialize_stream_progress(self):
        self._stream_progress.append(0)
        if self._visited:
            return
        self._visited = True
        for attr in dir(self):
            stream = getattr(self, attr)
            if isinstance(stream, Stream):
                stream._initialize_stream_progress()

    def _assign_stream_idx(self):
        idx = self._stream_count
        self._stream_count += 1
        assert len(self._stream_progress) >= self._stream_count, (
            len(self._stream_progress),
            self._stream_count,
        )
        return idx

    def _free_memory(self):
        _min_progress = min(self._stream_progress)
        while self._front < _min_progress:
            if self._front >= 0:
                self._results[self._front] = None
            self._front += 1

    @abstractmethod
    def _stream(self, video: Video) -> Iterable[T | Skip]:
        ...
