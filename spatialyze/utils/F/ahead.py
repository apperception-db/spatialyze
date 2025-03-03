from ...predicate import AtTimeNode, GenSqlVisitor, PredicateNode, call_node, cast
from .common import default_heading, default_location, is_location_type
from .convert_camera import convert_camera


@call_node
def ahead(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    obj1, obj2 = args

    assert is_location_type(obj1), type(obj1)
    assert is_location_type(obj2), type(obj2)

    _obj1 = default_location(obj1)
    _obj2 = default_location(obj2)
    heading = default_heading(obj2)

    o1 = visitor(_obj1)
    o2 = visitor(_obj2)
    h = visitor(cast(heading, "real"))
    if isinstance(_obj1, AtTimeNode):
        _obj1 = _obj1.attr
    if isinstance(_obj2, AtTimeNode):
        _obj2 = _obj2.attr
    cc = visitor(convert_camera(obj1, obj2, heading))
    return (
        f"((ST_X({o1}) - ST_X({o2})) * COS(PI() * (({h}) + 90) / 180) + "
        f"(ST_Y({o1}) - ST_Y({o2})) * SIN(PI() * (({h}) + 90) / 180) > 0 "
        f"AND ABS(ST_X({cc})) < 3)"
    )
