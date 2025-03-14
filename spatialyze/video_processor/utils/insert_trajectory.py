from typing import TYPE_CHECKING, TypeVar

import numpy as np
import numpy.typing as npt
import shapely.geometry

from ..types import Float3
from .infer_heading import infer_heading

if TYPE_CHECKING:
    from ...database import Database
    from .types import Trajectory

P1 = TypeVar("P1", Float3, shapely.geometry.Point)
PointTuple = tuple[int | str, str, str, int, P1, float | None]


def insert_trajectory(
    database: "Database",
    trajectory: "Trajectory",
):
    (
        item_id,
        ids,
        camera_id,
        object_type,
        points,
        headings,
    ) = trajectory

    prevPoint: Float3 | None = None
    st, en = ids[0], ids[-1]
    tuples: list[PointTuple[Float3] | None] = [None for _ in range(st, en + 1)]

    P = TypeVar("P", Float3, shapely.geometry.Point)

    def point(idx: int, p: P, h: float | None):
        return (item_id, camera_id, object_type, idx, p, h)

    for i, p, h in zip(ids, points, headings):
        h = infer_heading(h, prevPoint, p)
        tuples[i - st] = point(i, p, h)
        prevPoint = p

    prevHeading: float | None = None
    prevPoint = None
    tuplesWithPoints: list[PointTuple[shapely.geometry.Point]] = []
    for idx in range(st, en + 1):
        i = idx - st
        t = tuples[i]
        if t is None:
            assert prevPoint is not None
            npPrevPoint = np.array(prevPoint)
            npCurrPoint: None | npt.NDArray = None
            for jdx in range(idx, en + 1):
                j = jdx - st
                nt = tuples[j]
                if nt is None:
                    continue
                cp = nt[4]
                assert cp is not None
                npnp = np.array(cp)
                npCurrPoint = npPrevPoint + ((npnp - npPrevPoint) * (i - (i - 1)) / (j - (i - 1)))
                break
            assert isinstance(npCurrPoint, np.ndarray)
            x, y, z = np.array(npCurrPoint)
            t = point(idx, (float(x), float(y), float(z)), None)
            prevPoint = float(x), float(y), float(z)
        else:
            prevPoint = t[4]
        tuplesWithPoints.append(point(idx, shapely.geometry.Point(prevPoint), t[5]))

    tuplesWithPointsHeadings: list[PointTuple[shapely.geometry.Point]] = []
    for i, t in enumerate(tuplesWithPoints):
        h = t[5]
        if h is None and prevHeading is not None:
            for j, nt in enumerate(tuplesWithPoints):
                nh = nt[5]
                if j <= i:
                    continue
                if nh is not None:
                    h = prevHeading + ((nh - prevHeading) * (i - (i - 1)) / (j - (i - 1)))
                    break
        tuplesWithPointsHeadings.append((*t[:5], h))
        prevHeading = h

    insert = "INSERT INTO Item_Trajectory VALUES (?, ?, ?, ?, ST_GeomFromWKB(?), ?)"
    values = map(value, tuplesWithPointsHeadings)
    assert values is not None
    database.execute(insert, values, many=True)
    database._commit()


def value(t: PointTuple[shapely.geometry.Point]):
    return (*t[:4], t[4].wkb, t[5])
