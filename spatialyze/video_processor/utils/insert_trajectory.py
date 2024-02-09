from typing import TypeVar

import numpy as np
import numpy.typing as npt
from postgis import Point
from psycopg2.sql import SQL, Literal

from ...database import Database
from ..types import Float3
from ..utils.prepare_trajectory import Trajectory
from .infer_heading import infer_heading


def insert_trajectory(
    database: "Database",
    trajectory: Trajectory,
):
    (
        item_id,
        ids,
        camera_id,
        object_type,
        pairs,
        itemHeading_list,
    ) = trajectory

    prevPoint: Float3 | None = None
    st, en = ids[0], ids[-1]
    tuples: list[tuple[int | str, str, str, int, Float3, float | None] | None] = [
        None for _ in range(st, en + 1)
    ]

    P = TypeVar("P", Float3, Point)

    def point(idx: int, p: P, h: float | None) -> tuple[int | str, str, str, int, P, float | None]:
        return (item_id, camera_id, object_type, idx, p, h)

    for idx, current_point, curItemHeading in zip(
        ids,
        pairs,
        itemHeading_list,
    ):
        # Construct trajectory
        heading = infer_heading(curItemHeading, prevPoint, current_point)
        tuples[idx - st] = point(idx, current_point, heading)
        prevPoint = current_point

    prevHeading: float | None = None
    prevPoint = None
    _tuples: list[tuple[int | str, str, str, int, Point, float | None]] = []
    for idx in range(st, en + 1):
        i = idx - st
        t = tuples[i]
        if t is None:
            assert prevPoint is not None
            nppp = np.array(prevPoint)
            npcp: None | npt.NDArray = None
            for j in range(st, en + 1):
                j -= st
                if j <= i:
                    continue
                nt = tuples[j]
                if nt is None:
                    continue
                cp = nt[4]
                assert cp is not None
                npnp = np.array(cp)
                npcp = nppp + ((npnp - nppp) * (i - (i - 1)) / (j - (i - 1)))
                break
            assert isinstance(npcp, np.ndarray)
            x, y, z = np.array(npcp)
            t = point(idx, (float(x), float(y), float(z)), None)
            prevPoint = float(x), float(y), float(z)
        else:
            prevPoint = t[4]
        _tuples.append(point(idx, Point(prevPoint), None))

    __tuples: list[tuple[int | str, str, str, int, Point, float | None]] = []
    for i, t in enumerate(_tuples):
        h = t[5]
        if h is None and prevHeading is not None:
            for j, nt in enumerate(_tuples):
                nh = nt[5]
                if j <= i:
                    continue
                if nh is not None:
                    h = prevHeading + ((nh - prevHeading) * (i - (i - 1)) / (j - (i - 1)))
                    break
        __tuples.append(t[:5] + (h,))
        prevHeading = h

    obj = SQL(",").join(map(value, __tuples))
    insert = SQL("INSERT INTO Item_Trajectory2 VALUES {}")
    database.execute(insert.format(obj))
    database._commit()


def value(t: tuple[int | str, str, str, int, Point, float | None]):
    return SQL("(") + SQL(",").join(map(Literal, t)) + SQL(")")
