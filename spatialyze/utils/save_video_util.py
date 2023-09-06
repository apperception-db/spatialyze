import os

import cv2

from ..data_types.query_result import QueryResult
from ..video_processor.stages.tracking_3d.tracking_3d import Metadatum as T3DMetadatum
from .get_object_list import MovableObject, get_object_list


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

    for videoname, frame_tracking in bboxes.items():
        cameraId = video_to_camera[videoname]
        output_file = os.path.join(outputDir, cameraId + "-result.mp4")

        cap = cv2.VideoCapture(videoname)
        if not cap.isOpened():
            print(f"WARNING: Cannot read video file: {videoname}")
            continue

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        vid_writer = cv2.VideoWriter(
            output_file, cv2.VideoWriter_fourcc(*"mp4v"), 30, (width, height)
        )

        frame_cnt = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_cnt in frame_tracking:
                if addBoundingBoxes:
                    for bbox in frame_tracking.get(frame_cnt, []):
                        object_id, bbox_left, bbox_top, bbox_w, bbox_h = bbox
                        x1, y1 = bbox_left, bbox_top
                        x2, y2 = bbox_left + bbox_w, bbox_top + bbox_h
                        frame = cv2.rectangle(
                            frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2
                        )

                        frame = cv2.putText(
                            frame,
                            str(object_id),
                            (int(bbox_left), int(bbox_top)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (255, 0, 0),
                            2,
                            cv2.LINE_AA,
                        )
                vid_writer.write(frame)
                result.append((videoname, frame_cnt))

            frame_cnt += 1

        vid_writer.release()

    return result


def _get_bboxes(objList: "list[MovableObject]", cameraVideoNames: "dict[str, str]"):
    """
    Indexes objects based on frame ID
    """
    result: "dict[str, dict[int, list[tuple[int, float, float, float, float]]]]" = {}
    for obj in objList:
        for i, frameId in enumerate(obj.frame_ids):
            videoName = cameraVideoNames[obj.camera_id]
            if videoName not in result:
                result[videoName] = {}

            if frameId not in result[videoName]:
                result[videoName][frameId] = []

            result[videoName][frameId].append((obj.id, *obj.bboxes[i]))

    return result


def _get_video_names(objects: "dict[str, list[QueryResult]]"):
    """
    Returns mappings from videoName to cameraId and vice versa
    """
    camera_to_video: "dict[str, str]" = {}
    video_to_camera: "dict[str, str]" = {}
    for video, obj in objects.items():
        if len(obj) == 0:
            continue

        cameraId = obj[0][2]
        camera_to_video[cameraId] = video
        video_to_camera[video] = cameraId
    return camera_to_video, video_to_camera
