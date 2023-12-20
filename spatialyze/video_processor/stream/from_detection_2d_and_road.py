import numpy as np
import numpy.typing as npt
import torch
from pyquaternion import Quaternion

from ..stages.detection_3d.from_detection_2d_and_road import (
    TO_BOTTOM_LEFT,
    TO_BOTTOM_RIGHT,
)
from ..video import Video
from .data_types import Detection2D, Detection3D, Skip, skip
from .stream import Stream


class FromDetection2DAndRoad(Stream[Detection3D]):
    def __init__(self, detections: Stream[Detection2D]):
        self.detection2ds = detections

    def _stream(self, video: Video):
        with torch.no_grad():
            for d2d, frame in zip(self.detection2ds.stream(video), iter(video), strict=True):
                if isinstance(d2d, Skip):
                    yield skip
                    continue

                det, class_mapping, dids = d2d
                if len(det) == 0:
                    yield Detection3D(torch.tensor([], device=det.device), class_mapping, dids)
                    continue

                device = det.device
                [[fx, s, x0], [_, fy, y0], [_, _, _]] = frame.camera_intrinsic
                rotation = frame.camera_rotation
                translation = np.array(frame.camera_translation)

                _, d = det.shape

                d2dt = det.T[:4, :].cpu().numpy()
                assert isinstance(d2dt, np.ndarray)

                _d, N = d2dt.shape
                assert _d == 4

                # TODO: should it be a 2D bbox in 3D?
                bottoms = np.concatenate(
                    [
                        TO_BOTTOM_LEFT @ d2dt,
                        TO_BOTTOM_RIGHT @ d2dt,
                    ],
                    axis=1,
                )
                assert (2, N * 2) == bottoms.shape, ((2, N * 2), bottoms.shape)

                # iintrinsic = np.array([
                #     [1/fx, -s/(fx*fy), (s * y0 - fy * x0) / (fx * fy)],
                #     [0   , 1 / fy    , -y0 / fy                      ],
                #     [0   , 0         , 1                             ],
                # ])
                # TODO: use matrix multiplication with K^-1
                directions = np.stack(
                    (
                        (bottoms[0] / fx)
                        - (s * bottoms[1] / (fx * fy))
                        + ((s * y0) / (fx * fy))
                        - (x0 / fx),
                        (bottoms[1] - y0) / fy,
                        np.ones(N * 2),
                    )
                )
                assert (3, N * 2) == directions.shape, ((3, N * 2), directions.shape)

                rotated_directions = rotate(directions, rotation)

                # find t that z=0
                ts = -translation[2] / rotated_directions[2, :]

                points = rotated_directions * ts + translation[:, np.newaxis]
                points_from_camera = rotate(points - translation[:, np.newaxis], rotation.inverse)

                bbox3d = np.concatenate(
                    (
                        points[:, :N],
                        points[:, N:],
                    ),
                    axis=0,
                ).T
                assert (N, 6) == bbox3d.shape, bbox3d.shape

                bbox3d_from_camera = np.concatenate(
                    (
                        points_from_camera[:, :N],
                        points_from_camera[:, N:],
                    ),
                    axis=0,
                ).T
                assert (N, 6) == bbox3d_from_camera.shape, bbox3d_from_camera.shape

                d3d = torch.concatenate(
                    (
                        det,
                        torch.tensor(bbox3d, device=device),
                        torch.tensor(bbox3d_from_camera, device=device),
                    ),
                    dim=1,
                )
                assert (N, (d + 12)) == d3d.shape, d3d.shape

                yield Detection3D(d3d, class_mapping, dids)
        self.end()


def rotate(vectors: npt.NDArray, rotation: Quaternion) -> npt.NDArray:
    """Rotate 3D Vector by rotation quaternion.
    Params:
        vectors: (3 x N) 3-vectors each specified as any ordered
            sequence of 3 real numbers corresponding to x, y, and z values.
        rotation: A rotation quaternion.

    Returns:
        The rotated vectors (3 x N).
    """
    return rotation.unit.rotation_matrix @ vectors


def conj(q: npt.NDArray) -> npt.NDArray:
    return np.concatenate([q[0:1, :], -q[1:, :]])
