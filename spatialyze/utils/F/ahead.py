from spatialyze.predicate import GenSqlVisitor, PredicateNode, call_node

from .common import default_heading, default_location, is_location_type


@call_node
def ahead(visitor: "GenSqlVisitor", args: "list[PredicateNode]"):
    obj1, obj2 = args
    print(obj1, obj2)

    assert is_location_type(obj1), type(obj1)
    assert is_location_type(obj2), type(obj2)

    _obj1 = default_location(obj1)
    _obj2 = default_location(obj2)
    heading = default_heading(obj2)

    return f"ahead({','.join(map(visitor, [_obj1, _obj2, heading]))})"
