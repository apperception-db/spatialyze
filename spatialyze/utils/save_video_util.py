import cv2


def save_video_util(objects, trackings, VIDEO_PATH, OUTPUT_PATH, is_bbox=False, is_label=False):
    frame_trackings = _get_frame_objects(trackings=trackings)
    cameraIds = _get_camera_ids(objects=objects)

    for video in frame_trackings:
        cameraId = cameraIds[video]
        video_file = VIDEO_PATH + video
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

            if frame_cnt in frame_trackings and ret:
                if is_bbox:
                    for track in frame_trackings[frame_cnt]:
                        bbox_left, bbox_top, bbox_w, bbox_h = (
                            track.bbox_left,
                            track.bbox_top,
                            track.bbox_w,
                            track.bbox_h,
                        )
                        x1, y1 = bbox_left, bbox_top
                        x2, y2 = bbox_left + bbox_w, bbox_top - bbox_h
                        cv2.rectangle(
                            frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2
                        )

                vid_writer.write(frame)

            frame_cnt += 1
            if not ret:
                break

        vid_writer.release()


"""
Indexes objects based on frame ID
"""


def _get_frame_objects(trackings):
    result = {}
    for video in trackings:
        result[video] = {}
        for frame in trackings[video]:
            for objectId in frame:
                track = frame[objectId]
                frameId = track.frame_idx
                result[video][frameId] = track

    return result


"""
Gets the cameraIds relating to each of the videos
"""


def _get_camera_ids(objects):
    result = {}
    for video in objects:
        if len(objects[video]) == 0:
            continue

        result[video] = objects[video][0][2]
    return result
