from collections.abc import Iterable

from ...predicate import PredicateNode
from ..payload import Payload
from ..stages.in_view.in_view import InView
from ..video import Video
from .stream import Stream


class RoadVisibilityPruner(Stream[bool]):
    def __init__(
        self,
        distance: float,
        roadtypes: str | list[str] | None = None,
        predicate: PredicateNode | None = None,
    ):
        self.inview = InView(distance, roadtypes, predicate)

    def _stream(self, video: Video) -> Iterable[bool]:
        keep, _ = self.inview.run(Payload(video))
        assert keep is not None
        for k in keep:
            yield True if k else False
        self.end()
