from ...predicate import GenSqlVisitor, PredicateNode, call_node
from .common import default_location, is_location_type
from .contains import ROAD_TYPES, _region_to_str

# min_distance = custom_fn("minDistance", 2)


@call_node
def min_distance(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    object, segment = args

    assert is_location_type(object), type(object)
    # assert is_location_type(pov), type(pov)
    region_str = _region_to_str(segment)

    if region_str.lower() not in ROAD_TYPES:
        raise Exception("polygon should be either " + " or ".join(sorted(ROAD_TYPES)))

    object = default_location(object)
    return f"""
    (
        SELECT MIN(ST_Distance({visitor(object)}, elementPolygon))
        FROM SegmentPolygon
        WHERE list_contains(segmentTypes, '{region_str.lower()}')
    )
    """
