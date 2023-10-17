from collections.abc import Iterable

from .data_types import Skip, skip
from .reusable import reusable
from .stream import Stream
from ..payload import Payload
from ..stages.in_view.in_view import InView
from ..video import Video
from ...predicate import PredicateNode


@reusable
class RoadVisibilityPruner(Stream[bool]):
    def __init__(
        self,
        distance: float,
        roadtypes: str | list[str] | None = None,
        predicate: PredicateNode | None = None,
    ):
        self.inview = InView(distance, roadtypes, predicate)

    def stream(self, video: Video) -> Iterable[bool | Skip]:
        keep, _ = self.inview.run(Payload(video))
        return (True if k else skip for k in keep)
