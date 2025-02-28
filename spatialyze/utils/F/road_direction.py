from ...predicate import GenSqlVisitor, PredicateNode, call_node, cast
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

    # return f"roadDirection({','.join(map(visitor, [_location, cast(heading, 'real')]))})"
    return f"""
    (
    SELECT heading * 180 / PI()
    FROM Segment, {_location} AS point
    WHERE elementId IN (
        SELECT s.elementId
        FROM SegmentPolygon AS s
        WHERE St_Covers(s.elementPolygon, point)
        AND (SELECT id FROM Lane WHERE id = elementId) IS NOT NULL
    )
    AND ROUND(CAST(heading * 180 / PI() AS numeric), 3) != 45
    ORDER BY ST_Distance(SegmentLine, point) ASC LIMIT 1
    )
    """
