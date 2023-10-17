from collections.abc import Iterable
from typing import Generic, TypeVar

from ..video.video import Video
from .data_types import Skip

T = TypeVar("T")


class Stream(Generic[T]):
    def stream(self, video: Video) -> Iterable[T | Skip]:
        ...
