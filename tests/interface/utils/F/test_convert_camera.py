import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (convert_camera(o.trans@c.time, c.ego),
        "ConvertCamera(valueAtTimestamp(t0.translations,timestamp),egoTranslation,egoHeading)"),
    (convert_camera(o.trans@"2004-10-19 10:23:54", c.cam),
        "ConvertCamera(valueAtTimestamp(t0.translations,'2004-10-19 10:23:54'),cameraTranslation,cameraHeading)"),
    (convert_camera(o.trans@c.time, o.trans@c.time),
        "ConvertCamera(valueAtTimestamp(t0.translations,timestamp),valueAtTimestamp(t0.translations,timestamp),(headingAtTimestamp(t0.itemHeadings,timestamp))::real)"),
])
def test_convert_camera(fn, sql):
    assert gen(fn) == sql
