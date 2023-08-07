import pytest
from common import *


@pytest.mark.parametrize("fn, sql", [
    (
        contains_all('intersection', [o.trans, 2] @ c.time),
        """(EXISTS(SELECT 1
            FROM intersection
                JOIN SegmentPolygon
                    ON SegmentPolygon.elementId = intersection.id
                JOIN unnest(valueAtTimestamp(ARRAY[t0.translations,2],timestamp)) point
                    ON ST_Covers(SegmentPolygon.elementPolygon, point)
            GROUP BY intersection.id
            HAVING COUNT(point) = cardinality(valueAtTimestamp(ARRAY[t0.translations,2],timestamp))
        ))"""
    ),
    (
        contains_all('intersection', c.time),
        """(EXISTS(SELECT 1
            FROM intersection
                JOIN SegmentPolygon
                    ON SegmentPolygon.elementId = intersection.id
                JOIN unnest(timestamp) point
                    ON ST_Covers(SegmentPolygon.elementPolygon, point)
            GROUP BY intersection.id
            HAVING COUNT(point) = cardinality(timestamp)
        ))"""
    ),
    (
        contains_all('intersection', [c.time, o.trans]),
        """(EXISTS(SELECT 1
            FROM SegmentPolygon
            WHERE
                SegmentPolygon.__RoadType__intersection__ AND
                ST_Covers(SegmentPolygon.elementPolygon, timestamp) AND ST_Covers(SegmentPolygon.elementPolygon, t0.translations)
        ))"""
    )
])
def test_contain_all(fn, sql):
    assert gen(fn) == sql


@pytest.mark.parametrize("fn, msg", [
    (contains_all(c.time, 1), 
        "Frist argument of contains_all should be a constant, recieved TableAttrNode(name='timestamp', table=CameraTableNode, shorten=True)"),
    (contains_all('invalid', 1), 
        "polygon should be either intersection or lane or lanesection or road or roadsection"),
])
def test_exception(fn, msg):
    with pytest.raises(Exception) as e_info:
        gen(fn)
    assert str(e_info.value) == msg
