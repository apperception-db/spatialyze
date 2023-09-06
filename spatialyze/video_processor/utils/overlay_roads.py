from multiprocessing import Pool
from os import environ
from typing import TYPE_CHECKING

import cv2
import numpy as np
import numpy.typing as npt
import postgis
import psycopg2
from psycopg2 import sql
from tqdm import tqdm

from spatialyze.database import Database

from ..camera_config import CameraConfig
from ..stages.tracking_3d.from_tracking_2d_and_road import rotate
from ..utils.iterate_video import iterate_video

if TYPE_CHECKING:
    from ..payload import Payload


def overlay_to_frame(args: "tuple[CameraConfig, npt.NDArray]") -> "npt.NDArray":
    database = Database(
        psycopg2.connect(
            dbname=environ.get("AP_DB", "mobilitydb"),
            user=environ.get("AP_USER", "docker"),
            host=environ.get("AP_HOST", "localhost"),
            port=environ.get("AP_PORT", "25432"),
            password=environ.get("AP_PASSWORD", "docker"),
        )
    )
    frame, img = args
    intrinsic = np.array(frame.camera_intrinsic)
    polygons: "list[tuple[postgis.Polygon]]" = database.execute(
        sql.SQL(
            """
            SELECT elementPolygon
            FROM SegmentPolygon
            WHERE
                ST_Distance({camera}, elementPolygon) < 10
                AND location = {location}"""
        ).format(
            camera=sql.Literal(postgis.Point(*frame.camera_translation)),
            location=sql.Literal(frame.location),
        )
    )
    polygons = [p[0] for p in polygons]
    width = 1600
    height = 900
    for (p,) in polygons:
        if isinstance(p, postgis.polygon.Polygon):
            raise Exception()
        coords = np.vstack([np.array(p.coords).T, np.zeros((1, len(p.coords)))])
        coords = coords - np.array(frame.camera_translation)[:, np.newaxis]
        coords = rotate(coords, frame.camera_rotation.inverse.unit)
        coords = intrinsic @ coords
        coords = coords / coords[2:3, :]

        prev = None
        for c in coords.T[:, :2]:
            if prev is not None:
                ret, p1, p2 = cv2.clipLine((0, 0, width, height), prev.astype(int), c.astype(int))
                if ret:
                    img = cv2.line(img, p1, p2, (0, 0, 200), 3)
            prev = c
    return img


def overlay_roads(payload: "Payload", filename: str) -> None:
    video = cv2.VideoCapture(payload.video.videofile)

    with Pool() as pool:
        imgs = pool.imap(overlay_to_frame, zip(payload.video, iterate_video(video)))
        out: "None | cv2.VideoWriter" = None
        for image in tqdm(imgs, total=len(payload.video)):
            if out is None:
                height, width, _ = image.shape
                out = cv2.VideoWriter(
                    filename,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    int(payload.video.fps),
                    (width, height),
                )
            assert out is not None
            out.write(image)
        assert out is not None
        out.release()
        cv2.destroyAllWindows()
