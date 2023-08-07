import pytest
from common import *


o = objects[0]
c = camera


@pytest.mark.parametrize("fn, sql", [
    (ahead(o.trans@c.time, c.ego), 
        "ahead(valueAtTimestamp(t0.translations,timestamp),egoTranslation,egoHeading)"),
    (ahead(o.trans@c.time, c.cam), 
        "ahead(valueAtTimestamp(t0.translations,timestamp),cameraTranslation,cameraHeading)"),
    (ahead(o.trans@c.time, o.trans@c.time), 
        "ahead(valueAtTimestamp(t0.translations,timestamp),valueAtTimestamp(t0.translations,timestamp),(headingAtTimestamp(t0.itemHeadings,timestamp))::real)"),
])
def test_ahead(fn, sql):
    assert gen(fn) == sql
