from ...predicate import PredicateNode
from ..stages.detection_2d.object_type_filter import ObjectTypeFilter
from ..video import Video
from .data_types import Detection2D, Skip
from .reusable import reusable
from .stream import Stream


@reusable
class ObjectTypePruner(Stream[Detection2D]):
    def __init__(
        self,
        detections: Stream[Detection2D],
        types: list[str] | None = None,
        predicate: PredicateNode | None = None,
    ):
        self.detections = detections
        self.object_type_filter = ObjectTypeFilter(types, predicate)
        self.types = self.object_type_filter.types

    def stream(self, video: Video):
        type_indices_to_keep: set[int] | None = None

        for detection_2d in self.detections.stream(video):
            if detection_2d == Skip():
                yield Skip()
                continue

            det, class_mapping, ids = detection_2d
            if len(det) == 0:
                yield detection_2d
                continue

            if type_indices_to_keep is None:
                type_indices_to_keep = set()
                for t in self.types:
                    idx = class_mapping.index(t)
                    type_indices_to_keep.add(idx)

            det_to_keep: list[int] = []
            type_indices = det[:, 5]
            type_indices_list: list[float] = type_indices.tolist()
            for i, type_index in enumerate(type_indices_list):
                assert isinstance(type_index, float), type(type_index)
                assert type_index.is_integer()
                if type_index in type_indices_to_keep:
                    det_to_keep.append(i)

            yield Detection2D(det[det_to_keep], class_mapping, [ids[k] for k in det_to_keep])
