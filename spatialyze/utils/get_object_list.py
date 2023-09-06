from typing import NamedTuple

import numpy as np
import numpy.typing as npt

from ..data_types.camera_config import Float4
from ..data_types.query_result import QueryResult
from ..video_processor.stages.tracking_3d.tracking_3d import Metadatum as T3DMetadatum
from ..video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult


def interpolate_track(
    trackings: "dict[str, list[T3DMetadatum]]", video: "str", objectNum: "int", frameNum: "int"
) -> "Tracking3DResult":
    left, right = None, None
    leftNum, rightNum = frameNum, frameNum

    while left is None or right is None:
        if left is None:
            leftNum -= 1
            if objectNum in trackings[video][leftNum]:
                left = trackings[video][leftNum][objectNum]

        if right is None:
            rightNum += 1
            if objectNum in trackings[video][rightNum]:
                right = trackings[video][rightNum][objectNum]

    leftWeight = 1 - (frameNum - leftNum) / (rightNum - leftNum)
    rightWeight = (frameNum - leftNum) / (rightNum - leftNum)
    newPoint = np.array(left.point) * leftWeight + np.array(right.point) * rightWeight
    newBboxLeft = left.bbox_left * leftWeight + right.bbox_left * rightWeight
    newBboxTop = left.bbox_top * leftWeight + right.bbox_top * rightWeight
    newBboxHeight = left.bbox_h * leftWeight + right.bbox_h * rightWeight
    newBboxWidth = left.bbox_w * leftWeight + right.bbox_w * rightWeight

    return Tracking3DResult(
        frame_idx=frameNum,
        point=tuple(newPoint.tolist()),
        bbox_left=newBboxLeft,
        bbox_top=newBboxTop,
        bbox_h=newBboxHeight,
        bbox_w=newBboxWidth,
        detection_id=None,
        object_id=None,
        point_from_camera=None,
        object_type=None,
        timestamp=None,
    )


class MovableObject(NamedTuple):
    id: "int"
    type: "str"
    track: "list[npt.NDArray[np.floating]]"
    bboxes: "list[Float4]"
    frame_ids: "list[int]"
    camera_id: "str"


def get_object_list(
    objects: "dict[str, list[QueryResult]]",
    trackings: "dict[str, list[T3DMetadatum]]",
) -> "list[MovableObject]":
    tracks: "dict[str, dict[int, list[npt.NDArray[np.floating]]]]" = {}
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
            frameId, objectId, cameraId, filename = obj
            objectNum = int(objectId.split("_")[-1])

            if objectNum in trackings[video][frameId]:
                track = trackings[video][frameId][objectNum]
            else:
                track = interpolate_track(trackings, video, objectNum, frameId)

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
