from ...predicate import GenSqlVisitor, PredicateNode, call_node
from .common import default_heading, default_location, is_location_type


@call_node
def view_angle(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    object, pov = args

    assert is_location_type(object), type(object)
    assert is_location_type(pov), type(pov)

    object = default_location(object)
    _pov = default_location(pov)
    heading = default_heading(pov)

    o = visitor(object)
    p = visitor(_pov)
    h = visitor(heading)

    view_point_heading = f"((({h}::numeric % 360) + 360) % 360)"
    x1, y1 = f"ST_X({p})", f"ST_Y({p})"
    x2, y2 = f"ST_X({o})", f"ST_Y({o})"
    a = f"fmod(2 * PI() + PI()  / 2 - ATAN2(({y2} - {y1}), ({x2} - {x1})), 2 * PI())"
    azimuth = f"((((-{a} * 180 / PI())::numeric % 360) + 360) % 360)"
    clockwise = f"(({azimuth} - {view_point_heading} + 360)::numeric % 360)"
    counterClockwise = f"(({view_point_heading} - {azimuth} + 360)::numeric % 360)"
    return f"least({clockwise}, {counterClockwise})"
