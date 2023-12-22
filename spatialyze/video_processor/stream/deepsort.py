import os
import sys
from pathlib import Path

import numpy.typing as npt
import torch

from ...data_types.camera_config import CameraConfig
from ..types import DetectionId
from ..utils.xyxy2xywh import xyxy2xywh
from ..video import Video
from .data_types import Detection2D, Detection3D, Skip
from .stream import Stream
from .strongsort import TrackingResult

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
REID_WEIGHTS = WEIGHTS / "osnet_x0_25_msmt17.pt"
EMPTY_DETECTION = torch.Tensor(0, 6)

if not os.path.exists(WEIGHTS):
    os.makedirs(WEIGHTS)

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
from ..modules.yolo_tracker.yolov5.utils.torch_utils import select_device

MAX_DIST = "MAX_DIST"
MAX_IOU_DISTANCE = "MAX_IOU_DISTANCE"
MAX_AGE = "MAX_AGE"
N_INIT = "N_INIT"
NN_BUDGET = "NN_BUDGET"


class DeepSORT(Stream[list[TrackingResult]]):
    def __init__(
        self,
        detections: Stream[Detection2D] | Stream[Detection3D],
        frames: Stream[npt.NDArray],
    ):
        self.detection2ds = detections
        self.frames = frames

    def _stream(self, video: Video):
        with torch.no_grad():
            device = select_device("")
            # initialize deepsort
            cfg = get_config()
            cfg.merge_from_file(str(DEEPSORT))
            assert hasattr(cfg, "DEEPSORT"), (type(cfg), dir(cfg))
            cfg = getattr(cfg, "DEEPSORT")
            assert hasattr(cfg, MAX_DIST), (type(cfg), dir(cfg))
            assert hasattr(cfg, MAX_IOU_DISTANCE), (type(cfg), dir(cfg))
            assert hasattr(cfg, MAX_AGE), (type(cfg), dir(cfg))
            assert hasattr(cfg, N_INIT), (type(cfg), dir(cfg))
            assert hasattr(cfg, NN_BUDGET), (type(cfg), dir(cfg))
            deepsort = DeepSort(
                model_type="osnet_x0_25",
                device=device,
                max_dist=getattr(cfg, MAX_DIST),
                max_iou_distance=getattr(cfg, MAX_IOU_DISTANCE),
                max_age=getattr(cfg, MAX_AGE),
                n_init=getattr(cfg, N_INIT),
                nn_budget=getattr(cfg, NN_BUDGET),
            )

            saved_detections: list[dict[int, torch.Tensor] | None] = []
            classes: list[str] | None = None
            for detection, im0s in zip(
                self.detection2ds.stream(video),
                self.frames.stream(video),
                strict=True,
            ):
                if isinstance(detection, Skip) or len(detection[0]) == 0:
                    deepsort.increment_ages()
                    saved_detections.append(None)
                else:
                    det, _classes, dids = detection
                    # print(det.shape)
                    # print(det.shape)
                    if _classes is not None:
                        classes = _classes

                    assert not isinstance(im0s, Skip), type(im0s)
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
                deepsort.tracker.deleted_tracks = []
                for track in deleted_tracks:
                    yield _process_track(
                        track,
                        saved_detections,
                        classes,
                        video.camera_configs,
                    )
            for track in deepsort.tracker.tracks:
                yield _process_track(track, saved_detections, classes, video.camera_configs)
        self.end()


def _process_track(
    track: Track,
    detections: list[dict[int, torch.Tensor] | None],
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
        detection = detections[fid]
        assert detection is not None, (fid, oid, detection)
        bbox = detection[oid]
        del detection[oid]
        if len(detection) == 0:
            detection = None
        cls = int(bbox[5])
        return TrackingResult(did, tid, conf, bbox, clss[cls], camera_configs[fid].timestamp)

    # Sort track by frame idx
    _track = map(tracking_result, zip(track.detection_ids, track.confs))
    _track = sorted(_track, key=lambda d: d.detection_id.frame_idx)

    # Link track
    for before, after in zip(_track[:-1], _track[1:]):
        before.next = after
        after.prev = before

    return _track
