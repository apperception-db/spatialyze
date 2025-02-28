from ...predicate import GenSqlVisitor, PredicateNode, call_node, cast
from .common import default_heading, default_location, is_location_type


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
    return f"""
    ((ST_X({o1}) - ST_X({o2})) * COS(PI() * ({h} + 90) / 180) + (ST_Y({o1}) - ST_Y({o2})) * SIN(PI() * ({h} + 90) / 180) > 0
        AND ABS(ST_X(convertCamera({o1}, {o2}, {h}))) < 3)
    """
