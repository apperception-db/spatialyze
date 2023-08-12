def get_object_list(objects, trackings):
    tracks = {}
    bboxes = {}
    frameIds = {}
    objectTypes = {}

    for video in objects:
        videoObjects = objects[video]
        if len(videoObjects) == 0:
            continue
        
        cameraId = videoObjects[0][2] # cameraId same for everything in a video    
        tracks[cameraId] = {}
        bboxes[cameraId] = {}
        frameIds[cameraId] = {}
        objectTypes[cameraId] = {}

        for frame in trackings[video]:
            for objectId in frame:
                track = frame[objectId]

                if objectId not in tracks[cameraId]:
                    tracks[cameraId][objectId] = []
                    bboxes[cameraId][objectId] = []
                    frameIds[cameraId][objectId] = []

                tracks[cameraId][objectId].append(track.point)
                bboxes[cameraId][objectId].append((track.bbox_left, track.bbox_top, track.bbox_w, track.bbox_h))
                frameIds[cameraId][objectId].append(track.frame_idx)
                objectTypes[cameraId][objectId] = track.object_type

    result = []
    for cameraId in tracks:
        for objectId in tracks[cameraId]:
            result.append((
                objectId,
                objectTypes[cameraId][objectId],
                tracks[cameraId][objectId],
                bboxes[cameraId][objectId],
                frameIds[cameraId][objectId],
                cameraId
            ))
    return result