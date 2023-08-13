import cv2

from ..video_processor.stages.tracking_3d.tracking_3d import Metadatum as T3DMetadatum
from ..video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult


def save_video_util(
    objects: "dict[str, list[tuple]]",
    trackings: "dict[str, list[T3DMetadatum]]",
    VIDEO_PATH: "str",
    OUTPUT_PATH: "str",
    is_bbox: "bool" = False,
):
    frame_trackings = _get_frame_objects(trackings)
    cameraIds = _get_camera_ids(objects)

    for videoname, frame_tracking in frame_trackings.items():
        cameraId = cameraIds[videoname]
        video_file = VIDEO_PATH + videoname
        output_file = OUTPUT_PATH + cameraId + "-result.mp4"

        cap = cv2.VideoCapture(video_file)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        vid_writer = cv2.VideoWriter(
            output_file, cv2.VideoWriter_fourcc("m", "p", "4", "v"), 30, (width, height)
        )

        frame_cnt = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if is_bbox:
                for track in frame_tracking.get(frame_cnt, []):
                    bbox_left, bbox_top, bbox_w, bbox_h = (
                        track.bbox_left,
                        track.bbox_top,
                        track.bbox_w,
                        track.bbox_h,
                    )
                    x1, y1 = bbox_left, bbox_top
                    x2, y2 = bbox_left + bbox_w, bbox_top - bbox_h
                    frame = cv2.rectangle(
                        frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2
                    )

            vid_writer.write(frame)
            frame_cnt += 1

        vid_writer.release()


def _get_frame_objects(trackings: "dict[str, list[T3DMetadatum]]"):
    """
    Indexes objects based on frame ID
    """
    result: "dict[str, dict[int, list[Tracking3DResult]]]" = {}
    for video, tracking in trackings.items():
        result[video] = {}
        for frame in tracking:
            for objectId in frame:
                track = frame[objectId]
                frameId = track.frame_idx
                if frameId not in result[video]:
                    result[video][frameId] = []
                result[video][frameId].append(track)

    return result


def _get_camera_ids(objects: "dict[str, list[tuple]]"):
    """
    Gets the cameraIds relating to each of the videos
    """
    result: "dict[str, str]" = {}
    for video, obj in objects.items():
        if len(obj) == 0:
            continue

        result[video] = obj[0][2]
    return result
