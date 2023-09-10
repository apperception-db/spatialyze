from __future__ import annotations

from typing import List

from spatialyze.predicate import GenSqlVisitor, PredicateNode, call_node

from .common import default_heading, default_location


@call_node
def view_angle(visitor: "GenSqlVisitor", args: "List[PredicateNode]"):
    object, pov = args

    object = default_location(object)
    pov = default_location(pov)

    heading = default_heading(pov)

    return f"viewAngle({','.join(map(visitor, [object, heading, pov]))})"
