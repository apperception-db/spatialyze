import os
from typing import NamedTuple

import cv2

from ..data_types.query_result import QueryResult
from ..video_processor.stream.strongsort import TrackingResult
from .get_object_list import MovableObject, get_object_list

TEXT_PADDING = 5


def save_video_util(
    objects: "dict[str, list[QueryResult]]",
    trackings: "dict[str, list[list[TrackingResult]]]",
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
        output_file = os.path.join(outputDir, cameraId + "-result.mp4")

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
                        fontScale = 1
                        fontThickness = 2
                        label = f"{object_type}:{object_id}"
                        labelSize, _ = cv2.getTextSize(label, font, fontScale, fontThickness)
                        labelW, labelH = labelSize

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
