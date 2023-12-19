from ...predicate import (
    ArrayNode,
    CameraTableNode,
    GenSqlVisitor,
    LiteralNode,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
    call_node,
    lit,
    camera
)
from .common import default_location as dl
from .common import is_location_type

ROAD_TYPES = {"road", "lane", "lanesection", "roadsection", "intersection"}


@call_node
def stopped(visitor: GenSqlVisitor, args: list[PredicateNode], kwargs: dict[str, PredicateNode]):
    kwargs = kwargs or {}
    assert kwargs.keys() <= {"distance", "duration"}, kwargs

    (point,) = args
    distance = kwargs.get("distance", lit(5))
    duration = kwargs.get("duration", lit(5))

    assert isinstance(point, ObjectTableNode), point
    assert isinstance(distance, LiteralNode) and isinstance(distance.value, (float, int)), distance
    assert isinstance(duration, LiteralNode) and isinstance(duration.value, (float, int)), duration

    distance = distance.value
    duration = duration.value

    point1 = dl(point)

    return f"(ST_Distance({visitor(point1)},valueAtTimestamp({visitor(point.traj)},{visitor(camera.time)}+interval '{duration} secs'))<{distance})"
