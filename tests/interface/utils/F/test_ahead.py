import pytest
from common import *


o = objects[0]
c = camera


@pytest.mark.parametrize("fn, sql", [
    (ahead(o, c.ego), 
        "ahead(t0.translation,c0.egoTranslation,(c0.egoHeading)::real)"),
    (ahead(o, c.cam), 
        "ahead(t0.translation,c0.cameraTranslation,(c0.cameraHeading)::real)"),
    (ahead(o, o), 
        "ahead(t0.translation,t0.translation,(t0.itemHeading)::real)"),
])
def test_ahead(fn, sql):
    assert gen(fn) == sql
