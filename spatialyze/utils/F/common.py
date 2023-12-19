from ...predicate import (
    BinOpNode,
    CameraTableNode,
    CastNode,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
    camera,
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


def default_location(obj: TableNode):
    assert isinstance(obj, (ObjectTableNode, CameraTableNode)), type(obj)
    if isinstance(obj, ObjectTableNode):
        return obj.trans @ camera.time
    return obj.cam


def default_heading(object: "PredicateNode"):
    if isinstance(object, ObjectTableNode):
        object = object.traj @ camera.time
    elif isinstance(object, CameraTableNode):
        object = object.cam

    return get_heading_at_time(object)
