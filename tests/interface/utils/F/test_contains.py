import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (contains('lane', o),
        "(EXISTS(SELECT 1 FROM SegmentPolygon WHERE SegmentPolygon.__RoadType__lane__ AND\n"
        "    ST_Covers(SegmentPolygon.elementPolygon, valueAtTimestamp(t0.translations,c0.timestamp))\n"
        "))"),
    (contains(road_segment('lane'), o),
        "(EXISTS(SELECT 1 FROM SegmentPolygon WHERE SegmentPolygon.__RoadType__lane__ AND\n"
        "    ST_Covers(SegmentPolygon.elementPolygon, valueAtTimestamp(t0.translations,c0.timestamp))\n"
        "))"),
    (contains('lane', [o, o1, o2]),
        "(EXISTS(SELECT 1 FROM SegmentPolygon WHERE SegmentPolygon.__RoadType__lane__ AND\n"
        "    ST_Covers(SegmentPolygon.elementPolygon, valueAtTimestamp(t0.translations,c0.timestamp)) AND "
            "ST_Covers(SegmentPolygon.elementPolygon, valueAtTimestamp(t1.translations,c0.timestamp)) AND "
            "ST_Covers(SegmentPolygon.elementPolygon, valueAtTimestamp(t2.translations,c0.timestamp))\n"
        "))"),
    (contains('lane', [c, c.cam, c.ego]),
        "(EXISTS(SELECT 1 FROM SegmentPolygon WHERE SegmentPolygon.__RoadType__lane__ AND\n"
        "    ST_Covers(SegmentPolygon.elementPolygon, c0.cameraTranslation) AND "
            "ST_Covers(SegmentPolygon.elementPolygon, c0.cameraTranslation) AND "
            "ST_Covers(SegmentPolygon.elementPolygon, c0.egoTranslation)\n"
        "))"),
])
def test_contains(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (contains(o, o), 
        "Frist argument of contains should be a constant, recieved ObjectTableNode[0]"),
    (contains(1, o), 
        "1"),
    (contains('invalid', o), 
        "polygon should be either intersection or lane or lanesection or road or roadsection"),
    (contains('road', [o, o.heading]), 
        "['ObjectTableNode', 'TableAttrNode']"),
    (contains('road', [o, c.time]), 
        "['ObjectTableNode', 'TableAttrNode']"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
