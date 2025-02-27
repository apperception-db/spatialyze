from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import numpy.typing as npt
import shapely.geometry
from tqdm import tqdm

from ..data_types.camera_key import CameraKey
from ..data_types.nuscenes_annotation import NuscenesAnnotation
from ..data_types.nuscenes_camera import NuscenesCamera
from ..video_processor.utils.insert_trajectory import insert_trajectory
from ..video_processor.utils.types import Trajectory

if TYPE_CHECKING:
    from ..database import Database


class _MovableObject(NamedTuple):
    object_type: "str"
    frame_num: list[int]
    bboxes: "list[npt.NDArray]"
    timestamps: "list[int]"
    itemHeading: "list[float]"
    translations: "list[list[float]]"


class _Camera(NamedTuple):
    camera_id: "str"
    frame_id: "str"
    frame_num: "int"
    filename: "str"
    camera_translation: "bytes"
    camera_rotation: "list[float]"
    camera_intrinsic: "list[list[float]]"
    ego_translation: "bytes"
    ego_rotation: "list[float]"
    timestamp: "datetime"
    cameraHeading: "float"
    egoHeading: "float"


def ingest_processed_nuscenes(
    annotations_map: "dict[CameraKey, list[NuscenesAnnotation]]",
    camera_map: "dict[CameraKey, list[NuscenesCamera]]",
    database: "Database",
):
    keys = [k for k in camera_map.keys() if camera_map[k][0].location == "boston-seaport"]
    # print(len(keys))
    # ks = [k for k in keys if camera_map[k][0].location == 'boston-seaport']
    # print(len(ks))
    # ks = ks[:len(ks) // 5]
    # print(len(ks))
    ks = keys
    # camera_sqls: "list[psql.Composable]" = []
    # item_sqls: "list[psql.Composable]" = []
    print("Ingesting Cameras and Annotations")
    for k in tqdm(ks, total=len(ks)):
        camera = camera_map[k]
        annotations = annotations_map[k]

        objects: "dict[str, _MovableObject]" = {}
        cc_map: "dict[str, tuple[int, NuscenesCamera]]" = {}
        camera_sqls: "list[_Camera]" = []
        for idx, cc in enumerate(camera):
            assert cc.token not in cc_map
            cc_map[cc.token] = (idx, cc)
            fields = _Camera(
                camera_id=str(k),
                frame_id=cc.token,
                frame_num=idx,
                filename=cc.filename,
                camera_translation=shapely.geometry.Point(*cc.camera_translation).wkb,
                camera_rotation=list(cc.camera_rotation),
                camera_intrinsic=list(cc.camera_intrinsic),
                ego_translation=shapely.geometry.Point(*cc.ego_translation).wkb,
                ego_rotation=list(cc.ego_rotation),
                timestamp=datetime.fromtimestamp(cc.timestamp / 1000000.0),
                cameraHeading=cc.camera_heading,
                egoHeading=cc.ego_heading,
            )
            camera_sqls.append(fields)

        query = (
            "INSERT INTO Camera ("
            "cameraId, frameId, "
            "frameNum, fileName, "
            "cameraTranslation, cameraRotation, "
            "cameraIntrinsic, egoTranslation, "
            "egoRotation, timestamp, "
            "cameraHeading, egoHeading"
            ") VALUES (?, ?, ?, ?, ST_GeomFromWKB(?), ?, ?, ST_GeomFromWKB(?), ?, ?, ?, ?)"
        )
        database.update(query, vars=camera_sqls, many=True)

        for a in annotations:
            cc_idx, cc = cc_map[a.sample_data_token]
            timestamp = cc.timestamp
            item_id = f"{cc.channel}_{a.instance_token}"
            if item_id not in objects:
                objects[item_id] = _MovableObject(
                    object_type=a.category,
                    frame_num=[],
                    bboxes=[],
                    timestamps=[],
                    itemHeading=[],
                    translations=[],
                )
            # box = Box(a.translation, a.size, Quaternion(a.rotation))
            # corners = box.corners()
            # bbox = np.transpose(corners[:, [3, 7]])

            # objects[item_id].bboxes.append(bbox)
            objects[item_id].timestamps.append(timestamp)
            objects[item_id].itemHeading.append(a.heading)
            objects[item_id].translations.append(a.translation)
            objects[item_id].frame_num.append(cc_idx)

        for item_id, obj in objects.items():
            timestamps = np.array(obj.timestamps)
            # bboxes = np.array(obj.bboxes)
            itemHeadings = np.array(obj.itemHeading)
            translations = np.array(obj.translations)
            frame_nums = np.array(obj.frame_num)

            index = timestamps.argsort()

            timestamps = [datetime.fromtimestamp(t / 1000000.0) for t in timestamps[index].tolist()]
            # obj.bboxes = [bboxes[i, :, :] for i in index]
            itemHeadings = itemHeadings[index]
            translations = translations[index]
            frame_nums = frame_nums[index]
            assert len(frame_nums) == 0 or all(
                p < n for p, n in zip(frame_nums[:-1], frame_nums[1:])
            ), frame_nums

            traj = Trajectory(
                item_id,
                frame_nums.tolist(),
                str(k),
                obj.object_type,
                translations.tolist(),
                itemHeadings.tolist(),
            )

            insert_trajectory(database, traj)
