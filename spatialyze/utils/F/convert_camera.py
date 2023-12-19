from typing import List

from spatialyze.predicate import CameraTableNode, GenSqlVisitor, PredicateNode, TableAttrNode, call_node, camera

from .common import get_heading_at_time


@call_node
def convert_camera(visitor: "GenSqlVisitor", args: "List[PredicateNode]"):
    object, _camera = args[:2]
    heading = get_heading_at_time(_camera)
    if isinstance(_camera, CameraTableNode) or (isinstance(_camera, TableAttrNode) and _camera.name == "cameraTranslation"):
        heading = camera.heading
    else:
        assert isinstance(_camera, TableAttrNode), _camera
        assert _camera.name == "egoTranslation", _camera.name
        heading = camera.egoheading

    return f"ConvertCamera({','.join(map(visitor, [object, _camera, heading]))})"