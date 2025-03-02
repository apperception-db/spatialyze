import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (road_direction(o), 
        "ifnull((SELECT CAST(((s_inner.heading * 180 / PI()) + 360) AS numeric) % 360 FROM segment as s_inner WHERE elementId IN (   "
        "SELECT s_inner2.elementId    FROM SegmentPolygon AS s_inner2    WHERE ST_Covers(s_inner2.elementPolygon, t0.translation)    "
        "AND (SELECT l.id FROM Lane AS l WHERE l.id = s_inner.elementId) IS NOT NULL) AND ROUND(CAST(s_inner.heading * 180 / PI() AS "
        "numeric), 3) != -45 ORDER BY st_distance(s_inner.segmentLine, t0.translation), s_inner.elementId ASC LIMIT 1), t0.itemHeading) "),
    (road_direction(o, c.ego), 
        "ifnull((SELECT CAST(((s_inner.heading * 180 / PI()) + 360) AS numeric) % 360 FROM segment as s_inner WHERE elementId IN (   "
        "SELECT s_inner2.elementId    FROM SegmentPolygon AS s_inner2    WHERE ST_Covers(s_inner2.elementPolygon, t0.translation)    "
        "AND (SELECT l.id FROM Lane AS l WHERE l.id = s_inner.elementId) IS NOT NULL) AND ROUND(CAST(s_inner.heading * 180 / PI() AS "
        "numeric), 3) != -45 ORDER BY st_distance(s_inner.segmentLine, t0.translation), s_inner.elementId ASC LIMIT 1), c0.egoHeading) "),
    (road_direction(c), 
        "ifnull((SELECT CAST(((s_inner.heading * 180 / PI()) + 360) AS numeric) % 360 FROM segment as s_inner WHERE elementId IN (   "
        "SELECT s_inner2.elementId    FROM SegmentPolygon AS s_inner2    WHERE ST_Covers(s_inner2.elementPolygon, c0.cameraTranslation)    "
        "AND (SELECT l.id FROM Lane AS l WHERE l.id = s_inner.elementId) IS NOT NULL) AND ROUND(CAST(s_inner.heading * 180 / PI() AS numeric), 3) != -45 "
        "ORDER BY st_distance(s_inner.segmentLine, c0.cameraTranslation), s_inner.elementId ASC LIMIT 1), c0.cameraHeading) "),
    (road_direction(c.ego, o), 
        "ifnull((SELECT CAST(((s_inner.heading * 180 / PI()) + 360) AS numeric) % 360 FROM segment as s_inner WHERE elementId IN (   "
        "SELECT s_inner2.elementId    FROM SegmentPolygon AS s_inner2    WHERE ST_Covers(s_inner2.elementPolygon, c0.egoTranslation)    "
        "AND (SELECT l.id FROM Lane AS l WHERE l.id = s_inner.elementId) IS NOT NULL) AND ROUND(CAST(s_inner.heading * 180 / PI() AS numeric), 3) != -45 "
        "ORDER BY st_distance(s_inner.segmentLine, c0.egoTranslation), s_inner.elementId ASC LIMIT 1), t0.itemHeading) "),
])
def test_road_direction(fn, sql):
    assert gen(fn) == sql


