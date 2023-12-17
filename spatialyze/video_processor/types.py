from typing import NamedTuple, Tuple


UNIQUE_MAP: dict[int, int] = {}


class DetectionId(NamedTuple):
    frame_idx: int
    obj_order: "str | int"

    def __repr__(self) -> str:
        return f"(f={self.frame_idx} o={self.obj_order})"
    
    @classmethod
    def unique(cls, frame_idx: int) -> int:
        if frame_idx not in UNIQUE_MAP:
            UNIQUE_MAP[frame_idx] = 0
        UNIQUE_MAP[frame_idx] -= 1
        return UNIQUE_MAP[frame_idx]


class obj_detection(NamedTuple):
    detection_id: DetectionId
    car_loc3d: "Float3"
    car_loc2d: "Float2"
    car_bbox3d: "Tuple[Float3, Float3]"
    car_bbox2d: "Float22"


Float2 = Tuple[float, float]
Float22 = Tuple[Float2, Float2]

Float3 = Tuple[float, float, float]
Float33 = Tuple[Float3, Float3, Float3]

Float4 = Tuple[float, float, float, float]
