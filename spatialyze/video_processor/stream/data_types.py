from typing import NamedTuple

import numpy.typing as npt
import torch

from ..types import DetectionId


class Skip:
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Skip, cls).__new__(cls)
        return cls._instance


skip = Skip()


class Frame(NamedTuple):
    img: npt.NDArray


class Detection2D(NamedTuple):
    detections: torch.Tensor
    class_map: list[str] | None
    detection_ids: list[DetectionId]


class Detection3D(NamedTuple):
    detections: torch.Tensor
    class_map: list[str] | None
    detection_ids: list[DetectionId]
