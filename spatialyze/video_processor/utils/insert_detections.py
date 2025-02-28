import datetime

import shapely.geometry

from ...database import Database
from ...video_processor.stream.data_types import Detection3D


def insert_detections(
    database: Database,
    detections: Detection3D,
    camera_id: str,
    frame_num: int,
    timestamp: datetime.datetime,
):
    dets, clss, dids = detections
    assert len(dets) > 0, dets
    rows: list[tuple[str, str, str, int, bytes, datetime.datetime]] = []
    for did, det in zip(dids, dets):
        fid, oid = did
        det = det.detach().cpu().numpy()
        cls = int(det[5])
        x, y, z = map(float, (det[6:9] + det[9:12]) / 2.0)
        obj = (
            f"{fid}__{oid}",
            camera_id,
            clss[cls],
            frame_num,
            shapely.geometry.Point(x, y, z).wkb,
            timestamp,
        )
        # row = SQL("({})").format(SQL(",").join(map(Literal, obj)))
        # rows.append(row)
        rows.append(obj)

    insert = "INSERT INTO Item_Detection VALUES (?, ?, ?, ?, ST_GeomFromWKB(?), ?, null)"
    database.execute(insert, rows, many=True)
    database._commit()
