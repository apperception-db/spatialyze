from pathlib import Path
from typing import Literal
import time

import torch

from ...payload import Payload
from ...types import DetectionId
from ..detection_2d.detection_2d import Detection2D
from ..tracking.strongsort import StrongSORT as Tracking
from ..tracking.tracking import TrackingResult
from .tracking_2d import Metadatum, Tracking2D, Tracking2DResult

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
reid_weights = WEIGHTS / "osnet_x0_25_msmt17.pt"


class StrongSORT(Tracking2D):
    def __init__(
        self,
        method: "Literal['increment-ages', 'update-empty']" = "update-empty",
        cache: "bool" = True,
    ) -> None:
        super().__init__()
        self._benchmark = []
        self.tracking = Tracking(method=method, cache=cache)
        if hasattr(self.tracking, "ss_benchmark"):
            self.ss_benchmark = getattr(self.tracking, "ss_benchmark")

    def _run(self, payload: "Payload"):
        _, _metadata = self.tracking._run(payload)

        trackings = self.tracking.get(_metadata)
        assert trackings is not None

        detections = Detection2D.get(payload)
        assert detections is not None

        metadata: "list[dict[int, Tracking2DResult]]" = []
        trajectories: "dict[int, list[Tracking2DResult]]" = {}

        names = detections[0][1]
        assert names is not None
        
        frame_process_time = []

        for (dets, _, dids), ts in StrongSORT.tqdm(zip(detections, trackings)):
            current_process_start = time.time()
            d2ds_map: "dict[DetectionId, torch.Tensor]" = {}
            for d2d, did in zip(dets, dids):
                d2ds_map[did] = d2d

            metadatum: "Metadatum" = {}
            for t in ts:
                d2d = d2ds_map[t.detection_id]
                oid, tr = tracking_result(d2d, t, names)

                metadatum[oid] = tr

                if oid not in trajectories:
                    trajectories[oid] = []
                trajectories[oid].append(tr)
            metadata.append(metadatum)
            frame_process_time.append(time.time() - current_process_start)

        for trajectory in trajectories.values():
            for before, after in zip(trajectory[:-1], trajectory[1:]):
                before.next = after
                after.prev = before
                
        self._benchmark.append(
            {
                "name": payload.video.videofile,
                "frame_process_time": frame_process_time,
            }
        )

        return None, {self.classname(): metadata}


def tracking_result(d2d: "torch.Tensor", t: "TrackingResult", names: "list[str]"):
    bbox = d2d[:4].tolist()
    bl, bt, br, bb = bbox
    cls = int(d2d[5])
    oid = t.object_id

    return oid, Tracking2DResult(
        t.detection_id.frame_idx,
        t.detection_id,
        oid,
        bl,
        bt,
        br - bl,
        bb - bt,
        names[cls],
        t.confidence,
    )
