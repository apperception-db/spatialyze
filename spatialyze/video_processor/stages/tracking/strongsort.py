from pathlib import Path
from typing import Literal

import torch

from ...modules.yolo_tracker.trackers.multi_tracker_zoo import StrongSORT as _StrongSORT
from ...modules.yolo_tracker.trackers.multi_tracker_zoo import create_tracker
from ...modules.yolo_tracker.yolov5.utils.torch_utils import select_device
from ...payload import Payload
from ..decode_frame.decode_frame import DecodeFrame
from ..detection_2d.detection_2d import Detection2D
from .tracking import Tracking, TrackingResult

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
reid_weights = WEIGHTS / "osnet_x0_25_msmt17.pt"


class StrongSORT(Tracking):
    def __init__(
        self,
        method: "Literal['increment-ages', 'update-empty']" = "update-empty",
        cache: "bool" = True,
    ) -> None:
        super().__init__()
        self.cache = cache
        self.method: "Literal['increment-ages', 'update-empty']" = method
        # self.ss_benchmark = []


    def _run(self, payload: "Payload"):
        # load_data_start = time.time()
        detections = Detection2D.get(payload)
        assert detections is not None

        images = DecodeFrame.get(payload)
        assert images is not None
        # load_data_end = time.time()

        # init_start = time.time()
        metadata: "list[list[TrackingResult]]" = [[] for _ in range(len(payload.video))]
        device = select_device("")
        strongsort = create_tracker("strongsort", reid_weights, device, False)
        assert isinstance(strongsort, _StrongSORT)
        assert hasattr(strongsort, "tracker")
        assert hasattr(strongsort.tracker, "camera_update")
        assert hasattr(strongsort, "model")
        assert hasattr(strongsort.model, "warmup")
        curr_frame, prev_frame = None, None
        with torch.no_grad():
            strongsort.model.warmup()
            # init_end = time.time()

            # update_time = 0
            # skip_time = 0
            # tracking_start = time.time()
            assert len(detections) == len(images)
            for idx, ((det, _, dids), im0s) in enumerate(StrongSORT.tqdm(zip(detections, images))):
                im0 = im0s.copy()
                curr_frame = im0

                # update_start = time.time()
                # Always do camera update
                if prev_frame is not None and curr_frame is not None:
                    strongsort.tracker.camera_update(prev_frame, curr_frame, cache=self.cache)
                prev_frame = curr_frame
                # update_time += time.time() - update_start

                if payload.keep[idx] and len(det) != 0:
                    strongsort.update(det.cpu(), dids, im0)
                    continue

                # Skip if no detections or filtered frame
                # skip_start = time.time()
                if self.method == "increment-ages":
                    strongsort.increment_ages()
                elif self.method == "update-empty":
                    strongsort.update(torch.Tensor(0, 6), [], im0)
                else:
                    raise Exception(f"method {self.method} is not supported")
                # skip_time += time.time() - skip_start
            # tracking_end = time.time()

            # postprocess_start = time.time()
            for track in strongsort.tracker.tracks + strongsort.tracker.deleted_tracks:
                track_id = track.track_id
                assert isinstance(track_id, int), type(track_id)

                # Sort track by frame idx
                _track = sorted(
                    (
                        TrackingResult(did, track_id, conf)
                        for did, conf in zip(track.detection_ids, track.confs)
                    ),
                    key=lambda d: d.detection_id.frame_idx,
                )

                # Link track
                for before, after in zip(_track[:-1], _track[1:]):
                    before.next = after
                    after.prev = before

                # Add detections to metadata
                for tr in _track:
                    fid = tr.detection_id.frame_idx
                    metadata[fid].append(tr)
            # postprocess_end = time.time()

        # self.ss_benchmark.append({
        #     'file': payload.video.videofile,
        #     'load_data': load_data_end - load_data_start,
        #     'init': init_end - init_start,
        #     'tracking': tracking_end - tracking_start,
        #     'skip': skip_time,
        #     'update_camera': update_time,
        #     'postprocess': postprocess_end - postprocess_start,
        # })

        return None, {self.classname(): metadata}
