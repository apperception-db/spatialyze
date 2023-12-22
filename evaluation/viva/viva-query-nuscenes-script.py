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
import time

def savenrow(nrow: int):
    print(f'   ----------------------- nrow --------------', nrow)
    with open('nrow.txt', 'w') as f:
        f.write(str(nrow))

def savert(t: float, text: str):
    e = time.time() - t
    print(f'   ----------------------- {text} --------------', e)
    with open('benchmark.txt', 'r') as f:
        bm = f.read()
    with open('benchmark.txt', 'w') as f:
        f.write(bm)
        f.write('\n')
        f.write(text + ': ' + str(e))


with open('benchmark.txt', 'w') as f:
    f.write('')



starttime = time.time()
from spatialyze.database import database
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.road_network import RoadNetwork
from spatialyze.data_types.camera_config import camera_config
from spatialyze.video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult
from spatialyze.world import World, _execute
from spatialyze.video_processor.cache import disable_cache
from spatialyze.video_processor.metadata_json_encoder import MetadataJSONEncoder



# %%
OUTPUT_DIR = '../../data/pipeline/test-results'
VIDEO_DIR =  '/home/youse/videos-resized' # '../../data/pipeline/videos'
ROAD_DIR = '../../data/scenic/road-network/boston-seaport'

files = os.listdir(VIDEO_DIR)
with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
    videos = pickle.load(f)

disable_cache()

disable_cache()
savert(starttime, 'setup')


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
starttime = time.time()

world = World(database)
world.addGeogConstructs(RoadNetwork('Boston-Seaport', ROAD_DIR))

# %%
for video in videos.values():
    if video['filename'] not in files:
        continue

    videofile = os.path.join(VIDEO_DIR, video['filename'])
    camera = [] # [camera_config(*c) for c in video['frames']]
    for c in video['frames']:
        c = list(c)
        c[6] = c[6] * np.array([
            360 / 1600,
            240 / 900,
            1
        ]).reshape((3, 1))
        c = tuple(c)
        cam_config = camera_config(*c)
        camera.append(cam_config)



    world.addVideo(GeospatialVideo(videofile, camera))

savert(starttime, 'load-videos')


# %%
from spatialyze.utils import F

starttime = time.time()
o = world.object(0)
p = world.object(1)
c = world.camera()
world.filter(
    (o.type == 'car')  &  (p.type == 'person') &
    F.contains_all('intersection', [o.trans, p.trans]@c.time) &
    F.left_turn(o)
)
savert(starttime, 'define-query')

# %%

print("running savevideos")
starttime = time.time()
# result = world.getObjects()
world.saveVideos(outputDir=OUTPUT_DIR, addBoundingBoxes=True)
savert(starttime, 'process-and-annotate')

import os
from typing import NamedTuple

import cv2

from spatialyze.data_types.query_result import QueryResult
from spatialyze.video_processor.stages.tracking_3d.tracking_3d import Metadatum as T3DMetadatum
from spatialyze.utils.get_object_list import MovableObject, get_object_list

TEXT_PADDING = 5

def save_video_util(
    objects: "dict[str, list[QueryResult]]",
    trackings: "dict[str, list[T3DMetadatum]]",
    outputDir: "str",
    addBoundingBoxes: "bool" = False,
) -> "list[tuple[str, int]]":
    objList = get_object_list(objects=objects, trackings=trackings)
    camera_to_video, video_to_camera = _get_video_names(objects=objects)
    bboxes = _get_bboxes(objList=objList, cameraVideoNames=camera_to_video)

    result: "list[tuple[str, int]]" = []

    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    for videoname, frame_tracking in bboxes.items():
        cameraId = video_to_camera[videoname]
        output_file = os.path.join(outputDir, cameraId + "-result-good.mp4")

        cap = cv2.VideoCapture(videoname)
        assert cap.isOpened(), f"Cannot read video file: {videoname}"

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        vid_writer = cv2.VideoWriter(
            output_file, cv2.VideoWriter_fourcc(*"mp4v"), 1, (width, height)
        )

        frame_cnt = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_cnt in frame_tracking:
                if addBoundingBoxes:
                    for bbox in frame_tracking.get(frame_cnt, []):
                        object_id, object_type, bbox_left, bbox_top, bbox_w, bbox_h = bbox
                        x1, y1 = bbox_left, bbox_top
                        x2, y2 = bbox_left + bbox_w, bbox_top + bbox_h
                        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))

                        bboxColor = 255, 255, 0

                        # Place Bounding Box
                        frame = cv2.rectangle(frame, (x1, y1), (x2, y2), bboxColor, 2)

                        # Place Label Background
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        fontScale = 0.5
                        fontThickness = 1
                        label = f"{object_type}:{object_id}"
                        labelSize, _ = cv2.getTextSize(label, font, fontScale, fontThickness)
                        labelW, labelH = labelSize

                        if object_type == "car":

                            frame = cv2.rectangle(
                                frame,
                                (x1, y1 - labelH - 2 * TEXT_PADDING),
                                (x1 + labelW + 2 * TEXT_PADDING, y1),
                                bboxColor,
                                cv2.FILLED,
                            )

                            # Place Label
                            frame = cv2.putText(
                                frame,
                                label,
                                (x1 + TEXT_PADDING, y1 - TEXT_PADDING),
                                font,
                                fontScale,
                                (255, 255, 255),
                                fontThickness,
                                cv2.LINE_AA,
                            )
                vid_writer.write(frame)
                result.append((videoname, frame_cnt))

            frame_cnt += 1

        vid_writer.release()

    return result


class BboxWithIdAndType(NamedTuple):
    id: "int"
    type: "str"
    left: "float"
    top: "float"
    width: "float"
    height: "float"


def _get_bboxes(objList: "list[MovableObject]", cameraVideoNames: "dict[str, str]"):
    """
    Indexes objects based on frame ID
    """
    result: "dict[str, dict[int, list[BboxWithIdAndType]]]" = {}
    for obj in objList:
        videoName = cameraVideoNames[obj.camera_id]
        for frameId, bbox in zip(obj.frame_ids, obj.bboxes):
            if videoName not in result:
                result[videoName] = {}
            if frameId not in result[videoName]:
                result[videoName][frameId] = []
            result[videoName][frameId].append(BboxWithIdAndType(obj.id, obj.type, *bbox))

    return result


def _get_video_names(objects: "dict[str, list[QueryResult]]"):
    """
    Returns mappings from videoName to cameraId and vice versa
    """
    camera_to_video: "dict[str, str]" = {}
    video_to_camera: "dict[str, str]" = {}
    for video, obj in filter(lambda x: len(x[1]) > 0, objects.items()):
        _, cameraId, _, _ = obj[0]
        camera_to_video[cameraId] = video
        video_to_camera[video] = cameraId
    return camera_to_video, video_to_camera


save_video_util(world._objects, world._trackings, OUTPUT_DIR, addBoundingBoxes=True)

# %%
# print("result", format(end-start))


# %%
starttime = time.time()
result = world.getObjects()
print(len(result))
savert(starttime, 'process-and-objects')
with open ('viva-nuscenes-tracks.txt', 'w') as out_file:
    for track in result:
        print(track, file=out_file) 


