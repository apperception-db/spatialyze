import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (road_direction(o), 
        "roadDirection(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.itemHeadings,c0.timestamp))"),
    (road_direction(o, c.ego), 
        "roadDirection(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.egoHeading)"),
    (road_direction(c), 
        "roadDirection(c0.cameraTranslation,c0.cameraHeading)"),
    (road_direction(c.ego, o), 
        "roadDirection(c0.egoTranslation,valueAtTimestamp(t0.itemHeadings,c0.timestamp))"),
])
def test_road_direction(fn, sql):
    assert gen(fn) == sql


