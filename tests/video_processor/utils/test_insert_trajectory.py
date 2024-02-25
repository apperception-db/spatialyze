import numpy as np
import pytest
import math

from spatialyze.database import database
from spatialyze.video_processor.utils.insert_trajectory import insert_trajectory
from spatialyze.video_processor.utils.types import Trajectory


@pytest.mark.parametrize("params, output", [
    (
        Trajectory(
            '1',
            [0, 1, 5],
            "1",
            "car",
            [(1, 2, 3), (4, 5, 6), (7, 8, 9)],
            [math.radians(1), None, math.radians(3)],
        ),
        [
            ('1', '1', 'car', 0, 1, (1, 2, 3)),
            ('1', '1', 'car', 1, -45, (4, 5, 6)),
            ('1', '1', 'car', 2, -33, (4.75, 5.75, 6.)),
            ('1', '1', 'car', 3, -21, (5.5, 6.5, 7.)),
            ('1', '1', 'car', 4, -9, (6.25, 7.25, 8.)),
            ('1', '1', 'car', 5, 3, (7, 8, 9)),
        ]
    )
])
def test_insert_trajectory(params, output):
    database.reset()
    for i in range (6):
        database.update(f"insert into Camera values ('1', {i}, {i}, '', null, null, null, null, null, null, null)");
    insert_trajectory(database, params)
    res = database.execute("SELECT itemid, cameraid, objecttype, framenum, itemheading, translation FROM Item_Trajectory WHERE itemid = '1' order by frameNum;")

    assert len(res) == len(output)

    for r, o in zip(res, output):
        assert r[:4] == o[:4]
        assert np.allclose(np.array([r[4], *r[5]]), np.array([o[4], *o[5]]))
