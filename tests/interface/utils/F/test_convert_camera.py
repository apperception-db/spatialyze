import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (convert_camera(o, c.ego),
        "ConvertCamera(t0.translation,c0.egoTranslation,c0.egoHeading)"),
    (convert_camera(o, c),
        "ConvertCamera(t0.translation,c0.cameraTranslation,c0.cameraHeading)"),
    # (convert_camera(o, o),
    #     "ConvertCamera(t0.translation,t0.translations,timestamp),t0.itemHeading)"),
])
def test_convert_camera(fn, sql):
    assert gen(fn) == sql