from ...predicate import ArrayNode, GenSqlVisitor, LiteralNode, ObjectTableNode, PredicateNode, call_node


@call_node
def has_types(visitor: GenSqlVisitor, args: list[PredicateNode]):
    obj, *types = args

    assert isinstance(obj, ObjectTableNode), repr(obj)
    assert len(types) > 0

    if len(types) == 1:
        t = types[0]
        if isinstance(t, ArrayNode):
            types = t.exprs
    
    assert all(isinstance(t, LiteralNode) and isinstance(t.value, str) for t in types), [*map(repr, types)]
    types = [t.value for t in types if isinstance(t, LiteralNode) and isinstance(t.value, str)]

    def has_type(type: str):
        return f"({visitor(obj.type)} = '{type}')"

    return f"({' OR '.join(map(has_type, types))})"

