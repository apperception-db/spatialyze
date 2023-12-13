from ...predicate import GenSqlVisitor, PredicateNode, call_node


@call_node
def left_turn(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    object = args[0]
    return f"leftTurn({visitor(object.translations)}, {visitor(object.itemHeadings)}, Cameras.frameNum, Cameras.cameraId)"
