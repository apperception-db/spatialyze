import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (get_x(o.trans@c.time), 
        "st_x(valueAtTimestamp(t0.translations,timestamp))"),
    (get_x(c.ego), 
        "st_x(egoTranslation)"),
    (get_y(o.trans@c.time), 
        "st_y(valueAtTimestamp(t0.translations,timestamp))"),
    (get_y(c.ego), 
        "st_y(egoTranslation)"),
    (get_z(o.trans@c.time), 
        "st_z(valueAtTimestamp(t0.translations,timestamp))"),
    (get_z(c.ego), 
        "st_z(egoTranslation)"),
])

def test_get_(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (get_x(), 
        "get_x is expecting 1 arguments, but received 0"),
    (get_x(1,2), 
        "get_x is expecting 1 arguments, but received 2"),
    (get_y(), 
        "get_y is expecting 1 arguments, but received 0"),
    (get_y(1,2), 
        "get_y is expecting 1 arguments, but received 2"),
    (get_z(), 
        "get_z is expecting 1 arguments, but received 0"),
    (get_z(1,2), 
        "get_z is expecting 1 arguments, but received 2"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    str(e_info.value) == msg

