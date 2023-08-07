import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (contained(1, 2), "contained(1,2)"),
])
def test_contained(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (contained(1), 
        "contained is expecting 2 arguments, but received 1"),
    (contained(1,2,3), 
        "contained is expecting 2 arguments, but received 3"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    str(e_info.value) == msg

