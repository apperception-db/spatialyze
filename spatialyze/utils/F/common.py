from typing import TypeGuard

from ...predicate import (
    AtTimeNode,
    CameraTableNode,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
)

ROAD_TYPES = {
    "road",
    "lane",
    "lanesection",
    "roadSection",
    "intersection",
    "roadsection",
    "lanewithrightlane",
}


def default_location(obj: TableNode | TableAttrNode):
    assert isinstance(obj, (ObjectTableNode, CameraTableNode, TableAttrNode)), type(obj)
    if isinstance(obj, ObjectTableNode):
        return AtTimeNode(obj.trans)
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
