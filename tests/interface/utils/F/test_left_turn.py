import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (left_turn(o), 
        "leftTurn(t0.translations, t0.itemHeadings, Cameras.frameNum, Cameras.cameraId)"),
])
def test_left_turn(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (left_turn(c), "leftTurn accepts ObjectTableNode, got CameraTableNode"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
