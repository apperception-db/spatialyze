import numpy as np
import numpy.typing as npt
from bitarray import bitarray

from ...payload import Payload
from ...utils.depth_to_3d import depth_to_3d
from ..depth_estimation import DepthEstimation
from ..tracking_2d.tracking_2d import Tracking2D
from .tracking_3d import Metadatum, Tracking3D, Tracking3DResult


class FromTracking2DAndDepth(Tracking3D):
    def _run(self, payload: "Payload") -> "tuple[bitarray | None, dict[str, list] | None]":
        metadata: "list[Metadatum]" = []
        trajectories: "dict[int, list[Tracking3DResult]]" = {}

        depths = DepthEstimation.get(payload.metadata)
        assert depths is not None

        trackings = Tracking2D.get(payload.metadata)
        assert trackings is not None

        for k, depth, tracking, frame in zip(payload.keep, depths, trackings, payload.video):
            if not k or tracking is None or depth is None:
                metadata.append(dict())
                continue

            trackings3d: "dict[int, Tracking3DResult]" = {}
            for object_id, t in tracking.items():
                x = int(t.bbox_left + (t.bbox_w / 2))
                y = int(t.bbox_top + (t.bbox_h / 2))
                idx = t.frame_idx
                height, width = depth.shape
                d = depth[min(y, height - 1), min(x, width - 1)]
                camera = payload.video[idx]
                intrinsic = camera.camera_intrinsic

                point_from_camera = depth_to_3d(x, y, d, intrinsic)
                rotated_offset = camera.camera_rotation.rotate(np.array(point_from_camera))
                point: "npt.NDArray" = np.array(camera.camera_translation) + rotated_offset
                trackings3d[object_id] = Tracking3DResult(
                    t.frame_idx,
                    t.detection_id,
                    t.object_id,
                    point_from_camera,
                    tuple(point.tolist()),
                    t.bbox_left,
                    t.bbox_top,
                    t.bbox_w,
                    t.bbox_h,
                    t.object_type,
                    frame.timestamp,
                )
                if object_id not in trajectories:
                    trajectories[object_id] = []
                trajectories[object_id].append(trackings3d[object_id])
            metadata.append(trackings3d)

        for trajectory in trajectories.values():
            last = len(trajectory) - 1
            for i, traj in enumerate(trajectory):
                if i > 0:
                    traj.prev = trajectory[i - 1]
                if i < last:
                    traj.next = trajectory[i + 1]

        return None, {self.classname(): metadata}
