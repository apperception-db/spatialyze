from pathlib import Path

import numpy as np
import numpy.typing as npt
import torch

from ..modules.yolo_tracker.yolov5.models.common import DetectMultiBackend
from ..modules.yolo_tracker.yolov5.utils.augmentations import letterbox
from ..modules.yolo_tracker.yolov5.utils.general import (
    check_img_size,
    non_max_suppression,
    scale_boxes,
)
from ..modules.yolo_tracker.yolov5.utils.torch_utils import select_device
from ..stages.detection_2d.yolo_detection import class_mapping_to_list
from ..types import DetectionId
from ..video.video import Video
from .data_types import Detection2D, Skip, skip
from .stream import Stream

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
torch.hub.set_dir(str(WEIGHTS))


class Yolo(Stream[Detection2D]):
    def __init__(
        self,
        frames: Stream[npt.NDArray],
        half: bool = False,
        conf_thres: float = 0.25,
        iou_thres: float = 0.45,
        max_det: int = 1000,
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
    ):
        self.device = select_device("")
        try:
            model = torch.hub.load("ultralytics/yolov5", "yolov5s", verbose=False, _verbose=False)
            self.model: "DetectMultiBackend" = model.model.to(self.device)
        except BaseException:
            model = torch.hub.load(
                "ultralytics/yolov5", "yolov5s", verbose=False, _verbose=False, force_reload=True
            )
            self.model: "DetectMultiBackend" = model.model.to(self.device)
        stride, pt = self.model.stride, self.model.pt
        assert isinstance(stride, int), type(stride)
        assert isinstance(pt, bool), type(pt)
        self.pt = pt
        self.imgsz = check_img_size((640, 640), s=int(stride))
        self.half = half
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.max_det = max_det
        self.classes = classes
        self.agnostic_nms = agnostic_nms
        self.augment = augment

        self.frames = frames

    def _stream(self, video: Video):
        with torch.no_grad():
            _names = self.model.names

            assert isinstance(_names, dict), type(_names)
            names: list[str] = class_mapping_to_list(_names)
            self.model.eval()

            assert isinstance(self.imgsz, list), type(self.imgsz)
            self.model.warmup(imgsz=(1, 3, *self.imgsz))  # warmup

            for frame_idx, im0 in enumerate(self.frames.stream(video)):
                if isinstance(im0, Skip):
                    yield skip
                    continue

                im, _, _ = letterbox(im0, self.imgsz, stride=32, auto=True)  # padded resize
                im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
                im = np.ascontiguousarray(im)  # contiguous

                # t1 = time_sync()
                im = torch.from_numpy(im).to(self.device)
                im = im.half() if self.half else im.float()
                im /= 255.0  # 0 - 255 to 0.0 - 1.0
                if len(im.shape) == 3:
                    im = im[None]  # expand for batch dim

                # Inference
                pred = self.model(im, augment=self.augment)

                # Apply NMS
                pred = non_max_suppression(
                    pred,
                    self.conf_thres,
                    self.iou_thres,
                    self.classes,
                    self.agnostic_nms,
                    max_det=self.max_det,
                )

                # Process detections
                assert isinstance(pred, list), type(pred)
                assert len(pred) == 1, len(pred)
                det = pred[0]
                assert isinstance(det, torch.Tensor), type(det)
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()
                yield Detection2D(
                    det, names, [DetectionId(frame_idx, order) for order in range(len(det))]
                )
