import os
import sys
from pathlib import Path

import numpy as np
import numpy.typing as npt
import torch

from ..camera_config import CameraConfig
from ..types import DetectionId
from ..video import Video
from .data_types import Detection2D, Detection3D, Skip
from .stream import Stream
from .strongsort import TrackingResult

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
REID_WEIGHTS = WEIGHTS / "osnet_x0_25_msmt17.pt"
EMPTY_DETECTION = torch.Tensor(0, 6)

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

from ..modules.yolo_deepsort.deep_sort.deep_sort import DeepSort
from ..modules.yolo_deepsort.deep_sort.sort.track import Track
from ..modules.yolo_deepsort.deep_sort.utils.parser import get_config


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
    return torch.device("cuda:0" if cuda else "cpu")


class DeepSORT(Stream[list[TrackingResult]]):
    def __init__(
        self, detections: Stream[Detection2D] | Stream[Detection3D], frames: Stream[npt.NDArray]
    ):
        self.detection2ds = detections
        self.frames = frames

    def _stream(self, video: Video):
        with torch.no_grad():
            device = select_device("0")
            # initialize deepsort
            cfg = get_config()
            cfg.merge_from_file(str(DEEPSORT))
            assert hasattr(cfg, "DEEPSORT"), (type(cfg), dir(cfg))
            DEEPSORT_ = getattr(cfg, "DEEPSORT")
            deepsort = DeepSort(
                model_type="osnet_x0_25",
                device=device,
                max_dist=DEEPSORT_.MAX_DIST,
                max_iou_distance=DEEPSORT_.MAX_IOU_DISTANCE,
                max_age=DEEPSORT_.MAX_AGE,
                n_init=DEEPSORT_.N_INIT,
                nn_budget=DEEPSORT_.NN_BUDGET,
            )

            deleted_tracks_idx = 0
            saved_detections: list[dict[int, torch.Tensor]] = []
            classes: list[str] | None = None
            for idx, (detection, im0s) in enumerate(
                zip(self.detection2ds.stream(video), self.frames.stream(video))
            ):
                # assert not isinstance(im0s, Skip), type(im0s)

                if isinstance(detection, Skip) or len(detection[0]) == 0:
                    deepsort.increment_ages()
                    saved_detections.append({})
                else:
                    det, _classes, dids = detection
                    # print(det.shape)
                    # print(det.shape)
                    if _classes is not None:
                        classes = _classes
                    im0 = im0s.copy()

                    xywhs = xyxy2xywh(det[:, 0:4])
                    assert isinstance(xywhs, torch.Tensor), type(xywhs)
                    confs = det[:, 4]
                    cls = det[:, 5]

                    det = det.cpu()
                    # assert all(idx == did.frame_idx for did in dids), dids
                    # assert all(len(det) > int(did.obj_order) for did in dids), dids
                    deepsort.update(xywhs.cpu(), confs.cpu(), cls.cpu(), dids, im0)
                    saved_detections.append({int(did.obj_order): dt for dt, did in zip(det, dids)})

                deleted_tracks = deepsort.tracker.deleted_tracks
                while deleted_tracks_idx < len(deleted_tracks):
                    yield _process_track(
                        deleted_tracks[deleted_tracks_idx],
                        saved_detections,
                        classes,
                        video.camera_configs,
                    )
                    deleted_tracks_idx += 1
            for track in deepsort.tracker.tracks:
                yield _process_track(track, saved_detections, classes, video.camera_configs)


def _process_track(
    track: Track,
    detections: list[dict[int, torch.Tensor]],
    clss: list[str] | None,
    camera_configs: list[CameraConfig],
):
    tid = track.track_id
    assert isinstance(tid, int), type(tid)

    clss = clss or []

    def tracking_result(did_conf: tuple[DetectionId, float]):
        did, conf = did_conf
        fid, oid = did
        assert isinstance(oid, int), type(oid)
        bbox = detections[fid][oid]
        cls = int(bbox[5])
        return TrackingResult(
            did, tid, conf, detections[fid][oid], clss[cls], camera_configs[fid].timestamp
        )

    # Sort track by frame idx
    _track = map(tracking_result, zip(track.detection_ids, track.confs))
    _track = sorted(_track, key=lambda d: d.detection_id.frame_idx)

    # Link track
    for before, after in zip(_track[:-1], _track[1:]):
        before.next = after
        after.prev = before

    return _track
