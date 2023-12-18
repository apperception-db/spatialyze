from ...predicate import GenSqlVisitor, PredicateNode, call_node
from .common import default_location


@call_node
def contained(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    object, region = args[:2]

    object = default_location(object)

    return f"contained({visitor(object)}, {visitor(region)})"
