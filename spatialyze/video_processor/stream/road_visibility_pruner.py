from collections.abc import Iterable

from ...predicate import PredicateNode
from ..payload import Payload
from ..stages.in_view.in_view import InView
from ..video import Video
from .data_types import Skip, skip
from .stream import Stream


class RoadVisibilityPruner(Stream[bool]):
    def __init__(
        self,
        distance: float,
        roadtypes: str | list[str] | None = None,
        predicate: PredicateNode | None = None,
    ):
        self.inview = InView(distance, roadtypes, predicate)

    def _stream(self, video: Video) -> Iterable[bool | Skip]:
        keep, _ = self.inview.run(Payload(video))
        assert keep is not None
        return (True if k else skip for k in keep)
