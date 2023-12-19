import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (has_types(o, 'test'), "((t0.objectType = 'test'))"),
    (has_types(o, 'test', 'test2'), "((t0.objectType = 'test') OR (t0.objectType = 'test2'))"),
    (has_types(o, ['test']), "((t0.objectType = 'test'))"),
    (has_types(o, ['test', 'test2']), "((t0.objectType = 'test') OR (t0.objectType = 'test2'))"),
])
def test_has_types(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (has_types(c, 'test'), 
        "CameraTableNode[0]"),
    (has_types(o, c), 
        "['CameraTableNode[0]']"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
