from ...predicate import (
    GenSqlVisitor,
    ObjectTableNode,
    PredicateNode,
    call_node,
    camera,
)


@call_node
def left_turn(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    object = args[0]
    return f"leftTurn({visitor(object.itemHeadings)}, Cameras.frameNum, Cameras.cameraId)"
