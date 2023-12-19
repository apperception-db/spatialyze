from typing import TypeGuard

from ...predicate import (
    AtTimeNode,
    BinOpNode,
    CameraTableNode,
    CastNode,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
)

HEADINGS = {
    "trajCentroids": "itemHeadings",
    "translations": "itemHeadings",
    "egoTranslation": "egoHeading",
    "cameraTranslation": "cameraHeading",
}

ROAD_TYPES = {
    "road",
    "lane",
    "lanesection",
    "roadSection",
    "intersection",
    "roadsection",
    "lanewithrightlane",
}


def get_heading(arg: "PredicateNode"):
    if isinstance(arg, TableAttrNode) and arg.shorten:
        arg = getattr(arg.table, HEADINGS[arg.name])

    return arg


def get_heading_at_time(arg: "PredicateNode"):
    if isinstance(arg, BinOpNode) and arg.op == "matmul":
        return CastNode("real", get_heading_at_time(arg.left) @ arg.right)
    return get_heading(arg)


def default_location(obj: TableNode | TableAttrNode):
    assert isinstance(obj, (ObjectTableNode, CameraTableNode, TableAttrNode)), type(obj)
    if isinstance(obj, ObjectTableNode):
        return AtTimeNode(obj.traj)
    elif isinstance(obj, CameraTableNode):
        return obj.cam
    assert isinstance(obj.table, CameraTableNode), type(obj.table)
    assert obj.name in {"egoTranslation", "cameraTranslation"}, obj.name
    return obj


def default_heading(object: "PredicateNode"):
    assert isinstance(object, (ObjectTableNode, CameraTableNode, TableAttrNode)), type(object)
    if isinstance(object, ObjectTableNode):
        return AtTimeNode(object.heading)
    elif isinstance(object, CameraTableNode):
        return object.heading

    assert isinstance(object.table, CameraTableNode), type(object.table)
    assert object.name in {"egoTranslation", "cameraTranslation"}, object.name
    if object.name == "egoTranslation":
        return object.table.egoheading
    return object.table.heading


def is_location_type(p: PredicateNode) -> TypeGuard[TableNode | TableAttrNode]:
    return isinstance(p, TableNode) or (
        isinstance(p, TableAttrNode)
        and isinstance(p.table, CameraTableNode)
        and p.name in {"egoTranslation", "cameraTranslation"}
    )
