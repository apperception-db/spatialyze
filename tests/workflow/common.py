import pickle
import os
from os import environ
from bitarray import bitarray
import psycopg2

from spatialyze.database import Database
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.road_network import RoadNetwork
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.video_processor.stream.deepsort import DeepSORT
from spatialyze.world import World
from spatialyze.utils.F import heading_diff

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'
ROAD_DIR = './data/scenic/road-network/boston-seaport'

def build_filter_world(pkl: bool = False, alt_tracker: bool = False, track: bool = True):
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
        world.filter(heading_diff(o, c) != -1)

    return world
