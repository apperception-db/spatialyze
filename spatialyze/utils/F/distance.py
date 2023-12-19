from ...utils.F.common import default_location as dl
from ...predicate import GenSqlVisitor, TableNode, PredicateNode, call_node


@call_node
def distance(visitor: GenSqlVisitor, args: list[PredicateNode]):
    assert len(args) == 2, len(args)
    object1, object2 = args
    assert isinstance(object1, TableNode), type(object1)
    assert isinstance(object2, TableNode), type(object2)
    return (f"ST_Distance({visitor(dl(object1))},{visitor(dl(object2))})")
