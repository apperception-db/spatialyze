from ...predicate import GenSqlVisitor, LiteralNode, PredicateNode, call_node
from .common import ROAD_TYPES
from .common import default_location as dl
from .common import is_location_type


@call_node
def same_region(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    type_, traj1, traj2 = args
    if not isinstance(type_, LiteralNode) or type_.value.lower() not in ROAD_TYPES:
        raise Exception(f"Unsupported road type: {type_}")

    assert is_location_type(traj1), type(traj1)
    assert is_location_type(traj2), type(traj2)
    return f"sameRegion({','.join(map(visitor, [type_, dl(traj1), dl(traj2)]))})"
