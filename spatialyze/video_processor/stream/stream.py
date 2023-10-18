from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

from ..video.video import Video
from .data_types import Skip

T = TypeVar("T")


class Stream(Generic[T], ABC):
    __stream_count: int
    __stream_progress: list[int]

    __front: int
    __results: list[T | Skip | None]
    __video: Video | None
    __iter_stream: Iterator[T | Skip] | None

    def __new__(cls, *args, **kwargs):
        instance = super(Stream, cls).__new__(cls)
        for arg in args + tuple(kwargs.values()):
            if isinstance(arg, Stream):
                arg.__stream_progress.append(0)
        instance.__stream_count = 0
        instance.__stream_progress = []
        instance.__front = 0
        instance.__results = []
        instance.__video = None
        instance.__iter_stream = None
        return instance

    def execute(self, video: Video) -> list[T | Skip]:
        self.__initialize_stream(video)
        self.__initialize_stream_progress()
        return list(self.stream(video))

    def stream(self, video: Video) -> Iterable[T | Skip]:
        assert self.__video == video
        assert self.__iter_stream is not None

        idx = self.__assign_stream_idx()
        try:
            while True:
                while len(self.__results) <= self.__stream_progress[idx]:
                    self.__results.append(next(self.__iter_stream))

                result = self.__results[self.__stream_progress[idx]]
                assert result is not None
                yield result
                self.__stream_progress[idx] += 1

                self.__free_memory()
        except StopIteration:
            return

    def __initialize_stream(self, video: Video):
        self.__stream_progress = []
        self.__stream_count = 0
        self.__video = video
        self.__iter_stream = iter(self._stream(video))
        self.__results = [next(self.__iter_stream)]
        self.__front = 0
        for attr in dir(self):
            stream = getattr(self, attr)
            if isinstance(stream, Stream):
                stream.__initialize_stream(video)

    def __initialize_stream_progress(self):
        self.__stream_progress.append(0)
        for attr in dir(self):
            stream = getattr(self, attr)
            if isinstance(stream, Stream):
                stream.__initialize_stream_progress()

    def __assign_stream_idx(self):
        idx = self.__stream_count
        self.__stream_count += 1
        assert len(self.__stream_progress) >= self.__stream_count, (
            len(self.__stream_progress),
            self.__stream_count,
        )
        return idx

    def __free_memory(self):
        _min_progress = min(self.__stream_progress)
        while self.__front < _min_progress:
            self.__results[self.__front] = None
            self.__front += 1

    @abstractmethod
    def _stream(self, video: Video) -> Iterable[T | Skip]:
        ...
