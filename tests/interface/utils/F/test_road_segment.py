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
        "Unsupported road type: not_valid"),
    (road_segment([]), 
        "Unsupported road type: not_valid"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    str(e_info.value) == msg
