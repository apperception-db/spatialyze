from ...predicate import GenSqlVisitor, PredicateNode, call_node, cast
from .common import default_heading, default_location, is_location_type


@call_node
def road_direction(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    location = args[0]
    assert is_location_type(location), type(location)
    _location = default_location(location)

    heading = location if len(args) == 1 else args[1]
    heading = default_heading(heading)

    return f"roadDirection({','.join(map(visitor, [_location, cast(heading, 'real')]))})"
