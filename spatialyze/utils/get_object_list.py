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

    return Tracking3DResult(
        frame_idx=frameNum,
        point=tuple(newPoint.tolist()),
        point_from_camera=tuple(newPointFromCamera.tolist()),
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


def get_object_list(
    objects: "dict[str, list[QueryResult]]",
    trackings: "dict[str, list[T3DMetadatum]]",
) -> "list[MovableObject]":
    tracks: "dict[str, dict[int, list[Float3]]]" = {}
    bboxes: "dict[str, dict[int, list[Float4]]]" = {}
    frameIds: "dict[str, dict[int, list[int]]]" = {}
    objectTypes: "dict[str, dict[int, str]]" = {}

    for video in objects:
        videoObjects = objects[video]
        if len(videoObjects) == 0:
            continue

        cameraId = videoObjects[0][2]  # cameraId same for everything in a video
        assert isinstance(cameraId, str), type(cameraId)
        tracks[cameraId] = {}
        bboxes[cameraId] = {}
        frameIds[cameraId] = {}
        objectTypes[cameraId] = {}

        for obj in videoObjects:
            frameId, objectId, cameraId, _ = obj
            objectId = int(objectId)

            if objectId in trackings[video][frameId]:
                track = trackings[video][frameId][objectId]
            else:
                track = interpolate_track(trackings[video], objectId, frameId)

            if objectId not in tracks[cameraId]:
                tracks[cameraId][objectId] = []
            tracks[cameraId][objectId].append(track.point)

            if objectId not in bboxes[cameraId]:
                bboxes[cameraId][objectId] = []
            bboxes[cameraId][objectId].append(
                (track.bbox_left, track.bbox_top, track.bbox_w, track.bbox_h)
            )

            if objectId not in frameIds[cameraId]:
                frameIds[cameraId][objectId] = []
            frameIds[cameraId][objectId].append(track.frame_idx)

            objectTypes[cameraId][objectId] = track.object_type

    result: "list[MovableObject]" = []
    for cameraId in tracks:
        for objectId in tracks[cameraId]:
            result.append(
                MovableObject(
                    objectId,
                    objectTypes[cameraId][objectId],
                    tracks[cameraId][objectId],
                    bboxes[cameraId][objectId],
                    frameIds[cameraId][objectId],
                    cameraId,
                )
            )
    return result
