# import time
import os
import sys
from pathlib import Path

import numpy as np
import torch

from ...cache import cache
from ...payload import Payload
from ...types import DetectionId
from ..decode_frame.decode_frame import DecodeFrame
from ..detection_2d.detection_2d import Detection2D
from .tracking import Tracking, TrackingResult

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"

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


def xyxy2xywh(x):
    # Convert nx4 boxes from [x1, y1, x2, y2] to [x, y, w, h] where xy1=top-left, xy2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2  # x center
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2  # y center
    y[:, 2] = x[:, 2] - x[:, 0]  # width
    y[:, 3] = x[:, 3] - x[:, 1]  # height
    return y


def select_device(device="", batch_size=0, newline=True):
    # device = 'cpu' or '0' or '0,1,2,3'
    # s = f'YOLOv5 🚀 torch {torch.__version__} '  # string
    device = str(device).strip().lower().replace("cuda:", "")  # to string, 'cuda:0' to '0'
    cpu = device == "cpu"
    if cpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # force torch.cuda.is_available() = False
    elif device:  # non-cpu device requested
        os.environ["CUDA_VISIBLE_DEVICES"] = device  # set environment variable
        assert (
            torch.cuda.is_available()
        ), f"CUDA unavailable, invalid device {device} requested"  # check availability

    cuda = not cpu and torch.cuda.is_available()
    if cuda:
        devices = (
            device.split(",") if device else "0"
        )  # range(torch.cuda.device_count())  # i.e. 0,1,6,7
        n = len(devices)  # device count
        if n > 1 and batch_size > 0:  # check batch_size is divisible by device_count
            assert batch_size % n == 0, f"batch-size {batch_size} not multiple of GPU count {n}"
        # space = ' ' * (len(s) + 1)
        # for i, d in enumerate(devices):
        #     p = torch.cuda.get_device_properties(i)
        #     s += f"{'' if i == 0 else space}CUDA:{d} ({p.name}, {p.total_memory / 1024 ** 2:.0f}MiB)\n"  # bytes to MB
    # else:
    #     s += 'CPU\n'

    # if not newline:
    #     s = s.rstrip()
    # LOGGER.info(s.encode().decode('ascii', 'ignore') if platform.system() == 'Windows' else s)  # emoji-safe
    return torch.device("cuda:0" if cuda else "cpu")


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
                if not payload.keep[idx] or len(det) == 0:
                    deepsort.increment_ages()
                    continue

                im0 = im0s.copy()

                xywhs = xyxy2xywh(det[:, 0:4])
                assert isinstance(xywhs, torch.Tensor), type(xywhs)
                confs = det[:, 4]
                clss = det[:, 5]

                deepsort.update(xywhs.cpu(), confs.cpu(), clss.cpu(), im0, dids)

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
