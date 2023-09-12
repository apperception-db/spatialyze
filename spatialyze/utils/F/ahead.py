from spatialyze.predicate import (
    BinOpNode,
    GenSqlVisitor,
    PredicateNode,
    TableAttrNode,
    call_node,
)

from .common import get_heading_at_time


@call_node
def ahead(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    obj1, obj2 = args

    if not isinstance(obj2, TableAttrNode) and (
        not isinstance(obj2, BinOpNode) or obj2.op != "matmul"
    ):
        raise Exception("we dont support other location yet")

    heading = get_heading_at_time(obj2)
    return f"ahead({','.join(map(visitor, [obj1, obj2, heading]))})"
