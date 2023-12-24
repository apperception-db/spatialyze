import datetime

from postgis import Point
from psycopg2.sql import SQL, Composed, Literal

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
    if len(dets) == 0:
        return
    rows: list[Composed] = []
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
            Point(x, y, z),
            timestamp,
        )
        row = SQL("({})").format(SQL(",").join(map(Literal, obj)))
        rows.append(row)

    insert = SQL("INSERT INTO Item_Detection VALUES ")
    database.execute(insert + SQL(",").join(rows))
    database._commit()
