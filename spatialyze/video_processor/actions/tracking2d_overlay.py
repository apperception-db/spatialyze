import os

import cv2
import numpy as np

from ...utils.tqdm import tqdm
from ..stream.list_images import ListImages
from ..stream.load_images import LoadImages
from ..stream.sort import TrackingResult
from ..types import DetectionId
from ..video.video import Video

# from ..payload import Payload
# from ..stages.decode_frame.decode_frame import DecodeFrame
# from ..stages.tracking_2d.tracking_2d import Tracking2D


def interpolate(prev: TrackingResult, next: TrackingResult, i: int):
    return (
        (next.bbox * (next.detection_id.frame_idx - i))
        + (prev.bbox * (i - prev.detection_id.frame_idx))
    ) / (next.detection_id.frame_idx - prev.detection_id.frame_idx)


def tracking2d_overlay(t2ds: list[list[TrackingResult]], video: Video, base_dir: str):
    images = LoadImages(ListImages()).iterate(video)

    dets: list[list[TrackingResult]] = [list() for _ in range(len(video.camera_configs))]

    for tr in t2ds:
        prev: None | TrackingResult = None
        for det in tr:
            fid = det.detection_id.frame_idx
            if prev is not None:
                for i in range(prev.detection_id.frame_idx + 1, fid):
                    dets[i].append(
                        TrackingResult(
                            detection_id=DetectionId(frame_idx=i, obj_order=DetectionId.unique(i)),
                            object_id=det.object_id,
                            confidence=det.confidence,
                            bbox=interpolate(prev, det, i),
                            object_type=det.object_type,
                        )
                    )
            prev = det
            dets[fid].append(det)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    # print('dir', videofile)
    videofile = os.path.join(base_dir, video.videofile.split("/")[-1] + ".mp4")
    out = cv2.VideoWriter(videofile, fourcc, int(15), (1920, 1080))

    for t2d, image in tqdm(zip(dets, images), total=len(dets)):
        # assert isinstance(t2d, dict)
        assert isinstance(image, np.ndarray)

        for det in t2d:
            oid = det.object_id
            oid = int(oid)
            left, top, width, height = det.bbox[:4]
            left -= width / 2
            top -= height / 2
            start = (int(left), int(top))
            end = (int(left + width), int(top + height))

            ccode = [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
                "#bcbd22",
                "#17becf",
            ][oid % 10]
            ccode = ccode[1:]
            color = (int(ccode[4:], 16), int(ccode[2:4], 16), int(ccode[:2], 16))

            thickness = 2
            image = cv2.rectangle(image, start, end, color, thickness)

            image = cv2.putText(
                image,
                f"{det.object_type} {oid}",
                start,
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                thickness,
                cv2.LINE_AA,
            )
        out.write(image)

    out.release()
    cv2.destroyAllWindows()


# def tracking2d_overlay(payload: "Payload", base_dir: "str"):
#     t2ds = payload[Tracking2D]
#     assert t2ds is not None

#     images = payload[DecodeFrame]
#     assert images is not None

#     fourcc = cv2.VideoWriter_fourcc(*"mp4v")
#     videofile = os.path.join(base_dir, payload.video.videofile.split("/")[-1])
#     # print('dir', videofile)
#     out = cv2.VideoWriter(videofile, fourcc, int(payload.video.fps), payload.video.dimension)

#     for t2d, image in zip(t2ds, images):
#         assert isinstance(t2d, dict)
#         assert isinstance(image, np.ndarray)

#         for oid, det in t2d.items():
#             oid = int(oid)
#             l, t, w, h = det.bbox_left, det.bbox_top, det.bbox_w, det.bbox_h
#             start = (int(l), int(t))
#             end = (int(l + w), int(t + h))

#             ccode = [
#                 "#1f77b4",
#                 "#ff7f0e",
#                 "#2ca02c",
#                 "#d62728",
#                 "#9467bd",
#                 "#8c564b",
#                 "#e377c2",
#                 "#7f7f7f",
#                 "#bcbd22",
#                 "#17becf",
#             ][oid % 10]
#             ccode = ccode[1:]
#             color = (int(ccode[4:], 16), int(ccode[2:4], 16), int(ccode[:2], 16))

#             thickness = 2
#             image = cv2.rectangle(image, start, end, color, thickness)

#             image = cv2.putText(
#                 image,
#                 f"{det.object_type} {oid}",
#                 start,
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 1,
#                 color,
#                 thickness,
#                 cv2.LINE_AA,
#             )
#         out.write(image)

#     out.release()
#     cv2.destroyAllWindows()
