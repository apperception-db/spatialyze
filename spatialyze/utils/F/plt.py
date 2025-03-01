from ...predicate import GenSqlVisitor, LiteralNode, PredicateNode, call_node


@call_node
def plt(
    visitor: GenSqlVisitor,
    args: list[PredicateNode],
    kwargs: dict[str, PredicateNode],
):
    assert kwargs is None or len(kwargs) == 0, kwargs
    p1, p2 = args
    if isinstance(p1, LiteralNode):
        p1 = p1.value
        assert isinstance(p1, str), type(p1)
        p1 = f"ST_GeomFromText('{p1}')"
    else:
        p1 = visitor(p1)
    if isinstance(p2, LiteralNode):
        p2 = p2.value
        assert isinstance(p2, str), type(p2)
        p2 = f"ST_GeomFromText('{p2}')"
    else:
        p2 = visitor(p2)
    x1, x2 = f"ST_X({p1})", f"ST_X({p2})"
    y1, y2 = f"ST_Y({p1})", f"ST_Y({p2})"

    return f"(({x1} < {x2}) AND ({y1} < {y2}))"
