import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (like(o.type, 'human'), 
        "t0.objectType LIKE 'human'"),
    (like(o.type, 'human%'), 
        "t0.objectType LIKE 'human%'"),
])
def test_like(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (like(1), 
        "like accepts 2 arguments"),
    (like(1,2,3), 
        "like accepts 2 arguments"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
