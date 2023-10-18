from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

from ..video.video import Video
from .data_types import Skip

T = TypeVar("T")


class Stream(Generic[T], ABC):
    __use_count: int
    __use_progress: list[int]

    __front: int
    __results: list[T | Skip | None]
    __video: Video | None
    __iter_stream: Iterator[T | Skip] | None

    def __new__(cls, *args, **kwargs):
        instance = super(Stream, cls).__new__(cls)
        for arg in args + tuple(kwargs.values()):
            if isinstance(arg, Stream):
                arg.__use_progress.append(0)
        instance.__use_count = 0
        instance.__use_progress = []
        instance.__front = 0
        instance.__results = []
        instance.__video = None
        instance.__iter_stream = None
        return instance

    def stream(self, video: Video) -> Iterable[T | Skip]:
        if self.__video is None or self.__iter_stream is None:
            self.__video = video
            self.__iter_stream = iter(self._stream(video))
            self.__results.append(next(self.__iter_stream))
        assert self.__video == video

        idx = self.__assign_stream_idx()
        try:
            while True:
                while len(self.__results) <= self.__use_progress[idx]:
                    self.__results.append(next(self.__iter_stream))

                yield self.__results[self.__use_progress[idx]]
                self.__use_progress[idx] += 1

                self.__free_memory()
        except StopIteration:
            return

    def __assign_stream_idx(self):
        idx = self.__use_count
        self.__use_count += 1
        assert len(self.__use_progress) >= self.__use_count, (
            len(self.__use_progress),
            self.__use_count,
        )
        return idx

    def __free_memory(self):
        _min_progress = min(self.__use_progress)
        while self.__front < _min_progress:
            self.__results[self.__front] = None
            self.__front += 1

    @abstractmethod
    def _stream(self, video: Video) -> Iterable[T | Skip]:
        ...
