from ...predicate import (
    GenSqlVisitor,
    ObjectTableNode,
    PredicateNode,
    call_node,
    camera,
)


@call_node
def contained(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    object, region = args[:2]
    if isinstance(object, ObjectTableNode):
        object = object.traj @ camera.time
    return f"contained({visitor(object)}, {visitor(region)})"
