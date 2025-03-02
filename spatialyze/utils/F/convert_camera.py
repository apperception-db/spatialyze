from ...predicate import (
    CameraTableNode,
    GenSqlVisitor,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    call_node,
    camera,
)
from .common import default_heading, default_location


@call_node
def convert_camera(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    object, _camera, *_ = args
    assert isinstance(object, ObjectTableNode), object
    assert isinstance(_camera, (CameraTableNode, TableAttrNode)), _camera
    heading = default_heading(_camera)
    if isinstance(_camera, CameraTableNode) or (
        isinstance(_camera, TableAttrNode) and _camera.name == "cameraTranslation"
    ):
        heading = camera.heading
    else:
        assert isinstance(_camera, TableAttrNode), _camera
        assert _camera.name == "egoTranslation", _camera.name
        heading = camera.egoheading
    o, c, h = map(visitor, [default_location(object), default_location(_camera), heading])

    sx = f"(ST_X(ST_Centroid({o})) - ST_X(ST_Centroid({c})))"
    sy = f"(ST_Y(ST_Centroid({o})) - ST_Y(ST_Centroid({c})))"
    mag = f"(SQRT(POWER({sx}, 2) + POWER({sy}, 2)))"
    return f"ST_Point({mag} * COS(PI() * (-{h}) / 180 + ATAN2({sy}, {sx})), {mag} * SIN(PI() * (-{h}) / 180 + ATAN2({sy}, {sx})))"
