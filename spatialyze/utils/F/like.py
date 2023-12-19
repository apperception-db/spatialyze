from typing import List

from spatialyze.predicate import GenSqlVisitor, PredicateNode, call_node


@call_node
def like(visitor: "GenSqlVisitor", args: "List[PredicateNode]", kwargs: dict[str, PredicateNode]) -> str:
    assert kwargs is None or len(kwargs) == 0, kwargs
    if len(args) != 2:
        raise Exception("like accepts 2 arguments")
    return " LIKE ".join(map(visitor, args))
