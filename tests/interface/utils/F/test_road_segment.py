import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (road_segment('road'), 
        "roadSegment('road')")
])
def test_road_segment(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (road_segment('not_valid'), 
        "road_segment() takes a string as argument, received LiteralNode(value='not_valid', python=True)"),
    (road_segment([]), 
        "road_segment() takes a string as argument, received ArrayNode(exprs=[])"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
