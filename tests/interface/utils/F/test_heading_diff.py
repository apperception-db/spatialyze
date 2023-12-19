import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (distance(o, o), "ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp))"),
    (distance(o, c), "ST_Distance(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.cameraTranslation)"),
    (distance(c.cam, c.ego), "ST_Distance(c0.cameraTranslation,c0.egoTranslation)"),
])
def test_heading_diff(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (heading_diff(1, o), "LiteralNode(value=1, python=True)"),
    (heading_diff(o, 1), "LiteralNode(value=1, python=True)"),
    (heading_diff(o, o, test1=1, test2=2), "2"),
    (heading_diff(o, o, test1=1), "test1"),
    (heading_diff(o, o, between=1), "LiteralNode(value=1, python=True)"),
    (heading_diff(o, o, between=[1]), "1"),
    (heading_diff(o, o, between=[o, c]), "ObjectTableNode[0]"),
    (heading_diff(o, o, between=[1, c]), "CameraTableNode[0]"),
    (heading_diff(o.type, o, between=[1, c]), "ObjectTableNode[0]"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
