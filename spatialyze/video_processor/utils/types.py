from typing import NamedTuple

from ..types import Float3


class Trajectory(NamedTuple):
    obj_id: int | str
    ids: list[int]
    camera_id: str
    object_type: str
    pairs: list[Float3]
    itemHeadings: list[float | None]
