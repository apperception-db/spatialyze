from ...predicate import GenSqlVisitor, PredicateNode, call_node
from .common import default_heading, default_location, is_location_type


@call_node
def road_direction(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    location = args[0]
    assert is_location_type(location), type(location)
    _location = default_location(location)

    heading = location if len(args) == 1 else args[1]
    heading = default_heading(heading)

    return (
        "ifnull((SELECT CAST(((s_inner.heading * 180 / PI()) + 360) AS numeric) % 360 "
        "FROM segment as s_inner "
        "WHERE elementId IN ("
        "   SELECT s_inner2.elementId "
        "   FROM SegmentPolygon AS s_inner2 "
        "   WHERE ST_Covers(s_inner2.elementPolygon, {point}) "
        "   AND (SELECT l.id FROM Lane AS l WHERE l.id = s_inner.elementId) IS NOT NULL"
        ") AND ROUND(CAST(s_inner.heading * 180 / PI() AS numeric), 3) != -45 "
        "ORDER BY st_distance(s_inner.segmentLine, {point}), s_inner.elementId ASC "
        "LIMIT 1), {heading}) "
    ).format(heading=visitor(heading), point=visitor(_location))
