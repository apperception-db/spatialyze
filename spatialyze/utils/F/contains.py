from ...predicate import ArrayNode, GenSqlVisitor, LiteralNode, PredicateNode, TableNode, call_node
from .common import default_location as dl


ROAD_TYPES = {"road", "lane", "lanesection", "roadsection", "intersection"}


@call_node
def contains(visitor: GenSqlVisitor, args: list[PredicateNode]):
    region, points = args
    if not isinstance(region, LiteralNode):
        raise Exception(
            "Frist argument of contains_all should "
            "be a constant, recieved " + str(region)
        )

    assert isinstance(region.value, str), region.value
    region_str = region.value

    if region_str.lower() not in ROAD_TYPES:
        raise Exception(
            "polygon should be either "
            " or ".join(sorted(ROAD_TYPES))
        )

    if not isinstance(points, ArrayNode):
        points = ArrayNode([points])
    points = points.exprs
    assert all(isinstance(p, TableNode) for p in points), [*map(type, points)]
    points = [p for p in points if isinstance(p, TableNode)]

    def cover(p: TableNode):
        return f"ST_Covers(SegmentPolygon.elementPolygon, {visitor(dl(p))})"

    return (
        "(EXISTS(SELECT 1 FROM SegmentPolygon WHERE "
        f"    SegmentPolygon.__RoadType__{region_str}__ AND\n"
        f"    {' AND '.join(map(cover, points))}\n"
        "))"
    )
