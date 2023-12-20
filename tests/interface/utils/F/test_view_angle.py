import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (view_angle(o, c), 
        "viewAngle(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.cameraHeading,c0.cameraTranslation)"),
    (view_angle(o, o), 
        "viewAngle(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.itemHeadings,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp))")
])
def test_view_angle(fn, sql):
    assert gen(fn) == sql
