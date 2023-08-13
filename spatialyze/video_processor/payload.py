from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

from bitarray import bitarray

if TYPE_CHECKING:
    from .stages.stage import Stage
    from .video import Video


Metadata = Dict[str, List[Any]]


@dataclass
class Payload:
    video: "Video"
    keep: "bitarray"
    metadata: "Metadata"

    def __init__(
        self,
        video: "Video",
        keep: "bitarray | None" = None,
        metadata: "Metadata | None" = None,
    ):
        self.keep = _default_keep(video, keep)
        self.video = video
        if metadata is None:
            metadata = {}
        if not all(len(m) == len(video) for m in metadata.values()):
            raise Exception(f"metadata: {len(metadata)}, video: {len(video)}")
        self.metadata = metadata

    def filter(self, filter: "Stage"):
        # print("Stage: ", filter.classname())
        keep, metadata = filter.run(self)

        if keep is None:
            keep = self.keep
        assert len(keep) == len(
            self.video
        ), f"{filter.classname()} -- keep: {len(keep)}, video: {len(self.video)}"
        keep = keep & self.keep

        if metadata is None or len(metadata) == 0:
            metadata = self.metadata

        if len(metadata) != 0:
            metadata_l = metadata_len(metadata)
            assert metadata_l == len(
                keep
            ), f"{filter.classname()} -- metadata: {metadata_l}, keep: {len(keep)}"

        metadata = {**self.metadata, **metadata}
        return Payload(self.video, keep, metadata)

    def __getitem__(self, stage) -> "list[Any] | None":
        if isinstance(stage, str):
            if stage in self.metadata:
                return self.metadata[stage]
            for k, v in reversed(self.metadata.items()):
                if k.startswith(stage):
                    return v
            return None
        return stage.get(self.metadata)


def metadata_len(metadata: "dict[str, list[Any]]") -> "int | None":
    length: "int | None" = None
    for v in metadata.values():
        if length is None:
            length = len(v)
        assert length == len(v), (length, len(v))
    return length


def _default_keep(video: "Video", keep: "bitarray | None" = None):
    if keep is None:
        keep = bitarray(len(video))
        keep.setall(1)
    assert len(keep) == len(video), (len(keep), len(video))
    return keep
