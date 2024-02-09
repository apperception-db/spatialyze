import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (view_angle(o, c), 
        "viewAngle(t0.translation,c0.cameraHeading,c0.cameraTranslation)"),
    (view_angle(o, o), 
        "viewAngle(t0.translation,t0.itemHeading,t0.translation)")
])
def test_view_angle(fn, sql):
    assert gen(fn) == sql
