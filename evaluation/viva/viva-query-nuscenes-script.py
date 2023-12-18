# %%
from os import environ
# environ["AP_PORT"] = "25432" # str(input('port'))
# README command uses port=25432

# %%
import pickle
import json
import os
import psycopg2
import numpy as np

from spatialyze.database import database
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.road_network import RoadNetwork
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult
from spatialyze.world import World, _execute
from spatialyze.video_processor.cache import disable_cache
from spatialyze.video_processor.metadata_json_encoder import MetadataJSONEncoder

# %%
OUTPUT_DIR = '../../data/pipeline/test-results'
VIDEO_DIR =  '/home/youse/videos' # '../../data/pipeline/videos'
ROAD_DIR = '../../data/scenic/road-network/boston-seaport'

files = os.listdir(VIDEO_DIR)
with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
    videos = pickle.load(f)

disable_cache()

# %%
# database = Database(
#     psycopg2.connect(
#         dbname=environ.get("AP_DB", "mobilitydb"),
#         user=environ.get("AP_USER", "docker"),
#         host=environ.get("AP_HOST", "localhost"),
#         port=environ.get("AP_PORT", "25432"),
#         password=environ.get("AP_PASSWORD", "docker"),
#     )
# )

# %%
world = World(database)
world.addGeogConstructs(RoadNetwork('Boston-Seaport', ROAD_DIR))

# %%
for video in videos.values():
    if video['filename'] not in files:
        continue

    videofile = os.path.join(VIDEO_DIR, video['filename'])
    camera = [camera_config(*c) for c in video['frames']]

    world.addVideo(GeospatialVideo(videofile, camera))

# %%
from spatialyze.utils import F

o = world.object()
# p = world.object()
c = world.camera()
world.filter(
    (o.type == 'car') & # (p.type == 'person') &
    F.contained(o.trans@c.time, 'intersection') &
    F.left_turn(o) 
)

# %%
import time

print("running query")
start = time.time()
result = world.getObjects()
end = time.time()


# %%
print("result", format(end-start)) # Deepsort run = 2782.81840634346sec


# %%
with open ('viva-nuscenes-tracks.txt', 'w') as out_file:
    for track in result:
        print(track, file=out_file)    

# %%
world.saveVideos(outputDir=OUTPUT_DIR, addBoundingBoxes=True)


