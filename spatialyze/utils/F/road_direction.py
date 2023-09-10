from typing import List

from spatialyze.predicate import GenSqlVisitor, PredicateNode, call_node

from .common import default_location, get_heading_at_time


@call_node
def road_direction(visitor: "GenSqlVisitor", args: "List[PredicateNode]"):
    location = args[0]
    location = default_location(location)
    heading = get_heading_at_time(location if len(args) == 1 else args[1])

    return f"roadDirection({','.join(map(visitor, [location, heading]))})"
