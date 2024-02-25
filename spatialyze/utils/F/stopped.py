from ...predicate import (
    GenSqlVisitor,
    LiteralNode,
    ObjectTableNode,
    PredicateNode,
    call_node,
    lit,
)
from .common import default_location as dl


@call_node
def stopped(visitor: GenSqlVisitor, args: list[PredicateNode], kwargs: dict[str, PredicateNode]):
    kwargs = kwargs or {}
    assert kwargs.keys() <= {"distance", "duration"}, kwargs

    (point,) = args
    distance = kwargs.get("distance", lit(5))
    duration = kwargs.get("duration", lit(5))

    assert isinstance(distance, LiteralNode) and isinstance(distance.value, (float, int)), distance
    assert isinstance(duration, LiteralNode) and isinstance(duration.value, (float, int)), duration

    distance = distance.value
    duration = duration.value

    # TODO: support camera stop
    assert isinstance(point, ObjectTableNode), point
    point1 = dl(point)

    nextPoint = f"(SELECT translation FROM Item_Trajectory2 WHERE itemId = {visitor(point.id)} AND {visitor(point.frameNum)} + ROUND({duration} * (SELECT fps FROM Spatialyze_Metadata)) = frameNum)"
    return f"(EXIT {nextPoint} AND ST_Distance({visitor(point1)},{nextPoint})<{distance})"
