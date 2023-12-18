from ...predicate import ArrayNode, GenSqlVisitor, LiteralNode, PredicateNode, call_node
from .common import default_location, get_heading_at_time


@call_node
def heading_diff(
    visitor: "GenSqlVisitor", args: "list[PredicateNode]", named_args: "dict[str, PredicateNode]"
):
    object1, object2 = args

    object1 = default_location(object1)
    object2 = default_location(object2)

    angle_diff = (
        f"facingRelative({','.join(map(visitor, map(get_heading_at_time, [object1, object2])))})"
    )

    if "between" in named_args:
        func_name = "angleBetween"
        pair = named_args["between"]
    elif "excluding" in named_args:
        func_name = "angleExcluding"
        pair = named_args["excluding"]
    else:
        return angle_diff

    assert isinstance(pair, ArrayNode), type(pair)
    heading_from, heading_to = pair.exprs
    assert isinstance(heading_from, LiteralNode), type(heading_from)
    heading_from = heading_from.value
    assert isinstance(heading_to, LiteralNode), type(heading_to)
    heading_to = heading_to.value
    assert isinstance(heading_from, (int, float)), type(heading_from)
    assert isinstance(heading_to, (int, float)), type(heading_to)

    return f"{func_name}({angle_diff}, {heading_from}, {heading_to})"
