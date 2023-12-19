from typing import List

from spatialyze.predicate import (
    CameraTableNode,
    GenSqlVisitor,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    call_node,
    camera,
)

from .common import default_location, get_heading_at_time


@call_node
def convert_camera(visitor: "GenSqlVisitor", args: "List[PredicateNode]", kwargs: dict[str, PredicateNode]):
    assert kwargs is None or len(kwargs) == 0, kwargs
    object, _camera = args[:2]
    assert isinstance(object, ObjectTableNode), object
    assert isinstance(_camera, (CameraTableNode, TableAttrNode)), _camera
    heading = get_heading_at_time(_camera)
    if isinstance(_camera, CameraTableNode) or (
        isinstance(_camera, TableAttrNode) and _camera.name == "cameraTranslation"
    ):
        heading = camera.heading
    else:
        assert isinstance(_camera, TableAttrNode), _camera
        assert _camera.name == "egoTranslation", _camera.name
        heading = camera.egoheading

    return f"ConvertCamera({','.join(map(visitor, [default_location(object), default_location(_camera), heading]))})"
