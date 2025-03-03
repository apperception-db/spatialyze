import pytest
from common import *


o = objects[0]
c = camera


@pytest.mark.parametrize("fn, sql", [
    (ahead(o, c.ego), 
        "((ST_X(t0.translation) - ST_X(c0.egoTranslation)) * COS(PI() * (((c0.egoHeading)::real) + 90) / 180) + "
        "(ST_Y(t0.translation) - ST_Y(c0.egoTranslation)) * SIN(PI() * (((c0.egoHeading)::real) + 90) / 180) > 0 AND "
        "ABS(ST_X(ST_Point((SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.egoTranslation))), 2) + "
        "POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), 2))) * COS(PI() * (-c0.egoHeading) / 180 + "
        "ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), (ST_X(ST_Centroid(t0.translation)) - "
        "ST_X(ST_Centroid(c0.egoTranslation))))), (SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.egoTranslation))), 2) + "
        "POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), 2))) * SIN(PI() * (-c0.egoHeading) / 180 + "
        "ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.egoTranslation))), (ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.egoTranslation)))))))) < 3)"),
    (ahead(o, c.cam), 
        "((ST_X(t0.translation) - ST_X(c0.cameraTranslation)) * COS(PI() * (((c0.cameraHeading)::real) + 90) / 180) + "
        "(ST_Y(t0.translation) - ST_Y(c0.cameraTranslation)) * SIN(PI() * (((c0.cameraHeading)::real) + 90) / 180) > 0 AND "
        "ABS(ST_X(ST_Point((SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.cameraTranslation))), 2) + "
        "POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), 2))) * COS(PI() * (-c0.cameraHeading) / 180 + "
        "ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), (ST_X(ST_Centroid(t0.translation)) - "
        "ST_X(ST_Centroid(c0.cameraTranslation))))), (SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.cameraTranslation))), 2) + "
        "POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), 2))) * SIN(PI() * (-c0.cameraHeading) / 180 + "
        "ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(c0.cameraTranslation))), (ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(c0.cameraTranslation)))))))) < 3)"),
    (ahead(o, o), 
        "((ST_X(t0.translation) - ST_X(t0.translation)) * COS(PI() * (((t0.itemHeading)::real) + 90) / 180) + "
        "(ST_Y(t0.translation) - ST_Y(t0.translation)) * SIN(PI() * (((t0.itemHeading)::real) + 90) / 180) > 0 AND "
        "ABS(ST_X(ST_Point((SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(t0.translation))), 2) + "
        "POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(t0.translation))), 2))) * COS(PI() * (-t0.itemHeading) / 180 + "
        "ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(t0.translation))), (ST_X(ST_Centroid(t0.translation)) - "
        "ST_X(ST_Centroid(t0.translation))))), (SQRT(POWER((ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(t0.translation))), 2) + "
        "POWER((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(t0.translation))), 2))) * SIN(PI() * (-t0.itemHeading) / 180 + "
        "ATAN2((ST_Y(ST_Centroid(t0.translation)) - ST_Y(ST_Centroid(t0.translation))), (ST_X(ST_Centroid(t0.translation)) - ST_X(ST_Centroid(t0.translation)))))))) < 3)"),
])
def test_ahead(fn, sql):
    assert gen(fn) == sql
