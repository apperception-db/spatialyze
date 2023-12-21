from ...predicate import (
    ArrayNode,
    CallNode,
    CameraTableNode,
    GenSqlVisitor,
    LiteralNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
    call_node,
)
from .common import default_location as dl
from .common import is_location_type

ROAD_TYPES = {"road", "lane", "lanesection", "roadsection", "intersection"}


@call_node
def contains(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    region, points = args

    region_str = _region_to_str(region)

    if region_str.lower() not in ROAD_TYPES:
        raise Exception("polygon should be either " + " or ".join(sorted(ROAD_TYPES)))

    if not isinstance(points, ArrayNode):
        points = ArrayNode([points])
    points = points.exprs
    assert all(map(is_location_type, points)), [*map(lambda p: p.__class__.__name__, points)]
    points = [*filter(is_location_type, points)]

    def cover(p: TableNode | TableAttrNode):
        if isinstance(p, TableNode):
            return f"ST_Covers(SegmentPolygon.elementPolygon, {visitor(dl(p))})"
        assert isinstance(p.table, CameraTableNode), type(p.table)
        assert p.name in {"egoTranslation", "cameraTranslation"}, p.name
        return f"ST_Covers(SegmentPolygon.elementPolygon, {visitor(p)})"

    return (
        f"(EXISTS(SELECT 1 FROM SegmentPolygon WHERE SegmentPolygon.__RoadType__{region_str}__ AND\n"
        f"    {' AND '.join(map(cover, points))}\n"
        "))"
    )


def _region_to_str(region: PredicateNode) -> str:
    if isinstance(region, CallNode):
        (arg,) = region.params
        assert isinstance(arg, LiteralNode)
        region = arg

    if not isinstance(region, LiteralNode):
        raise Exception("Frist argument of contains should be a constant, recieved " + str(region))

    assert isinstance(region.value, str), region.value
    return region.value
