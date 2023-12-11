from typing import NamedTuple

from ..data_types.camera_config import Float3, Float4
from ..data_types.query_result import QueryResult
from ..video_processor.stream.deepsort import TrackingResult
from ..video_processor.types import DetectionId


def interpolate_track(
    trackings: dict[int, TrackingResult],
    frameNum: int,
) -> "TrackingResult":
    left, right = None, None
    leftNum, rightNum = frameNum, frameNum

    while left is None:
        leftNum -= 1
        if leftNum in trackings:
            left = trackings[leftNum]

    while right is None:
        rightNum += 1
        if rightNum in trackings:
            right = trackings[rightNum]

    leftWeight = 1 - (frameNum - leftNum) / (rightNum - leftNum)
    rightWeight = (frameNum - leftNum) / (rightNum - leftNum)

    newBbox = (left.bbox * leftWeight) + (right.bbox * rightWeight)

    timedelta = right.timestamp - left.timestamp
    newTimestamp = left.timestamp + timedelta * rightWeight

    return TrackingResult(
        detection_id=DetectionId(frameNum, -1),
        object_id=trackings[0].object_id,
        confidence=trackings[0].confidence,
        bbox=newBbox,
        object_type=trackings[0].object_type,
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
    trackings: "dict[str, list[list[TrackingResult]]]",
) -> "list[MovableObject]":
    tracks: "dict[ObjectListKey, list[Float3]]" = {}
    bboxes: "dict[ObjectListKey, list[Float4]]" = {}
    frameIds: "dict[ObjectListKey, list[int]]" = {}
    objectTypes: "dict[ObjectListKey, str]" = {}

    for video in objects:
        _trackings = trackings[video]
        _trackings = {
            tr[0].object_id: {
                t.detection_id.frame_idx: t
                for t in tr
            }
            for tr in _trackings
        }
        for obj in objects[video]:
            frameId, cameraId, _, objectIds = obj
            for objectId in map(int, objectIds):
                key = ObjectListKey(cameraId, objectId)
                __trackings = _trackings[objectId]

                if frameId in __trackings:
                    track = __trackings[frameId]
                else:
                    track = interpolate_track(__trackings, frameId)

                if key not in tracks:
                    tracks[key] = []
                x, y, z = (track.bbox[6:9] + track.bbox[9:12]) / 2
                tracks[key].append((float(x), float(y), float(z)))

                if key not in bboxes:
                    bboxes[key] = []
                l, t, r, b = track.bbox[:4]
                bbox = float(l), float(t), float(r - l), float(b - t)
                bboxes[key].append(bbox)

                if key not in frameIds:
                    frameIds[key] = []
                frameIds[key].append(track.detection_id.frame_idx)

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
