from typing import NamedTuple

import torch

from ...types import DetectionId
from ..stage import Stage


class Metadatum(NamedTuple):
    """
    detections:
    -----------
    A torch.Tensor with size N x 18, representing N objects detected from a single frame.
    Each including 3d information.

    Each column represents:
    - bbox_left
    - bbox_top
    - bbox_w
    - bbox_h
    - conf
    - class
    - bbox3d_left_x
    - bbox3d_left_y
    - bbox3d_left_z

    - bbox3d_right_x
    - bbox3d_right_y
    - bbox3d_right_z

    - bbox3d_from_camera_left_x
    - bbox3d_from_camera_left_y
    - bbox3d_from_camera_left_z

    - bbox3d_from_camera_right_x
    - bbox3d_from_camera_right_y
    - bbox3d_from_camera_right_z

    class_map:
    ----------
    A mapping from an object class number (in detections[:, 5]) to a class string name
    """

    detections: "torch.Tensor"
    class_map: "list[str] | None"
    detection_ids: "list[DetectionId]"


class Detection3D(Stage[Metadatum]):
    pass
