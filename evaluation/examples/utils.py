import datetime
from typing import NamedTuple

import numpy as np

from spatialyze.video_processor.types import Float2, Float3, Float33
from spatialyze.video_processor.camera_config import camera_config
from pyquaternion import Quaternion
import cv2
import os
import tqdm


start_date = datetime.datetime(
    year=2018,
    month=8,
    day=27,
    hour=15,
    minute=51,
    second=32,
    microsecond=0
)


# SkyQuery ---


class TopDownCameraConfig(NamedTuple):
    tl: Float2
    tr: Float2
    br: Float2
    bl: Float2
    camera_id: str
    frame_id: int
    filename: str
    camera_translation: Float3
    camera_rotation: tuple[float, float, float, float]
    camera_intrinsic: Float33
    ego_translation: Float3
    ego_rotation: tuple[float, float, float, float]
    timestamp: datetime.datetime
    camera_heading: float
    ego_heading: float


def topdown_config(v: tuple[Float2, Float2, Float2, Float2], idx: int, file: str):
    timestamp = start_date + datetime.timedelta(milliseconds=40 * idx)
    t2 = np.array(v).mean(axis=0).tolist()
    assert isinstance(t2, list)
    x, y = t2
    assert isinstance(x, float)
    assert isinstance(y, float)
    translation: Float3 = x, y, 0
    return TopDownCameraConfig(
        *v,
        'camera1',
        idx,
        file,
        translation,
        (1, 0, 0, 0),
        ((190, 0, 800), (0, 190, 450), (0, 0, 1)),
        translation,
        (1, 0, 0, 0),
        timestamp,
        0,
        0,
    )


# VIVA ---


CAMERA_INTRINSIC_FULL = np.array([
    [1272,    0, 960],
    [   0, 1272, 540],
    [   0,    0,   1],
])
CAMERA_INTRINSIC = CAMERA_INTRINSIC_FULL * np.array([
    360 / 1920,
    240 / 1080,
    1
]).reshape((3, 1))
CAMERA_TRANSLATION = np.array([0, 0, 5])
CAMERA_ROTATION = Quaternion((0.430, -0.561, 0.561, -0.430))


def vv_config(idx: int, videofile: str):
    timestamp = start_date + datetime.timedelta(seconds=idx)
    return camera_config(
        camera_id='camera-1',
        camera_heading=-90,
        camera_intrinsic=CAMERA_INTRINSIC,
        camera_translation=CAMERA_TRANSLATION,
        ego_heading=0,
        ego_rotation=Quaternion((1, 0, 0, 0)),
        camera_rotation=CAMERA_ROTATION,
        filename=videofile,
        ego_translation=np.array([0, 0, 0]),
        frame_id=idx,
        frame_num=idx + 1,
        location="viva-location",
        timestamp=timestamp,
        road_direction=0,
    )


def resize(video_dir, video_name):
    writer = cv2.VideoWriter(
        os.path.join(video_dir, video_name),
        cv2.VideoWriter_fourcc(*'mp4v'),
        1,
        (360, 240),
    )
    # images = []
    idx = 0
    last = None
    frame_count = 0
    _size = 0
    N = 6490
    for i in tqdm(range(1, N + 1), total=N):
        # print('video', i)
        cap = cv2.VideoCapture(os.path.join(video_dir, str(i) + '.mp4'))
        # print(cap.get(cv2.CAP_PROP_FPS))
        count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                if idx % cap.get(cv2.CAP_PROP_FPS) == 0:
                    # images.append(cv2.resize(frame, (360, 240)))
                    img = cv2.resize(frame, (360, 240))
                    writer.write(img)
                    _size += img.size * img.itemsize
                    count += 1
                    # print('frame', frame_count)
                    frame_count += 1
                last = frame
            else:
                break
            idx += 1
        # print('c=', count)
        cap.release()
    # images.append(cv2.resize(last, (360, 240)))
    img = cv2.resize(last, (360, 240))
    _size += img.size * img.itemsize
    writer.write(img)
    writer.release()
    cv2.destroyAllWindows()