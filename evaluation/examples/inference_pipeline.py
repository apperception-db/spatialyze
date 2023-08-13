import os
import pickle
from spatialyze.video_processor.actions.tracking2d_overlay import tracking2d_overlay

from spatialyze.video_processor.pipeline import Pipeline
from spatialyze.video_processor.payload import Payload
from spatialyze.video_processor.video import Video
from spatialyze.video_processor.camera_config import camera_config

from spatialyze.video_processor.stages.in_view.in_view import InView
from spatialyze.video_processor.stages.decode_frame.decode_frame import DecodeFrame
from spatialyze.video_processor.stages.detection_2d.yolo_detection import YoloDetection
from spatialyze.video_processor.stages.tracking_2d.strongsort import StrongSORT
from spatialyze.video_processor.stages.detection_2d.object_type_filter import ObjectTypeFilter
from spatialyze.video_processor.stages.detection_3d.from_detection_2d_and_road import FromDetection2DAndRoad

from spatialyze.video_processor.cache import disable_cache

disable_cache()

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'

files = os.listdir(VIDEO_DIR)

with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
    videos = pickle.load(f)

pipeline = Pipeline([
    InView(50, 'intersection'),
    DecodeFrame(),
    YoloDetection(),
    ObjectTypeFilter(['car']),
    FromDetection2DAndRoad(),
    StrongSORT(),
])

for name, video in videos.items():
    if video['filename'] not in files:
        continue
    
    frames = Video(
        os.path.join(VIDEO_DIR, video["filename"]),
        [camera_config(*f, 0) for f in video["frames"]],
    )

    payload = Payload(frames)
    payload.keep.setall(0)
    payload.keep[(len(payload.video) * 3) // 4:] = 1
    output = pipeline.run(payload)
    tracking2d_overlay(output, './examples/videos')
