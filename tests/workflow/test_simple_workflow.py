import pickle
import json
import os
from os import environ
import psycopg2
import numpy as np

from spatialyze.database import Database
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.road_network import RoadNetwork
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult
from spatialyze.world import World, _execute
from spatialyze.video_processor.cache import disable_cache
from spatialyze.video_processor.metadata_json_encoder import MetadataJSONEncoder


OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'
ROAD_DIR = './data/scenic/road-network/boston-seaport'
disable_cache()


def test_simple_workflow():
    database = Database(
    psycopg2.connect(
        dbname=environ.get("AP_DB", "mobilitydb"),
        user=environ.get("AP_USER", "docker"),
        host=environ.get("AP_HOST", "localhost"),
        port=environ.get("AP_PORT", "25432"),
        password=environ.get("AP_PASSWORD", "docker"),
    )
)
    files = os.listdir(VIDEO_DIR)
    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    world = World(database)
    world.addGeogConstructs(RoadNetwork('Boston-Seaport', ROAD_DIR))
    
    for video in videos.values():
        if video['filename'] not in files:
            continue
        
        videofile = os.path.join(VIDEO_DIR, video['filename'])
        camera = [camera_config(*c) for c in video['frames']]

        world.addVideo(GeospatialVideo(videofile, camera))
        # break
    
    o = world.object()
    world.filter(o.type == 'car')
    
    objects, trackings = _execute(world, optimization=False)

    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.json'), 'w') as f:
    #     json.dump(trackings, f, indent=1, cls=MetadataJSONEncoder)
    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.pkl'), 'wb') as f:
    #     pickle.dump(trackings, f)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.pkl'), 'rb') as f:
        trackings_groundtruth = pickle.load(f)
    
    for filename, tgs in trackings_groundtruth.items():
        assert filename in trackings, (filename, trackings.keys())
        tps = trackings[filename]
        assert len(tps) == len(tgs), (len(tps), len(tgs))
        for idx, (tp, tg) in enumerate(zip(tps, tgs)):
            assert len(tp) == len(tg), (idx, len(tp), len(tg))
            for oid, g in tg.items():
                assert oid in tp, (oid, tp.keys())
                p = tp[oid]
                assert isinstance(g, Tracking3DResult), (g, type(g))
                assert p.frame_idx == g.frame_idx, (p.frame_idx, g.frame_idx)
                assert tuple(p.detection_id) == tuple(g.detection_id), (p.detection_id, g.detection_id)
                assert p.object_id == g.object_id, (p.object_id, g.object_id)
                assert np.allclose(np.array(p.point_from_camera), np.array(g.point_from_camera)), (p.point_from_camera, g.point_from_camera)
                assert np.allclose(np.array(p.point.tolist()), np.array(g.point)), (p.point, g.point)
                assert p.bbox_left == g.bbox_left, (p.bbox_left, g.bbox_left)
                assert p.bbox_top == g.bbox_top, (p.bbox_top, g.bbox_top)
                assert p.bbox_w == g.bbox_w, (p.bbox_width, g.bbox_w)
                assert p.bbox_h == g.bbox_h, (p.bbox_height, g.bbox_h)
                assert p.object_type == g.object_type, (p.object_type, g.object_type)
                assert p.timestamp == g.timestamp, (p.timestamp, g.timestamp)
    
    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.json'), 'w') as f:
    #     json.dump(objects, f, indent=1)
    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.pkl'), 'wb') as f:
    #     pickle.dump(objects, f)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.pkl'), 'rb') as f:
        objects_groundtruth = pickle.load(f)
    
    assert len(objects) == len(objects_groundtruth), (len(objects), len(objects_groundtruth))
    for filename, ogs in objects_groundtruth.items():
        assert filename in objects, (filename, objects.keys())
        ops = objects[filename]
        assert len(ops) == len(ogs), (len(ops), len(ogs))
        for p, og in zip(sorted(ops), sorted(ogs)):
            assert tuple(p) == tuple(og), (p, og)
