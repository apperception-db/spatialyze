from collections.abc import Iterable
from typing import TypeVar, Generic

from .data_types import Skip
from ..video.video import Video


T = TypeVar('T')


class Stream(Generic[T]):
    def stream(self, video: Video) -> Iterable[T | Skip]:
        ...
