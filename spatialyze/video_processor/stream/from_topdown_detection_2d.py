import cv2
import numpy as np
import torch

from ..types import Float2
from ..video import Video
from .data_types import Detection2D, Detection3D, Skip, skip
from .stream import Stream

width = 1920
height = 1080
src_points = np.array(
    [
        [0, 0],
        [width, 0],
        [width, height],
        [0, height],
    ],
    dtype="float32",
).reshape(-1, 1, 2)


class FromTopDownDetection2D(Stream[Detection3D]):
    def __init__(self, detections: Stream[Detection2D]):
        self.detection2ds = detections

    def _stream(self, video: Video):
        with torch.no_grad():
            for d2d, frame in zip(self.detection2ds.stream(video), video.camera_configs):
                if isinstance(d2d, Skip) or frame is None:
                    yield skip
                    continue

                det, class_mapping, dids = d2d
                if len(det) == 0:
                    # yield Detection3D(torch.tensor([], device=det.device), class_mapping, dids)
                    yield Detection3D(torch.tensor([]), class_mapping, dids)
                    continue

                # device = det.device
                if isinstance(det, torch.Tensor):
                    det = det.cpu().numpy()

                assert isinstance(frame, list)
                camera_frame = frame[:4]
                dst_points = np.array(camera_frame, dtype="float32").reshape(-1, 1, 2)
                H, _ = cv2.findHomography(src_points, dst_points)

                # d2d = det[:, :4].cpu().numpy()
                d2d = det[:, :4]

                _, d = det.shape
                N, _d = d2d.shape
                assert _d == 4

                tl = d2d[:, :2].copy()

                tr = d2d[:, :2].copy()
                tr[:, 0] += d2d[:, 2]

                bl = d2d[:, :2].copy()
                bl[:, 1] += d2d[:, 3]

                br = d2d[:, :2].copy()
                br += d2d[:, 2:4]

                points = np.concatenate([tl, tr, br, bl], axis=0, dtype="float32")
                assert (N * 4, 2) == points.shape, points.shape
                points = points.reshape(-1, 1, 2)
                assert (N * 4, 1, 2) == points.shape, points.shape
                # points = np.array(d2d[:, :2] + d2d[:, 2:4] / 2.0, dtype='float32').reshape(-1, 1, 2)
                # transformed_points = torch.tensor(cv2.perspectiveTransform(points, H), device=device)
                transformed_points = np.array(cv2.perspectiveTransform(points, H))
                # zeros = torch.zeros((N, 1), device=device)
                zeros = np.zeros((N, 1))

                tl = transformed_points[:N, 0, :]
                tr = transformed_points[N : 2 * N, 0, :]
                br = transformed_points[2 * N : 3 * N, 0, :]
                bl = transformed_points[3 * N : 4 * N, 0, :]

                d3d = np.concatenate(
                    [
                        det,
                        tl,
                        zeros,
                        tr,
                        zeros,
                        br,
                        zeros,
                        bl,
                        zeros,
                    ],
                    axis=1,
                )
                assert (N, (d + 12)) == d3d.shape, d3d.shape

                yield Detection3D(torch.from_numpy(d3d), class_mapping, dids)
