from __future__ import annotations

from typing import List

from spatialyze.predicate import GenSqlVisitor, LiteralNode, PredicateNode, call_node

from .common import ROAD_TYPES


@call_node
def road_segment(visitor: "GenSqlVisitor", args: "List[PredicateNode]", kwargs: dict[str, PredicateNode]):
    assert kwargs is None or len(kwargs) == 0, kwargs
    table = args[0]
    assert (
        isinstance(table, LiteralNode)
        and isinstance(table.value, str)
        and table.value in ROAD_TYPES
    ), f"road_segment() takes a string as argument, received {table}"
    return f"roadSegment('{table.value}')"
