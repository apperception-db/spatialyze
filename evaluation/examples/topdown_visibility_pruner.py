from collections.abc import Iterable

import numpy as np
from postgis import MultiPoint
from psycopg2 import sql

from spatialyze.database import database
from spatialyze.video_processor.camera_config import CameraConfig
from spatialyze.video_processor.video import Video
from spatialyze.video_processor.stream.data_types import Skip
from spatialyze.video_processor.stream.stream import Stream

BATCH_SIZE = 1000


class TopDownVisibilityPruner(Stream[bool]):
    def _stream(self, video: Video) -> Iterable[bool | Skip]:
        i = 0
        # prev = 0
        # keep: list[int] = []
        N = len(video.camera_configs)
        while i * BATCH_SIZE < N:
            start = i * BATCH_SIZE
            end = min(N, (i + 1) * BATCH_SIZE)
            batch = video.camera_configs[start:end]
            indices, view_areas = get_views(batch)
            results = database.execute(
                sql.SQL(
                    "SELECT index "
                    "FROM UNNEST ({view_areas}, {indices}::int[]) AS ViewArea(points, index) "
                    "JOIN SegmentPolygon ON ST_Intersects(ST_ConvexHull(points), elementPolygon) "
                ).format(
                    view_areas=sql.Literal(view_areas),
                    indices=sql.Literal(indices),
                )
            )
            keep = np.zeros(end - start, dtype=bool)
            # print(np.array(results, dtype=int).shape)
            # print(np.array(results, dtype=int))
            # print(np.array(results, dtype=int)[:, 0])
            keep[np.array(results, dtype=int)[:, 0]] = True
            for k in keep:
                # print(k)
                yield k.item()

            i += 1
        self.end()


def get_views(configs: list[list[tuple[float, float]]] | list[CameraConfig]):
    indices: list[int] = []
    view_areas: list[MultiPoint] = []
    for ind, view_area_2d in enumerate(configs):
        if view_area_2d is None:
            continue

        assert isinstance(view_area_2d, list), view_area_2d
        view_area = MultiPoint(view_area_2d[:4])
        view_areas.append(view_area)
        indices.append(ind)
    if len(indices) == 0:
        print("get-views ----------------", configs)

    return indices, view_areas
