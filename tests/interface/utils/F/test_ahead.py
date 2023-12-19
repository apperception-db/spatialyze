import pytest
from common import *


o = objects[0]
c = camera


@pytest.mark.parametrize("fn, sql", [
    (ahead(o, c.ego), 
        "ahead(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.egoTranslation,c0.egoHeading)"),
    (ahead(o, c.cam), 
        "ahead(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.cameraTranslation,c0.cameraHeading)"),
    (ahead(o, o), 
        "ahead(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.itemHeadings,c0.timestamp))"),
])
def test_ahead(fn, sql):
    assert gen(fn) == sql
