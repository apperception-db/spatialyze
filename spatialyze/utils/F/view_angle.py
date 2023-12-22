from ...predicate import GenSqlVisitor, PredicateNode, call_node
from .common import default_heading, default_location, is_location_type


@call_node
def view_angle(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    object, pov = args

    assert is_location_type(object), type(object)
    assert is_location_type(pov), type(pov)

    object = default_location(object)
    _pov = default_location(pov)
    heading = default_heading(pov)

    return f"viewAngle({','.join(map(visitor, [object, heading, _pov]))})"
