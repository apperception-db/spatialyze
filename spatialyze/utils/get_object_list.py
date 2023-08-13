import numpy as np
import numpy.typing as npt

from ..data_types.camera_config import Float4
from ..video_processor.stages.tracking_3d.tracking_3d import Metadatum as T3DMetadatum


def get_object_list(
    objects: "dict[str, list[tuple]]",
    trackings: "dict[str, list[T3DMetadatum]]",
) -> "list[tuple[int, str, list[npt.NDArray[np.floating]], list[Float4], list[int], str]]":
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

        for frame in trackings[video]:
            for objectId, track in frame.items():
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

    result: "list[tuple[int, str, list[npt.NDArray[np.floating]], list[Float4], list[int], str]]" = []
    for cameraId in tracks:
        for objectId in tracks[cameraId]:
            result.append(
                (
                    objectId,
                    objectTypes[cameraId][objectId],
                    tracks[cameraId][objectId],
                    bboxes[cameraId][objectId],
                    frameIds[cameraId][objectId],
                    cameraId,
                )
            )
    return result
