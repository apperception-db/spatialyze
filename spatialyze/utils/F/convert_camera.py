from typing import List

from spatialyze.predicate import GenSqlVisitor, PredicateNode, call_node

from .common import default_heading, default_location


@call_node
def convert_camera(visitor: "GenSqlVisitor", args: "List[PredicateNode]"):
    object, camera = args[:2]

    object = default_location(object)
    camera = default_location(object)
    heading = default_heading(camera)

    return f"ConvertCamera({','.join(map(visitor, [object, camera, heading]))})"
