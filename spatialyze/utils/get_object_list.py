from typing import NamedTuple

import numpy as np

from ..data_types.camera_config import Float3, Float4
from ..data_types.query_result import QueryResult
from ..video_processor.stages.tracking_3d.tracking_3d import Metadatum as T3DMetadatum
from ..video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult
from ..video_processor.types import DetectionId


def interpolate_track(
    trackings: "list[T3DMetadatum]", objectId: "int", frameNum: "int"
) -> "Tracking3DResult":
    left, right = None, None
    leftNum, rightNum = frameNum, frameNum

    while left is None:
        leftNum -= 1
        if objectId in trackings[leftNum]:
            left = trackings[leftNum][objectId]

    while right is None:
        rightNum += 1
        if objectId in trackings[rightNum]:
            right = trackings[rightNum][objectId]

    leftWeight = 1 - (frameNum - leftNum) / (rightNum - leftNum)
    rightWeight = (frameNum - leftNum) / (rightNum - leftNum)
    newPoint = np.array(left.point) * leftWeight + np.array(right.point) * rightWeight
    newPointFromCamera = (
        np.array(left.point_from_camera) * leftWeight
        + np.array(right.point_from_camera) * rightWeight
    )
    newBboxCenterX = (left.bbox_left + left.bbox_w / 2.0) * leftWeight + (
        right.bbox_left + right.bbox_w / 2.0
    ) * rightWeight
    newBboxCenterY = (left.bbox_top + left.bbox_h / 2.0) * leftWeight + (
        right.bbox_top + right.bbox_h / 2.0
    ) * rightWeight
    newBboxHeight = left.bbox_h * leftWeight + right.bbox_h * rightWeight
    newBboxWidth = left.bbox_w * leftWeight + right.bbox_w * rightWeight
    newBboxLeft = newBboxCenterX - newBboxWidth / 2.0
    newBboxTop = newBboxCenterY - newBboxHeight / 2.0

    timedelta = right.timestamp - left.timestamp
    newTimestamp = left.timestamp + timedelta * rightWeight

    x, y, z = newPoint.tolist()
    _x, _y, _z = newPointFromCamera.tolist()
    return Tracking3DResult(
        frame_idx=frameNum,
        point=(x, y, z),
        point_from_camera=(_x, _y, _z),
        bbox_left=newBboxLeft,
        bbox_top=newBboxTop,
        bbox_h=newBboxHeight,
        bbox_w=newBboxWidth,
        detection_id=DetectionId(frameNum, -1),
        object_id=objectId,
        object_type=left.object_type,
        timestamp=newTimestamp,
    )


class MovableObject(NamedTuple):
    id: "int"
    type: "str"
    track: "list[Float3]"
    bboxes: "list[Float4]"
    frame_ids: "list[int]"
    camera_id: "str"


class ObjectListKey(NamedTuple):
    cameraId: "str"
    objectId: "int"


def get_object_list(
    objects: "dict[str, list[QueryResult]]",
    trackings: "dict[str, list[T3DMetadatum]]",
) -> "list[MovableObject]":
    tracks: "dict[ObjectListKey, list[Float3]]" = {}
    bboxes: "dict[ObjectListKey, list[Float4]]" = {}
    frameIds: "dict[ObjectListKey, list[int]]" = {}
    objectTypes: "dict[ObjectListKey, str]" = {}

    for video in objects:
        for obj in objects[video]:
            frameId, cameraId, _, objectIds = obj
            for objectId in map(int, objectIds):
                key = ObjectListKey(cameraId, objectId)

                if objectId in trackings[video][frameId]:
                    track = trackings[video][frameId][objectId]
                else:
                    track = interpolate_track(trackings[video], objectId, frameId)

                if key not in tracks:
                    tracks[key] = []
                tracks[key].append(track.point)

                if key not in bboxes:
                    bboxes[key] = []
                bbox = track.bbox_left, track.bbox_top, track.bbox_w, track.bbox_h
                bboxes[key].append(bbox)

                if key not in frameIds:
                    frameIds[key] = []
                frameIds[key].append(track.frame_idx)

                objectTypes[key] = track.object_type

    return [
        MovableObject(
            key.objectId,
            objectTypes[key],
            tracks[key],
            bboxes[key],
            frameIds[key],
            key.cameraId,
        )
        for key in tracks
    ]
