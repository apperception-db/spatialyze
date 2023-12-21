from ctypes import (
    CDLL,
    POINTER,
    RTLD_GLOBAL,
    Structure,
    c_char_p,
    c_float,
    c_int,
    c_void_p,
    pointer,
)
from pathlib import Path
from typing import NamedTuple

import torch
from tqdm.notebook import tqdm

from ..modules.yolo_tracker.yolov5.utils.torch_utils import select_device
from ..types import DetectionId, Float4
from ..video.video import Video
from .data_types import Detection2D, Skip, skip
from .stream import Stream

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent
DATA = SPATIALYZE / "data"
SKYQUERY = DATA / "skyquery"
CAR_MODEL = SKYQUERY / "car-model"
CFG = CAR_MODEL / "yolov3.cfg"
WEIGHTS = CAR_MODEL / "yolov3.best"

DARKNET = SPATIALYZE / "spatialyze" / "video_processor" / "modules" / "darknet"
LIBDARKNET = DARKNET / "libdarknet.so"


class BOX(Structure):
    _fields_ = [("x", c_float), ("y", c_float), ("w", c_float), ("h", c_float)]


class DETECTION(Structure):
    _fields_ = [
        ("bbox", BOX),
        ("classes", c_int),
        ("prob", POINTER(c_float)),
        ("mask", POINTER(c_float)),
        ("objectness", c_float),
        ("sort_class", c_int),
    ]


class IMAGE(Structure):
    _fields_ = [("w", c_int), ("h", c_int), ("c", c_int), ("data", POINTER(c_float))]


try:
    lib = CDLL(str(LIBDARKNET), RTLD_GLOBAL)
    lib.network_width.argtypes = [c_void_p]
    lib.network_width.restype = c_int
    lib.network_height.argtypes = [c_void_p]
    lib.network_height.restype = c_int

    set_gpu = lib.cuda_set_device
    set_gpu.argtypes = [c_int]

    get_network_boxes = lib.get_network_boxes
    get_network_boxes.argtypes = [
        c_void_p,
        c_int,
        c_int,
        c_float,
        c_float,
        POINTER(c_int),
        c_int,
        POINTER(c_int),
    ]
    get_network_boxes.restype = POINTER(DETECTION)

    free_detections = lib.free_detections
    free_detections.argtypes = [POINTER(DETECTION), c_int]

    load_net = lib.load_network
    load_net.argtypes = [c_char_p, c_char_p, c_int]
    load_net.restype = c_void_p

    do_nms_obj = lib.do_nms_obj
    do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

    free_image = lib.free_image
    free_image.argtypes = [IMAGE]

    load_image = lib.load_image_color
    load_image.argtypes = [c_char_p, c_int, c_int]
    load_image.restype = IMAGE

    predict_image = lib.network_predict_image
    predict_image.argtypes = [c_void_p, IMAGE]
    predict_image.restype = POINTER(c_float)

    set_gpu(0)

    def detect(net, meta, image, thresh=0.5, hier_thresh=0.5, nms=0.45):
        im = load_image(image, 0, 0)
        num = c_int(0)
        pnum = pointer(num)
        predict_image(net, im)
        dets = get_network_boxes(net, im.w, im.h, thresh, hier_thresh, None, 0, pnum)
        num = pnum[0]
        if nms:
            do_nms_obj(dets, num, meta.classes, nms)

        res: list[tuple[str, float, Float4]] = []
        for j in range(num):
            for i in range(meta.classes):
                if dets[j].prob[i] > 0:
                    b = dets[j].bbox
                    res.append((meta.names[i], dets[j].prob[i], (b.x, b.y, b.w, b.h)))
        res = sorted(res, key=lambda x: -x[1])
        free_image(im)
        free_detections(dets, num)
        return res

except OSError:

    def load_net(cfg, weights, gpu):
        raise OSError("libdarknet.so not found")


class YoloMeta(NamedTuple):
    classes: int
    names: list[str]


YOLO_META = YoloMeta(1, ["car"])


class DetectTopDownCars(Stream[Detection2D]):
    def __init__(
        self,
        frames: Stream[str],
    ):
        self.device = select_device("")
        self.net = load_net(str(CFG).encode("utf-8"), str(WEIGHTS).encode("utf-8"), 0)
        self.meta = YOLO_META
        self.frames = frames

    def _stream(self, video: Video):
        with torch.no_grad():
            for frame_idx, im0 in tqdm(
                enumerate(self.frames.stream(video)),
                total=len(video.camera_configs),
            ):
                if isinstance(im0, Skip):
                    yield skip
                    continue

                r: list[tuple[str, float, Float4]] = detect(
                    self.net, self.meta, im0.encode("utf-8"), thresh=0.3
                )
                _dets = [(x, y, w, h, conf, 0) for _, conf, (x, y, w, h) in r]
                # dets: torch.Tensor = torch.tensor(_dets, dtype=torch.float32, device=self.device)
                dets = torch.tensor(_dets, dtype=torch.float32)
                yield Detection2D(
                    dets, ["car"], [DetectionId(frame_idx, order) for order in range(len(_dets))]
                )
        self.end()
