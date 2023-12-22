import os
import pickle
from bitarray import bitarray
import numpy as np
import json

from spatialyze.video_processor.pipeline import Pipeline
from spatialyze.video_processor.payload import Payload
from spatialyze.video_processor.video import Video
from spatialyze.data_types.camera_config import camera_config
from spatialyze.video_processor.cache import disable_cache
from spatialyze.video_processor.metadata_json_encoder import MetadataJSONEncoder

from spatialyze.video_processor.stages.decode_frame.decode_frame import DecodeFrame
from spatialyze.video_processor.stages.detection_2d.yolo_detection import YoloDetection
from spatialyze.video_processor.stages.tracking_2d.deepsort import DeepSORT
from spatialyze.video_processor.stages.tracking_2d.strongsort import StrongSORT
from spatialyze.video_processor.stages.stage import Stage

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'
disable_cache()
Stage.enable_progress()

def test_strongsort():
    files = os.listdir(VIDEO_DIR)

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    pipeline = Pipeline([
        DecodeFrame(),
        YoloDetection(),
        StrongSORT(),
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

        output = pipeline.run(Payload(frames, keep))
        # track_result = StrongSORT.get(output)
        track_result = output['Tracking2D.StrongSORT']
        assert track_result is not None

        # with open(os.path.join(OUTPUT_DIR, f'StrongSORT--{name}.json'), 'w') as f:
        #     json.dump(track_result, f, indent=1, cls=MetadataJSONEncoder)

        with open(os.path.join(OUTPUT_DIR, f'StrongSORT--{name}.json'), 'r') as f:
            track_groundtruth = json.load(f)
        
        for tr, tg in zip(track_result, track_groundtruth):
            for oid, detr in tr.items():
                detg = tg[str(oid)]

                assert detr.frame_idx == detg['frame_idx']
                assert detr.object_id == detg['object_id']
                assert tuple(detr.detection_id) == tuple(detg['detection_id'])
                assert abs(detr.bbox_left - detg['bbox_left']) <= 1
                assert abs(detr.bbox_top - detg['bbox_top']) <= 1
                assert abs(detr.bbox_w - detg['bbox_w']) <= 1
                assert abs(detr.bbox_h - detg['bbox_h']) <= 1
                assert detr.object_type == detg['object_type']
                assert abs(float(detr.confidence) - detg['confidence']) <= 0.05


def test_deepsort():
    files = os.listdir(VIDEO_DIR)

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    pipeline = Pipeline([
        DecodeFrame(),
        YoloDetection(),
        DeepSORT(),
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

        output = pipeline.run(Payload(frames, keep))
        # track_result = DeepSORT.get(output)
        track_result = output['Tracking2D.DeepSORT']
        assert track_result is not None

        # with open(os.path.join(OUTPUT_DIR, f'DeepSORT--{name}.json'), 'w') as f:
        #     json.dump(track_result, f, indent=1, cls=MetadataJSONEncoder)

        with open(os.path.join(OUTPUT_DIR, f'DeepSORT--{name}.json'), 'r') as f:
            track_groundtruth = json.load(f)
        
        for tr, tg in zip(track_result, track_groundtruth):
            for oid, detr in tr.items():
                detg = tg[str(oid)]

                assert detr.frame_idx == detg['frame_idx']
                assert detr.object_id == detg['object_id']
                assert tuple(detr.detection_id) == tuple(detg['detection_id'])
                assert abs(detr.bbox_left - detg['bbox_left']) <= 1
                assert abs(detr.bbox_top - detg['bbox_top']) <= 1
                assert abs(detr.bbox_w - detg['bbox_w']) <= 1
                assert abs(detr.bbox_h - detg['bbox_h']) <= 1
                assert detr.object_type == detg['object_type']
                assert abs(float(detr.confidence) - detg['confidence']) <= 0.05
