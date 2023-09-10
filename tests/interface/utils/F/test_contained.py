import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (contained(1, 2), "contained(1,2)"),
    (contained(objects[0], 'intersection'), "contained(valueAtTimestamp(t0.trajCentroids,timestamp),'intersection')"),
    (contained(objects[0]@camera.time, 'intersection'), "contained(valueAtTimestamp(t0.trajCentroids,timestamp),'intersection')"),
    (contained(objects[0].traj@camera.time, 'intersection'), "contained(valueAtTimestamp(t0.trajCentroids,timestamp),'intersection')"),
])
def test_contained(fn, sql):
    assert gen(fn) == sql
