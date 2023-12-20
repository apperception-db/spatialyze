import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (distance(o, o), "ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp))"),
    (distance(o, c), "ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.cameraTranslation)"),
    (distance(c.cam, c.ego), "ST_Distance(c0.cameraTranslation,c0.egoTranslation)"),
])
def test_distance(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (distance(1, o), "LiteralNode(value=1, python=True)"),
    (distance(o, 1), "LiteralNode(value=1, python=True)"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
