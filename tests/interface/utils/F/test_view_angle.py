import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (view_angle(o, c), 
        "least(((((((-fmod(2 * PI() + PI()  / 2 - ATAN2((ST_Y(t0.translation) - ST_Y(c0.cameraTranslation)), (ST_X(t0.translation) - ST_X(c0.cameraTranslation))), "
        "2 * PI()) * 180 / PI())::numeric % 360) + 360) % 360) - (((c0.cameraHeading::numeric % 360) + 360) % 360) + 360)::numeric % 360), "
        "(((((c0.cameraHeading::numeric % 360) + 360) % 360) - ((((-fmod(2 * PI() + PI()  / 2 - ATAN2((ST_Y(t0.translation) - ST_Y(c0.cameraTranslation)), "
        "(ST_X(t0.translation) - ST_X(c0.cameraTranslation))), 2 * PI()) * 180 / PI())::numeric % 360) + 360) % 360) + 360)::numeric % 360))"),
    (view_angle(o, o), 
        "least(((((((-fmod(2 * PI() + PI()  / 2 - ATAN2((ST_Y(t0.translation) - ST_Y(t0.translation)), (ST_X(t0.translation) - ST_X(t0.translation))), "
        "2 * PI()) * 180 / PI())::numeric % 360) + 360) % 360) - (((t0.itemHeading::numeric % 360) + 360) % 360) + 360)::numeric % 360), "
        "(((((t0.itemHeading::numeric % 360) + 360) % 360) - ((((-fmod(2 * PI() + PI()  / 2 - ATAN2((ST_Y(t0.translation) - ST_Y(t0.translation)), "
        "(ST_X(t0.translation) - ST_X(t0.translation))), 2 * PI()) * 180 / PI())::numeric % 360) + 360) % 360) + 360)::numeric % 360))")
])
def test_view_angle(fn, sql):
    assert gen(fn) == sql
