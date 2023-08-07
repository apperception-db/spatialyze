import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (road_direction(o.trans@c.time), 
        "roadDirection(valueAtTimestamp(t0.translations,timestamp),(headingAtTimestamp(t0.itemHeadings,timestamp))::real)"),
    (road_direction(o.trans@c.time, c.ego), 
        "roadDirection(valueAtTimestamp(t0.translations,timestamp),egoHeading)"),
    (road_direction(c.ego), 
        "roadDirection(egoTranslation,egoHeading)"),
    (road_direction(c.ego, o.trans@c.time), 
        "roadDirection(egoTranslation,(headingAtTimestamp(t0.itemHeadings,timestamp))::real)"),
])
def test_road_direction(fn, sql):
    assert gen(fn) == sql


