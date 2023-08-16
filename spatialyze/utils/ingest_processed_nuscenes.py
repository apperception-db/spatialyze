from tqdm import tqdm
from datetime import datetime
import numpy as np
import numpy.typing as npt
from typing import TYPE_CHECKING, NamedTuple
import psycopg2.sql as psql
from postgis import Point
from mobilitydb import TGeomPointInst, TGeomPointSeq, TFloatSeq, TFloatInst

from ..data_types.camera_key import CameraKey
from ..data_types.nuscenes_annotation import NuscenesAnnotation
from ..data_types.nuscenes_camera import NuscenesCamera

if TYPE_CHECKING:
    from ..database import Database


class _MovableObject(NamedTuple):
    object_type: "str"
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
    keys = list(camera_map.keys())
    # print(len(keys))
    # ks = [k for k in keys if camera_map[k][0].location == 'boston-seaport']
    # print(len(ks))
    # ks = ks[:len(ks) // 5]
    # print(len(ks))
    ks = keys
    camera_sqls: "list[psql.Composable]" = []
    item_sqls: "list[psql.Composable]" = []
    print('Ingesting Cameras and Annotations')
    for k in tqdm(ks, total=len(ks)):
        camera = camera_map[k]
        if camera[0].location != 'boston-seaport':
            continue
        annotations = annotations_map[k]

        objects: "dict[str, _MovableObject]" = {}
        cc_map: "dict[str, NuscenesCamera]" = {}
        for idx, cc in enumerate(camera):
            assert cc.token not in cc_map
            cc_map[cc.token] = cc
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
            brackets = ','.join(['{}'] * len(fields))
            camera_sqls.append(psql.SQL(f"({brackets})").format(*(v for _, v in fields)))

        for a in annotations:
            cc = cc_map[a.sample_data_token]
            timestamp = cc.timestamp
            item_id = f"{cc.channel}_{a.instance_token}"
            if item_id not in objects:
                objects[item_id] = _MovableObject(
                    object_type=a.category,
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

        for item_id, obj in objects.items():
            timestamps = np.array(obj.timestamps)
            # bboxes = np.array(obj.bboxes)
            itemHeadings = np.array(obj.itemHeading)
            translations = np.array(obj.translations)

            index = timestamps.argsort()

            timestamps = [datetime.fromtimestamp(t / 1000000.0) for t in timestamps[index].tolist()]
            # obj.bboxes = [bboxes[i, :, :] for i in index]
            itemHeadings = itemHeadings[index]
            translations = translations[index]

            # bboxes = np.array(obj.bboxes)
            # converted_bboxes = [bbox_to_data3d(bbox) for bbox in bboxes]

            # pairs = []
            # deltas = []
            # for meta_box in converted_bboxes:
            #     pairs.append(meta_box[0])
            #     deltas.append(meta_box[1:])
            trajectory = [TGeomPointInst(Point(*p), t) for p, t in zip(translations, timestamps)]
            headings = [TFloatInst(f, t) for f, t in zip(itemHeadings, timestamps)]
            item_sqls.append(psql.SQL("""(
                {item_id},      {camera_id},
                {object_type},  {traj_centroids},
                {translations}, {item_headings}
            )""").format(
                item_id=L(item_id),
                camera_id=L(str(k)),
                object_type=L(obj.object_type),
                traj_centroids=L(TGeomPointSeq(trajectory, upper_inc=True)),
                translations=L(TGeomPointSeq(trajectory, upper_inc=True)),
                item_headings=L(TFloatSeq(headings, upper_inc=True)),
            ))
        camera_sqls, item_sqls = _flush(camera_sqls, item_sqls, database, 1000)
    _flush(camera_sqls, item_sqls, database)


def _flush(
    camera_sqls: "list[psql.Composable]",
    item_sqls: "list[psql.Composable]",
    database: "Database",
    threshold: "int | None" = None,
) -> "tuple[list[psql.Composable], list[psql.Composable]]":
    if threshold is None or len(camera_sqls) + len(item_sqls) >= threshold:
        query = psql.SQL("""
        INSERT INTO Cameras (cameraId, frameId, frameNum, fileName,
            cameraTranslation, cameraRotation, cameraIntrinsic,
            egoTranslation, egoRotation, timestamp, cameraHeading, egoHeading)
        VALUES {}""").format(psql.SQL(",").join(camera_sqls))
        database.update(query)

        if len(item_sqls) != 0:
            query = psql.SQL("""
            INSERT INTO Item_General_Trajectory (ItemId, CameraId,
                ObjectType, TrajCentroids, Translations, ItemHeadings)
            VALUES {}""").format(psql.SQL(",").join(item_sqls))
            database.update(query)
        return [], []
    return camera_sqls, item_sqls

