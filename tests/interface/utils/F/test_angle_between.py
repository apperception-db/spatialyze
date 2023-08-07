import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (angle_between(1, 2, 3), "angleBetween(1,2,3)"),
])
def test_angle_between(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (angle_between(1), 
        "angle_between is expecting 3 arguments, but received 1"),
    (angle_between(1,2,3,4), 
        "angle_between is expecting 3 arguments, but received 4"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    str(e_info.value) == msg