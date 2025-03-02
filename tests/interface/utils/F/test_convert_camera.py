import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (convert_camera(o, c.ego),
        "ST_Point((SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.egoTranslation))), 2) + POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), 2))) * COS(PI() * (-c0.egoHeading) / 180 + ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), (ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.egoTranslation))))), (SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.egoTranslation))), 2) + POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), 2))) * SIN(PI() * (-c0.egoHeading) / 180 + ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), (ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.egoTranslation))))))"),
    (convert_camera(o, c),
        "ST_Point((SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.cameraTranslation))), 2) + POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), 2))) * COS(PI() * (-c0.cameraHeading) / 180 + ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), (ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.cameraTranslation))))), (SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.cameraTranslation))), 2) + POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), 2))) * SIN(PI() * (-c0.cameraHeading) / 180 + ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), (ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.cameraTranslation))))))"),
    # (convert_camera(o, o),
    #     "ConvertCamera(t0.translation,t0.translations,timestamp),t0.itemHeading)"),
])
def test_convert_camera(fn, sql):
    assert gen(fn) == sql