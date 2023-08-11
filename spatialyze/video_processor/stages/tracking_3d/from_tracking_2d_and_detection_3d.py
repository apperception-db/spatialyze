from bitarray import bitarray

from ...payload import Payload
from ..detection_3d import Detection3D
from ..tracking_2d.tracking_2d import Tracking2D
from .tracking_3d import Metadatum, Tracking3D, Tracking3DResult


class FromTracking2DAndDetection3D(Tracking3D):
    def _run(self, payload: "Payload") -> "tuple[bitarray | None, dict[str, list] | None]":
        metadata: "list[Metadatum]" = []
        trajectories: "dict[int, list[Tracking3DResult]]" = {}

        trackings = Tracking2D.get(payload.metadata)
        assert trackings is not None

        detections = Detection3D.get(payload.metadata)
        assert detections is not None

        for k, detection, tracking, frame in zip(
            payload.keep, detections, trackings, payload.video
        ):
            dets, _, dids = detection
            if not k or tracking is None or detection is None:
                metadata.append(dict())
                continue

            points_left = dets[:, 6:9]
            points_right = dets[:, 9:12]
            points = (points_left + points_right) / 2

            points_from_camera_left = dets[:, 12:15]
            points_from_camera_right = dets[:, 15:18]
            points_from_camera = (points_from_camera_left + points_from_camera_right) / 2

            detection_map = {
                did: (det, p, pfc)
                for det, p, pfc, did
                in zip(dets, points.tolist(), points_from_camera.tolist(), dids)
            }
            trackings3d: "dict[int, Tracking3DResult]" = {}
            for object_id, t in tracking.items():
                did = t.detection_id
                det, p, pfc = detection_map[did]

                trackings3d[object_id] = Tracking3DResult(
                    t.frame_idx,
                    t.detection_id,
                    t.object_id,
                    pfc,
                    p,
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
