from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import numpy.typing as npt
import psycopg2.sql as psql
from postgis import Point
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


L = psql.Literal


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
    camera_sqls: "list[psql.Composable]" = []
    # item_sqls: "list[psql.Composable]" = []
    print("Ingesting Cameras and Annotations")
    for k in tqdm(ks, total=len(ks)):
        camera = camera_map[k]
        annotations = annotations_map[k]

        objects: "dict[str, _MovableObject]" = {}
        cc_map: "dict[str, tuple[int, NuscenesCamera]]" = {}
        for idx, cc in enumerate(camera):
            assert cc.token not in cc_map
            cc_map[cc.token] = (idx, cc)
            fields: "list[tuple[str, psql.Composable]]" = [
                ("camera_id", L(str(k))),
                ("frame_id", L(cc.token)),
                ("frame_num", L(idx)),
                ("filename", L(cc.filename)),
                ("camera_translation", L(Point(*cc.camera_translation))),
                ("camera_rotation", L(list(cc.camera_rotation))),
                ("camera_intrinsic", L(list(cc.camera_intrinsic))),
                ("ego_translation", L(Point(*cc.ego_translation))),
                ("ego_rotation", L(list(cc.ego_rotation))),
                ("timestamp", L(datetime.fromtimestamp(cc.timestamp / 1000000.0))),
                ("cameraHeading", L(cc.camera_heading)),
                ("egoHeading", L(cc.ego_heading)),
            ]
            brackets = ",".join(["{}"] * len(fields))
            camera_sqls.append(psql.SQL(f"({brackets})").format(*(v for _, v in fields)))

        query = psql.SQL(
            "INSERT INTO Camera ("
            "cameraId, frameId, "
            "frameNum, fileName, "
            "cameraTranslation, cameraRotation, "
            "cameraIntrinsic, egoTranslation, "
            "egoRotation, timestamp, "
            "cameraHeading, egoHeading"
            ") VALUES {}"
        ).format(psql.SQL(",").join(camera_sqls))
        database.update(query)

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
            assert len(frame_nums) == 0 or all(p < n for p, n in zip(frame_nums[:-1], frame_nums[1:])), frame_nums

            traj = Trajectory(
                item_id,
                frame_nums.tolist(),
                str(k),
                obj.object_type,
                translations.tolist(),
                itemHeadings.tolist(),
            )

            insert_trajectory(database, traj)
