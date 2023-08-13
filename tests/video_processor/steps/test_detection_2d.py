import os
import pickle
from bitarray import bitarray
import numpy as np
import json

from spatialyze.video_processor.pipeline import Pipeline
from spatialyze.video_processor.payload import Payload
from spatialyze.video_processor.video import Video
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.video_processor.cache import disable_cache

from spatialyze.video_processor.stages.decode_frame.decode_frame import DecodeFrame
from spatialyze.video_processor.stages.detection_2d.yolo_detection import YoloDetection

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'
disable_cache()

def test_detection_2d():
    files = os.listdir(VIDEO_DIR)

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    pipeline = Pipeline([DecodeFrame(), YoloDetection()])

    for name, video in videos.items():
        if video['filename'] not in files:
            continue
        
        frames = Video(
            os.path.join(VIDEO_DIR, video["filename"]),
            [camera_config(*f, 0) for f in video["frames"]],
        )
        keep = bitarray(len(frames))
        keep.setall(0)
        keep[(len(frames) * 3) // 4:] = 1

        output = pipeline.run(Payload(frames, keep))
        det_result = YoloDetection.get(output)
        assert det_result is not None

        with open(os.path.join(OUTPUT_DIR, f'YoloDetection--{name}.json'), 'w') as f:
            json.dump([(d[0].cpu().numpy().tolist(), d[1], d[2]) for d in det_result], f, indent=1)

        with open(os.path.join(OUTPUT_DIR, f'YoloDetection--{name}.json'), 'r') as f:
            det_groundtruth = json.load(f)
        
        for (det0, _, did0), (det1, _, did1) in zip(det_result, det_groundtruth):
            assert len(det0) == len(det1)
            if len(det1) == 0:
                continue
            det0 = det0.cpu().numpy()
            det1 = np.array(det1)
            assert np.allclose(det0[:,:4], det1[:,:4], atol=2)
            assert np.allclose(det0[:,4], det1[:,4], atol=0.05)
            assert np.allclose(det0[:,5], det1[:,5])

            assert all(tuple(d0) == tuple(d1) for d0, d1 in zip(did0, did1))
