from ...predicate import (
    CallNode,
    GenSqlVisitor,
    LiteralNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
    call_node,
)
from .common import default_location as dl


@call_node
def contained_margin(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    point, geom, margin = args
    assert isinstance(point, (TableAttrNode, TableNode)), point.__class__.__name__
    assert isinstance(geom, CallNode) and geom.name == "road_segment", geom.__class__.__name__
    assert isinstance(margin, LiteralNode) and isinstance(
        margin.value, (int, float)
    ), margin.__class__.__name__

    point = dl(point)
    return f"containedMargin({','.join(map(visitor, [point, geom, margin]))})"
