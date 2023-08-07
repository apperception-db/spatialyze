import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (angle_excluding(1, 2, 3), "angleExcluding(1,2,3)"),
])
def test_angle_excluding(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (angle_excluding(1), 
        "angle_excluding is expecting 3 arguments, but received 1"),
    (angle_excluding(1,2,3,4), 
        "angle_excluding is expecting 3 arguments, but received 4"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    str(e_info.value) == msg
