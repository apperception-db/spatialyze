from ...predicate import GenSqlVisitor, ObjectTableNode, PredicateNode, call_node


@call_node
def left_turn(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    object = args[0]
    assert isinstance(object, ObjectTableNode)
    return f"leftTurn({visitor(object.translations)}, {visitor(object.itemHeadings)}, Cameras.frameNum, Cameras.cameraId)"
