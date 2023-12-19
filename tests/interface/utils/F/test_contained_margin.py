import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (contained_margin(1, 2, 3), "containedMargin(1,2,3)"),
])
def test_contained_margin(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (contained_margin(1), 
        "containedMargin is expecting 3 arguments, but received 1"),
    (contained_margin(1,2,3,4), 
        "containedMargin is expecting 3 arguments, but received 4"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
