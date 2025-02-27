import pickle
import os
from os import environ
import json
import datetime
import torch

from bitarray import bitarray
import duckdb
import numpy as np

from spatialyze.video_processor.stream.strongsort import TrackingResult
from spatialyze.world import TrackingResults, QueryResult

from spatialyze.database import Database
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.road_network import RoadNetwork
from spatialyze.utils.get_object_list import MovableObject
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.video_processor.stream.deepsort import DeepSORT
from spatialyze.world import TrackingResults, World
from spatialyze.utils.F import heading_diff

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'
ROAD_DIR = './data/scenic/road-network/boston-seaport'

def build_filter_world(pkl: bool = False, alt_tracker: bool = False, track: bool = True):
    database = Database(duckdb.connect(':memory:'))
    files = os.listdir(VIDEO_DIR)
    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    world = World(database, tracker=DeepSORT if alt_tracker else None)
    world.addGeogConstructs(RoadNetwork('Boston-Seaport', ROAD_DIR))
    
    for video in videos.values():
        if video['filename'] not in files:
            continue
        
        videofile = os.path.join(VIDEO_DIR, video['filename'])
        camera = [camera_config(*c) for c in video['frames']]
        keep = bitarray(len(camera))
        keep.setall(0)
        keep[(len(camera) * 3 // 4):] = 1
        if pkl:
            camera = videofile[:-len("mp4")] + 'camera.pkl'

        world.addVideo(GeospatialVideo(videofile, camera, keep))
    
    o = world.object()
    c = world.camera()
    world.filter(o.type == 'car')
    if track:
        world.filter((heading_diff(o, c) != -390) | True)

    return world


def trackid(track: list[TrackingResult]):
    return track[0].object_id


def frameidx(track: TrackingResult):
    return track.detection_id.frame_idx


def compare_trackings(
    trackings_prediction: dict[str, list[TrackingResults]],
    trackings_groundtruth: dict[str, list[TrackingResults]],
):
    for filename, tgs in trackings_groundtruth.items():
        assert filename in trackings_prediction, (filename, trackings_prediction.keys())
        tps = trackings_prediction[filename]
        assert len(tps) == len(tgs), (len(tps), len(tgs))
        for idx, (tp, tg) in enumerate(zip(sorted(tps, key=trackid), sorted(tgs, key=trackid))):
            assert len(tp) == len(tg), (idx, len(tp), len(tg))
            for p, g in zip(sorted(tp, key=frameidx), sorted(tg, key=frameidx)):
                assert isinstance(p, TrackingResult), (p, type(p))
                assert isinstance(g, TrackingResult), (g, type(g))
                assert tuple(p.detection_id) == tuple(g.detection_id), (p.detection_id, g.detection_id)
                assert p.object_id == g.object_id, (p.object_id, g.object_id)
                assert p.object_type == g.object_type, (p.object_type, g.object_type)
                assert p.timestamp == g.timestamp, (p.timestamp, g.timestamp)
                assert np.allclose(np.array([p.confidence]), np.array([g.confidence]), atol=0.001, rtol=0), (p.confidence, g.confidence)
                for pbbox, gbbox in zip(p.bbox.detach().cpu().numpy(), g.bbox.detach().cpu().numpy()):
                    assert np.allclose(pbbox, gbbox, atol=0.001, rtol=0), (pbbox, gbbox)


def compare_objects(
    objects_prediction: dict[str, list[QueryResult]],
    objects_groundtruth: dict[str, list[QueryResult]],
):
    assert len(objects_prediction) == len(objects_groundtruth), (len(objects_prediction), len(objects_groundtruth))
    for filename, ogs in objects_groundtruth.items():
        assert filename in objects_prediction, (filename, objects_prediction.keys())
        ops = objects_prediction[filename]
        assert len(ops) == len(ogs), (len(ops), len(ogs))
        for p, og in zip(sorted(ops), sorted(ogs)):
            assert tuple(p) == tuple(og), (p, og)


def compare_objects2(
    objects2_prediction: list[MovableObject],
    objects2_groundtruth: list[MovableObject],
):
    for o2, og in zip(sorted(objects2_prediction), sorted(objects2_groundtruth)):
        assert o2.id == og.id, (o2.id, og.id)
        assert o2.type == og.type, (o2.type, og.type)
        assert np.allclose(np.array(o2.track), np.array(og.track), atol=0.001, rtol=0), (o2.track, og.track)
        assert np.allclose(np.array(o2.bboxes), np.array(og.bboxes), atol=2, rtol=0), (o2.bboxes, og.bboxes)
        assert np.allclose(np.array(o2.frame_ids), np.array(og.frame_ids)), (o2.frame_ids, og.frame_ids)
        assert o2.camera_id == og.camera_id, (o2.camera_id, og.camera_id)


class ResultsEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return str(o)
        if isinstance(o, torch.Tensor):
            return o.detach().tolist()
        return json.JSONEncoder.default(self, o)
