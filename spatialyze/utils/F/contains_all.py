from __future__ import annotations

from typing import List

from spatialyze.predicate import (
    ArrayNode,
    GenSqlVisitor,
    LiteralNode,
    PredicateNode,
    call_node,
)

ROAD_TYPES = {"road", "lane", "lanesection", "roadsection", "intersection"}


@call_node
def contains_all(visitor: "GenSqlVisitor", args: "List[PredicateNode]"):
    polygon, points = args
    if not isinstance(polygon, LiteralNode):
        raise Exception(
            "Frist argument of contains_all should be a constant, recieved " + str(polygon)
        )

    polygon_ = visitor(polygon)[1:-1]

    if polygon_.lower() not in ROAD_TYPES:
        raise Exception("polygon should be either " + " or ".join(sorted(ROAD_TYPES)))

    assert isinstance(points, ArrayNode), type(points)
    return f"""(EXISTS(SELECT 1
        FROM SegmentPolygon
        WHERE
            SegmentPolygon.__RoadType__{polygon_}__ AND
            {" AND ".join(f"ST_Covers(SegmentPolygon.elementPolygon, {visitor(point)})" for point in points.exprs)}
    ))"""
