import os
import pickle
from bitarray import bitarray
import numpy as np
import json
import pickle
import pandas as pd

from spatialyze.video_processor.pipeline import Pipeline
from spatialyze.video_processor.payload import Payload
from spatialyze.video_processor.stages.detection_3d.ground_truth import GroundTruthDetection3D
from spatialyze.video_processor.video import Video
from spatialyze.video_processor.camera_config import camera_config

from spatialyze.video_processor.stages.decode_frame.decode_frame import DecodeFrame
from spatialyze.video_processor.stages.detection_2d.yolo_detection import YoloDetection, Metadatum as D2DMetadatum
from spatialyze.video_processor.stages.detection_3d.from_detection_2d_and_road import FromDetection2DAndRoad
from spatialyze.video_processor.stages.detection_3d.from_detection_2d_and_depth import FromDetection2DAndDepth
from spatialyze.video_processor.stages.depth_estimation import DepthEstimation

from common import yolo_output

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'


def compare_detections(det_result: list, det_groundtruth: list):
    for (det0, _, did0), (det1, _, did1) in zip(det_result, det_groundtruth):
        assert len(det0) == len(det1)
        if len(det1) == 0:
            continue
        det0 = det0.cpu()
        det1 = np.array(det1)
        for d0, d1 in zip(det0, det1):
            assert np.allclose(d0[:4], d1[:4], atol=2)
            assert np.allclose(d0[4], d1[4], atol=0.05)
            assert np.allclose(d0[5], d1[5])
            assert np.allclose(d0[6:12], d1[6:12], atol=0.2)
            assert np.allclose(d0[12:], d1[12:], rtol=0.01)

        assert all(tuple(d0) == tuple(d1) for d0, d1 in zip(did0, did1))


def test_detection_3d():
    files = os.listdir(VIDEO_DIR)

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    pipeline = Pipeline([
        # Manually ingest processed detections from YoloDetection
        DecodeFrame(),
        # YoloDetection(),
        FromDetection2DAndRoad(),
        DepthEstimation(),
        FromDetection2DAndDepth(),
    ])

    for name, video in videos.items():
        if video['filename'] not in files:
            continue
        
        frames = Video(
            os.path.join(VIDEO_DIR, video["filename"]),
            [camera_config(*f, 0) for f in video["frames"]],
        )
        keep = bitarray(len(frames))
        keep.setall(0)
        keep[(len(frames) * 7) // 8:] = 1

        output = pipeline.run(Payload(frames, keep, metadata=yolo_output(name)))
        det_result = output[FromDetection2DAndRoad]
        assert det_result is not None
        if os.environ.get('GENERATE_PROCESSOR_TEST_RESULTS', 'false') == 'true':
            with open(os.path.join(OUTPUT_DIR, f'FromDetection2DAndRoad--{name}.json'), 'w') as f:
                json.dump([(d[0].cpu().numpy().tolist(), d[1], d[2]) for d in det_result], f, indent=1)
            with open(os.path.join(OUTPUT_DIR, f'FromDetection2DAndRoad--{name}.pkl'), 'wb') as f:
                pickle.dump([(d[0].cpu(), d[1], d[2]) for d in det_result], f)

        with open(os.path.join(OUTPUT_DIR, f'FromDetection2DAndRoad--{name}.pkl'), 'rb') as f:
            det_groundtruth = pickle.load(f)
        compare_detections(det_result, det_groundtruth)


        det_result = FromDetection2DAndDepth.get(output)
        assert det_result is not None
        # if os.environ.get('GENERATE_PROCESSOR_TEST_RESULTS', 'false') == 'true':
        with open(os.path.join(OUTPUT_DIR, f'FromDetection2DAndDepth--{name}.json'), 'w') as f:
            json.dump([(d[0].cpu().numpy().tolist(), d[1], d[2]) for d in det_result], f, indent=1)
        with open(os.path.join(OUTPUT_DIR, f'FromDetection2DAndDepth--{name}.pkl'), 'wb') as f:
            pickle.dump([(d[0].cpu(), d[1], d[2]) for d in det_result], f)

        with open(os.path.join(OUTPUT_DIR, f'FromDetection2DAndDepth--{name}.pkl'), 'rb') as f:
            det_groundtruth = pickle.load(f)
        compare_detections(det_result, det_groundtruth)


def test_groundtruth():
    files = os.listdir(VIDEO_DIR)

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    with open('./data/nuscenes/processed/annotation-mini.pkl', 'rb') as f:
        annotations = pd.DataFrame.from_records(pickle.load(f))
    
    pipeline = Pipeline([GroundTruthDetection3D(annotations)])

    for name, video in videos.items():
        if video['filename'] not in files:
            continue
        
        frames = Video(
            os.path.join(VIDEO_DIR, video["filename"]),
            [camera_config(*f, 0) for f in video["frames"]],
        )
        keep = bitarray(len(frames))
        keep.setall(0)
        keep[(len(frames) * 7) // 8:] = 1

        output = pipeline.run(Payload(frames, keep))
        # det_result = GroundTruthDetection3D.get(output)
        det_result = output[GroundTruthDetection3D]
        assert det_result is not None

        if os.environ.get('GENERATE_PROCESSOR_TEST_RESULTS', 'false') == 'true':
            with open(os.path.join(OUTPUT_DIR, f'GroundTruthDetection3D--{name}.json'), 'w') as f:
                json.dump([(d[0].cpu().numpy().tolist(), d[1], d[2]) for d in det_result], f, indent=1)
            with open(os.path.join(OUTPUT_DIR, f'GroundTruthDetection3D--{name}.pkl'), 'wb') as f:
                pickle.dump([(d[0].cpu(), d[1], d[2]) for d in det_result], f)

        with open(os.path.join(OUTPUT_DIR, f'GroundTruthDetection3D--{name}.pkl'), 'rb') as f:
            det_groundtruth = pickle.load(f)
        compare_detections(det_result, det_groundtruth)
