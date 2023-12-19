import pytest
from common import *


o = objects[0]
c = camera


@pytest.mark.parametrize("fn, sql", [
    (stopped(o), "(ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp+interval '5 secs'))<5)"),
    (stopped(o, distance=3.1), "(ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp+interval '5 secs'))<3.1)"),
    (stopped(o, duration=6.5), "(ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp+interval '6.5 secs'))<5)"),
    (stopped(o, distance=3.1, duration=6.5), "(ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp+interval '6.5 secs'))<3.1)"),
])
def test_stopped(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (stopped(c), "CameraTableNode[0]"),
    (stopped(o, illegal=1), "{'illegal': LiteralNode(value=1, python=True)}"),
    (stopped(o, distance=c), "CameraTableNode[0]"),
    (stopped(o, duration=c), "CameraTableNode[0]"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg