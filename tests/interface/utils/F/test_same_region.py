import pytest
from common import *


o = objects[0]
c = camera


@pytest.mark.parametrize("fn, sql", [
    (same_region('intersection', o, c), "sameRegion('intersection',t0.translation,c0.cameraTranslation)"),
])
def test_same_retion(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (same_region(c, o, o), "Unsupported road type: CameraTableNode[0]"),
    (same_region('invalid', o, o), "Unsupported road type: LiteralNode(value='invalid', python=True)"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg