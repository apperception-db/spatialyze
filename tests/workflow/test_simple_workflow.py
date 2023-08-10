import pickle
import json
import os
from os import environ
import psycopg2

from spatialyze.database import Database
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.road_network import RoadNetwork
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.world import World, _execute
from spatialyze.video_processor.cache import disable_cache


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
    
    o = world.object()
    world.filter(o.type == 'car')
    
    objects = _execute(world)
    
    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow.json'), 'w') as f:
    #     json.dump(objects, f, indent=1)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow.json'), 'r') as f:
        objects_groundtruth = json.load(f)
    
    for filename, ogs in objects_groundtruth.items():
        assert filename in objects, (filename, objects.keys())
        for op, og in zip(sorted(objects[filename]), sorted(ogs)):
            assert tuple(op) == tuple(og), (op, og)
