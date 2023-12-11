import os
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Iterator, NamedTuple

# limit the number of cpus used by high performance libraries
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import cv2
import numpy as np
import numpy.typing as npt
import torch

from ...modules.yolo_tracker.yolov5.utils.augmentations import letterbox
from ...modules.yolo_tracker.yolov5.utils.general import (
    check_img_size,
    non_max_suppression,
    scale_boxes,
)
from ...modules.yolo_tracker.yolov5.utils.torch_utils import select_device
from ...stages.decode_frame.decode_frame import DecodeFrame
from ...types import DetectionId
from .detection_2d import Detection2D, Metadatum

if TYPE_CHECKING:
    from ...modules.yolo_tracker.yolov5.models.common import DetectMultiBackend
    from ...payload import Payload


FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
torch.hub.set_dir(str(WEIGHTS))


class YoloDetection(Detection2D):
    def __init__(
        self,
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
            model = torch.hub.load("ultralytics/yolov5", "yolov5n", verbose=False, _verbose=False)
            self.model: "DetectMultiBackend" = model.model.to(self.device)
        except BaseException:
            model = torch.hub.load(
                "ultralytics/yolov5", "yolov5n", verbose=False, _verbose=False, force_reload=True
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

    # @cache
    def _run(self, payload: "Payload"):
        if YoloDetection.progress:
            print(self.device)
        with torch.no_grad():
            _names = self.model.names
            assert isinstance(_names, dict), type(_names)
            names: "list[str]" = class_mapping_to_list(_names)
            dataset = LoadImages(payload, img_size=self.imgsz, auto=self.pt)
            self.model.eval()
            assert isinstance(self.imgsz, list), type(self.imgsz)
            self.model.warmup(imgsz=(1, 3, *self.imgsz))  # warmup
            metadata: "list[Metadatum]" = []
            for frame_idx, im, im0s in YoloDetection.tqdm(dataset):
                if not payload.keep[frame_idx]:
                    metadata.append(Metadatum(torch.Tensor([]), None, []))
                    continue
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
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0s.shape).round()
                metadata.append(
                    Metadatum(
                        det, None, [DetectionId(frame_idx, order) for order in range(len(det))]
                    )
                )
        m0 = metadata[0]
        metadata[0] = Metadatum(m0.detections, names, m0.detection_ids)
        return None, {self.classname(): metadata}


def class_mapping_to_list(names: "dict[int, str]") -> "list[str]":
    out: "list[str]" = []
    for i, (idx, name) in enumerate(sorted(names.items())):
        assert i == idx, (i, idx)
        out.append(name)

    return out


class ImageOutput(NamedTuple):
    frame_idx: int
    image: "npt.NDArray"
    original_image: "npt.NDArray"
    # path: str


class LoadImages(Iterator[ImageOutput], Iterable[ImageOutput]):
    # YOLOv5 image/video dataloader, i.e. `python detect.py --source image.jpg/vid.mp4`
    def __init__(
        self,
        payload: "Payload",
        img_size: "int | list[int]" = 640,
        stride=32,
        auto=True,
        transforms=None,
        vid_stride=1,
    ):
        self.img_size = img_size
        self.stride = stride
        self.mode = "image"
        self.auto = auto
        self.transforms = transforms  # optional
        self.vid_stride = vid_stride  # video frame-rate stride
        self._new_video(payload.video.videofile)  # new video
        self.keep = payload.keep

        images = DecodeFrame.get(payload)
        assert images is not None
        self.images = images

    def __iter__(self):
        self.count = 0
        return self

    def __next__(self) -> "ImageOutput":
        if self.frame >= self.frames:
            raise StopIteration

        # Read video
        self.mode = "video"
        im0 = self.images[self.frame]
        assert isinstance(im0, np.ndarray)

        frame_idx = self.frame
        self.frame += self.vid_stride
        # im0 = self._cv2_rotate(im0)  # for use if cv2 autorotation is False
        # s = f'video {self.count + 1}/{self.len} ({self.frame}/{self.frames}): '

        if self.transforms:
            im = self.transforms(im0)  # transforms
        else:
            im = letterbox(im0, self.img_size, stride=self.stride, auto=self.auto)[
                0
            ]  # padded resize
            im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
            im = np.ascontiguousarray(im)  # contiguous

        # return frame_idx, im, im0, s
        return ImageOutput(frame_idx, im, im0)

    def _new_video(self, path):
        # Create a new video capture object
        self.frame = 0
        self.cap = cv2.VideoCapture(path)
        self.frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.len = int(self.frames / self.vid_stride)
        self.orientation = int(self.cap.get(cv2.CAP_PROP_ORIENTATION_META))  # rotation degrees
        # self.cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 0)  # disable https://github.com/ultralytics/yolov5/issues/8493

    def __len__(self):
        return self.len
