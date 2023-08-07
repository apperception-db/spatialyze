import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (facing_relative(o.trans@c.time, c.ego), 
        "facingRelative((headingAtTimestamp(t0.itemHeadings,timestamp))::real,egoHeading)"),
    (facing_relative(o.trans@c.time, o.traj@c.time), 
        "facingRelative((headingAtTimestamp(t0.itemHeadings,timestamp))::real,(headingAtTimestamp(t0.itemHeadings,timestamp))::real)"),
    (facing_relative(o.trans@c.time, c.cam), 
        "facingRelative((headingAtTimestamp(t0.itemHeadings,timestamp))::real,cameraHeading)"),
])
def test_facing_relative(fn, sql):
    assert gen(fn) == sql
