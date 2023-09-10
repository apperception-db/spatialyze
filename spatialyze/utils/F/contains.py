from ...predicate import GenSqlVisitor, PredicateNode, call_node
from .common import default_location


@call_node
def contains(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    region, object = args
    object = default_location(object)

    return f"contained({visitor(object)},{visitor(region)})"
