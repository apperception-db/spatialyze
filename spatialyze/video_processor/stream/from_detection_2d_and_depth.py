import numpy as np
import numpy.typing as npt
import torch

from ..utils.exhausted import exhausted
from ..utils.depth_to_3d import depth_to_3d
from ..video import Video
from .data_types import Detection2D, Detection3D, Skip, skip
from .stream import Stream


class FromDetection2DAndDepth(Stream[Detection3D]):
    def __init__(self, detections: Stream[Detection2D], depths: Stream[npt.NDArray]):
        self.detection2ds = detections
        self.depths = depths

    def _stream(self, video: Video):
        with torch.no_grad():
            for d2d, depth, frame in zip(
                self.detection2ds.stream(video),
                self.depths.stream(video),
                iter(video),
                strict=True
            ):
                if isinstance(d2d, Skip) or isinstance(depth, Skip):
                    yield skip
                    continue

                det, class_mapping, dids = d2d
                d3ds = []
                for detection in det:
                    bbox_left, bbox_top, bbox_right, bbox_bottom = detection[:4]

                    xc = int((bbox_left + bbox_right) / 2)
                    yc = int((bbox_top + bbox_bottom) / 2)

                    xl = int(bbox_left)
                    xr = int(bbox_right)

                    height, width = depth.shape

                    d = depth[
                        max(0, min(yc, height - 1)),
                        max(0, min(xc, width - 1)),
                    ]
                    intrinsic = frame.camera_intrinsic

                    point_from_camera_l = depth_to_3d(xl, yc, d, intrinsic)
                    rotated_offset_l = frame.camera_rotation.rotate(np.array(point_from_camera_l))
                    point_l = np.array(frame.camera_translation) + rotated_offset_l

                    point_from_camera_r = depth_to_3d(xr, yc, d, intrinsic)
                    rotated_offset_r = frame.camera_rotation.rotate(np.array(point_from_camera_r))
                    point_r = np.array(frame.camera_translation) + rotated_offset_r

                    d3d = [
                        *detection,
                        *point_l,
                        *point_r,
                        *point_from_camera_l,
                        *point_from_camera_r,
                    ]
                    d3ds.append(d3d)
                yield Detection3D(torch.tensor(d3ds, device=det.device), class_mapping, dids)
        self.end()
