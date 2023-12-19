from ...predicate import (
    ArrayNode,
    AtTimeNode,
    CameraTableNode,
    GenSqlVisitor,
    LiteralNode,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
    call_node,
    cast,
)


@call_node
def heading_diff(
    visitor: "GenSqlVisitor", args: "list[PredicateNode]", named_args: "dict[str, PredicateNode]"
):
    obj1, obj2 = args
    assert isinstance(obj1, (TableNode, TableAttrNode)), repr(obj1)
    assert isinstance(obj2, (TableNode, TableAttrNode)), repr(obj2)

    obj1 = default_heading(obj1)
    obj2 = default_heading(obj2)

    angle_diff = angle(obj1 - obj2)

    if len(named_args) == 0:
        return visitor(angle_diff)

    assert len(named_args) == 1, len(named_args)
    func = next(iter(named_args.keys()))
    pair = next(iter(named_args.values()))
    assert func in {"between", "excluding"}, func

    assert isinstance(pair, ArrayNode), repr(pair)
    pair = pair.exprs
    assert len(pair) == 2, len(pair)

    angle_from, angle_to = pair
    assert isinstance(angle_from, LiteralNode) and isinstance(angle_from.value, (int, float)), repr(
        angle_from
    )
    assert isinstance(angle_to, LiteralNode) and isinstance(angle_to.value, (int, float)), repr(
        angle_to
    )

    angle_from = ((angle_from.value % 360) + 360) % 360
    angle_to = ((angle_to.value % 360) + 360) % 360

    if (angle_from <= angle_to) == (func == "between"):
        pred = (angle_from < angle_diff) & (angle_diff < angle_to)
    else:
        pred = (angle_from > angle_diff) | (angle_diff > angle_to)

    return visitor(pred)


def angle(x: PredicateNode):
    return ((cast(x, "numeric") % 360) + 360) % 360


def default_heading(obj: TableNode | TableAttrNode):
    assert isinstance(obj, (ObjectTableNode, CameraTableNode, TableAttrNode)), repr(obj)
    if isinstance(obj, ObjectTableNode):
        return AtTimeNode(obj.heading)
    elif isinstance(obj, CameraTableNode):
        return obj.heading

    assert isinstance(obj.table, CameraTableNode), repr(obj.table)
    if obj.name == "egoTranslation":
        return obj.table.egoheading
    elif obj.name == "cameraTranslation":
        return obj.table.heading
    return obj
