import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (convert_camera(o, c.ego),
        "ConvertCamera(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.egoTranslation,c0.egoHeading)"),
    (convert_camera(o, c),
        "ConvertCamera(valueAtTimestamp(t0.trajCentroids,c0.timestamp),c0.cameraTranslation,c0.cameraHeading)"),
    # (convert_camera(o, o),
    #     "ConvertCamera(valueAtTimestamp(t0.trajCentroids,c0.timestamp),valueAtTimestamp(t0.trajCentroids,timestamp),valueAtTimestamp(t0.itemHeadings,c0.timestamp))"),
])
def test_convert_camera(fn, sql):
    assert gen(fn) == sql