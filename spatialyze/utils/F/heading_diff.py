from ...predicate import GenSqlVisitor, PredicateNode, call_node
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
        heading_from, heading_to = named_args["between"]
        func_name = "angleBetween"
    elif "excluding" in named_args:
        heading_from, heading_to = named_args["excluding"]
        func_name = "angleExcluding"
    else:
        return angle_diff

    return f"{func_name}({angle_diff}, {heading_from}, {heading_to})"

    return "a"
    # return f"contained({visitor(object)},{visitor(region)})"
