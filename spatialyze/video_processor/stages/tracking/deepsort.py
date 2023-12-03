# import time
from pathlib import Path

import torch

from ...cache import cache
from ...modules.yolo_deepsort.deep_sort.deep_sort import DeepSort
from ...modules.yolo_deepsort.deep_sort.utils.parser import get_config
from ...modules.yolo_deepsort.yolov5.utils.general import xyxy2xywh
from ...modules.yolo_deepsort.yolov5.utils.torch_utils import select_device
from ...payload import Payload
from ...types import DetectionId
from ..decode_frame.decode_frame import DecodeFrame
from ..detection_2d.detection_2d import Detection2D
from .tracking import Tracking, TrackingResult

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
reid_weights = WEIGHTS / "osnet_x0_25_msmt17.pt"


class DeepSORT(Tracking):
    def __init__(self):
        super().__init__()
        # self.ss_benchmark = []

    @cache
    def _run(self, payload: "Payload"):
        # load_data_start = time.time()
        detections = Detection2D.get(payload)
        assert detections is not None

        images = DecodeFrame.get(payload)
        assert images is not None
        # load_data_end = time.time()

        metadata: "list[list[TrackingResult]]" = [[] for _ in range(len(payload.video))]

        with torch.no_grad():
            device = select_device("0")
            # initialize deepsort
            cfg = get_config()
            cfg.merge_from_file("deep_sort/configs/deep_sort.yaml")
            deepsort = DeepSort(
                model_type="osnet_x0_25",
                device=device,
                max_dist=cfg.DEEPSORT.MAX_DIST,
                max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                max_age=cfg.DEEPSORT.MAX_AGE,
                n_init=cfg.DEEPSORT.N_INIT,
                nn_budget=cfg.DEEPSORT.NN_BUDGET,
            )

            assert len(detections) == len(images)
            for idx, ((det, _, dids), im0s) in enumerate(DeepSORT.tqdm(zip(detections, images))):
                im0 = im0s.copy()

                xywhs = xyxy2xywh(det[:, 0:4])
                assert isinstance(xywhs, torch.Tensor), type(xywhs)
                confs = det[:, 4]
                clss = det[:, 5]

                if payload.keep[idx] and len(det) != 0:
                    deepsort.update(xywhs.cpu(), confs.cpu(), clss.cpu(), im0, dids)
                    continue

                deepsort.increment_ages()

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
