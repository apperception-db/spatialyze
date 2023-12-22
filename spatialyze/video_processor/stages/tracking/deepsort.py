# import time
import sys
from pathlib import Path

import torch

from ...payload import Payload
from ...types import DetectionId
from ...utils.xyxy2xywh import xyxy2xywh
from ..decode_frame.decode_frame import DecodeFrame
from ..detection_2d.detection_2d import Detection2D
from .tracking import Tracking, TrackingResult

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"

DEEPSORT = (
    SPATIALYZE
    / "spatialyze"
    / "video_processor"
    / "modules"
    / "yolo_deepsort"
    / "deep_sort"
    / "configs"
    / "deep_sort.yaml"
)

TORCHREID = (
    SPATIALYZE
    / "spatialyze"
    / "video_processor"
    / "modules"
    / "yolo_deepsort"
    / "deep_sort"
    / "deep"
    / "reid"
)
sys.path.append(str(TORCHREID))

from ...modules.yolo_deepsort.deep_sort.deep_sort import DeepSort
from ...modules.yolo_deepsort.deep_sort.utils.parser import get_config
from ...modules.yolo_tracker.yolov5.utils.torch_utils import select_device


class DeepSORT(Tracking):
    def __init__(self):
        super().__init__()
        # self.ss_benchmark = []

    def _run(self, payload: "Payload"):
        # load_data_start = time.time()
        detections = Detection2D.get(payload)
        assert detections is not None

        images = DecodeFrame.get(payload)
        assert images is not None
        # load_data_end = time.time()

        metadata: "list[list[TrackingResult]]" = [[] for _ in range(len(payload.video))]

        with torch.no_grad():
            device = select_device("")
            # initialize deepsort
            cfg = get_config()
            cfg.merge_from_file(str(DEEPSORT))
            assert hasattr(cfg, "DEEPSORT"), (type(cfg), dir(cfg))
            cfgds = getattr(cfg, "DEEPSORT")
            assert hasattr(cfgds, "MAX_DIST"), (type(cfgds), dir(cfgds))
            assert hasattr(cfgds, "MAX_IOU_DISTANCE"), (type(cfgds), dir(cfgds))
            assert hasattr(cfgds, "MAX_AGE"), (type(cfgds), dir(cfgds))
            assert hasattr(cfgds, "N_INIT"), (type(cfgds), dir(cfgds))
            assert hasattr(cfgds, "NN_BUDGET"), (type(cfgds), dir(cfgds))
            deepsort = DeepSort(
                model_type="osnet_x0_25",
                device=device,
                max_dist=getattr(cfgds, "MAX_DIST"),
                max_iou_distance=getattr(cfgds, "MAX_IOU_DISTANCE"),
                max_age=getattr(cfgds, "MAX_AGE"),
                n_init=getattr(cfgds, "N_INIT"),
                nn_budget=getattr(cfgds, "NN_BUDGET"),
            )

            assert len(detections) == len(images)
            for idx, ((det, _, dids), im0s) in enumerate(DeepSORT.tqdm(zip(detections, images))):
                if not payload.keep[idx] or len(det) == 0:
                    deepsort.increment_ages()
                    continue

                im0 = im0s.copy()

                xywhs = xyxy2xywh(det[:, 0:4])
                assert isinstance(xywhs, torch.Tensor), type(xywhs)
                confs = det[:, 4]
                clss = det[:, 5]

                deepsort.update(xywhs.cpu(), confs.cpu(), clss.cpu(), dids, im0)

            # postprocess_start = time.time()
            for track in deepsort.tracker.tracks + deepsort.tracker.deleted_tracks:
                track_id = track.track_id
                assert isinstance(track_id, int), type(track_id)

                def tracking_result(did_conf: tuple[DetectionId, float]):
                    did, conf = did_conf
                    return TrackingResult(did, track_id, conf)

                # Sort track by frame idx
                _track = sorted(
                    map(tracking_result, zip(track.detection_ids, track.confs)), key=frame_idx
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


def frame_idx(d: TrackingResult):
    return d.detection_id.frame_idx
