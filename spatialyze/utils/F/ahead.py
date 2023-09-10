from spatialyze.predicate import GenSqlVisitor, PredicateNode, call_node

from .common import default_heading, default_location


@call_node
def ahead(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    obj1, obj2 = args

    obj1 = default_location(obj1)
    obj2 = default_location(obj2)
    heading = default_heading(obj2)

    return f"ahead({','.join(map(visitor, [obj1, obj2, heading]))})"
