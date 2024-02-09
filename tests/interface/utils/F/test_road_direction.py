import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (road_direction(o), 
        "roadDirection(t0.translation,(t0.itemHeading)::real)"),
    (road_direction(o, c.ego), 
        "roadDirection(t0.translation,(c0.egoHeading)::real)"),
    (road_direction(c), 
        "roadDirection(c0.cameraTranslation,(c0.cameraHeading)::real)"),
    (road_direction(c.ego, o), 
        "roadDirection(c0.egoTranslation,(t0.itemHeading)::real)"),
])
def test_road_direction(fn, sql):
    assert gen(fn) == sql


