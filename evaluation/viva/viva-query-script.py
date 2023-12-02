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
OUTPUT_DIR = '/home/youse/viva-results'
VIDEO_DIR =  '/home/youse/viva-data' # '../../data/pipeline/videos'
# ROAD_DIR = '../../data/scenic/road-network/boston-seaport'

files = os.listdir(VIDEO_DIR)



disable_cache()

# %%
# First run = 8015.9125235sec
# We want 240 * 20sec =  4800sec worth of video. So we will use 4800s/5s = 960 videos
files = [x for x in files if int(x.split(".")[0]) <= 960]

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
# world.addGeogConstructs(RoadNetwork('Boston-Seaport', ROAD_DIR))

# %%
from pyquaternion import Quaternion

CAMERA_INTRINSIC = np.array([
    [1272,    0, 960],
    [   0, 1272, 540],
    [   0,    0,   1]
])

CAMERA_TRANSLATION = np.array([0, 0, 5])

CAMERA_ROTATION = Quaternion((0.430, -0.561, 0.561, -0.430))

# %%
import cv2
import datetime

for video in files:
    videofile = os.path.join(VIDEO_DIR, video)
    
    cap = cv2.VideoCapture(videofile)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    camera = []
    for frame in range(frame_count):
        camera.append(camera_config(
            camera_id=video,
            camera_heading=90,
            camera_intrinsic=CAMERA_INTRINSIC,
            camera_translation=CAMERA_TRANSLATION,
            ego_heading=0,
            ego_rotation=Quaternion((1, 0, 0, 0)),
            camera_rotation=CAMERA_ROTATION,
            filename=videofile,
            ego_translation=np.array([0, 0, 0]),
            frame_id=frame,
            frame_num=frame,
            location="viva-data",
            timestamp=datetime.datetime.fromtimestamp(frame + 10),
            road_direction=0,
        ))

    world.addVideo(GeospatialVideo(videofile, camera))

# %%
from spatialyze.utils import F

o = world.object()
# p = world.object()
c = world.camera()
world.filter(
    (o.type == 'car') &
    # F.contained(o.trans@c.time, 'intersection') &
    F.left_turn(o)
)

# %%
import time

print("running query")
start = time.time()
result = world.getObjects()
end = time.time()


# %%
print("result", format(end-start))


# %%
# result = world.getObjects()
# result

# # %%
# world.saveVideos(outputDir=OUTPUT_DIR, addBoundingBoxes=True)


