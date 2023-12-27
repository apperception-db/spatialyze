import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (custom_fn('c1', 1)(1), "c1(1)"),
    (custom_fn('c2', 2)(1, 2), "c2(1,2)"),
    (custom_fn('c3', 3)(1, 2, 3), "c3(1,2,3)"),
])
def test_distance(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (custom_fn('c1', 1)(o, o), "c1 is expecting 1 arguments, but received 2"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
