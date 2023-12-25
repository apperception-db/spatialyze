import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (contained_margin(o.bbox, road_segment('intersection'), 3), "containedMargin(objectBBox(t0.itemId,c0.timestamp),roadSegment('intersection'),3)"),
])
def test_contained_margin(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (contained_margin(o.trans, road_segment('intersection'), o), "ObjectTableNode"),
    (contained_margin(o.trans,o,3), "ObjectTableNode"),
    (contained_margin(1, road_segment('intersection'), 3), "LiteralNode"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
