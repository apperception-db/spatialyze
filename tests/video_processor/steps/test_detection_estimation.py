import os
import pickle
from bitarray import bitarray
import json
import pickle

from spatialyze.video_processor.pipeline import Pipeline
from spatialyze.video_processor.payload import Payload
from spatialyze.video_processor.stages.detection_3d.from_detection_2d_and_road import FromDetection2DAndRoad
from spatialyze.video_processor.video import Video
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.video_processor.stages.detection_estimation import DetectionEstimation

from common import yolo_output

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'


def test_detection_estimation():
    files = os.listdir(VIDEO_DIR)

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    pipeline = Pipeline([
        # Manually ingest processed detections from YoloDetection
        # DecodeFrame(),
        # YoloDetection(),
        FromDetection2DAndRoad(),
        DetectionEstimation(),
    ])

    for name, video in videos.items():
        if video['filename'] not in files:
            continue
        
        frames = Video(
            os.path.join(VIDEO_DIR, video["filename"]),
            [camera_config(*f) for f in video["frames"]],
        )
        keep = bitarray(len(frames))
        keep.setall(0)
        keep[(len(frames) * 7) // 8:] = 1

        output = pipeline.run(Payload(frames, keep, metadata=yolo_output(name)))
        keep_result = [*output.keep]
        if os.environ.get('GENERATE_PROCESSOR_TEST_RESULTS', 'false') == 'true':
            with open(os.path.join(OUTPUT_DIR, f'DetectionEstimationKeep--{name}.json'), 'w') as f:
                json.dump(keep_result, f, indent=1)

        with open(os.path.join(OUTPUT_DIR, f'DetectionEstimationKeep--{name}.json'), 'r') as f:
            keep_groundtruth = json.load(f)
        
        assert keep_result == keep_groundtruth
