import torch

from spatialyze.predicate import (
    ArrayNode,
    BinOpNode,
    BoolOpNode,
    CallNode,
    CameraTableNode,
    CastNode,
    CompOpNode,
    LiteralNode,
    ObjectTableNode,
    PredicateNode,
    TableAttrNode,
    TableNode,
    UnaryOpNode,
    Visitor,
)

from ...payload import Payload
from .detection_2d import Detection2D, Metadatum


class ObjectTypeFilter(Detection2D):
    def __init__(self, types: "list[str] | None" = None, predicate: "PredicateNode | None" = None):
        if types is None:
            assert predicate is not None, "Can only except either types or predicate"
            self.types = list(FindType()(predicate))
        else:
            assert types is not None, "Can only except either types or predicate"
            self.types = types

    def __repr__(self) -> str:
        return f"ObjectTypeFilter(types={self.types})"

    def add_type(self, type: "str"):
        self.types.append(type)

    def _run(self, payload: "Payload"):
        detection_2d = Detection2D.get(payload)
        assert detection_2d is not None

        assert len(detection_2d) != 0
        _, class_mapping, _ = detection_2d[0]
        if isinstance(class_mapping, dict):
            # TODO: class_mapping should not be a dict
            class_mapping = list(class_mapping.values())
        assert isinstance(class_mapping, list)
        type_indices_to_keep: "set[int]" = set()

        for t in self.types:
            idx = class_mapping.index(t)
            type_indices_to_keep.add(idx)

        metadata = []
        for keep, (det, _, ids) in zip(payload.keep, detection_2d):
            if not keep:
                metadata.append(Metadatum(torch.Tensor([]), class_mapping, []))
                continue

            det_to_keep: "list[int]" = []
            if len(det) > 0:
                type_indices = det[:, 5]
                type_indices_list: "list[float]" = type_indices.tolist()
                for i, type_index in enumerate(type_indices_list):
                    assert isinstance(type_index, float)
                    assert type_index.is_integer()
                    if type_index in type_indices_to_keep:
                        det_to_keep.append(i)

            metadata.append(
                Metadatum(det[det_to_keep], class_mapping, [ids[k] for k in det_to_keep])
            )
        return None, {ObjectTypeFilter.classname(): metadata}


class FindType(Visitor["set[str]"]):
    def __init__(self) -> None:
        super().__init__()
        self.types = set()

    def visit_ArrayNode(self, node: "ArrayNode") -> "set[str]":
        types = set()
        for e in node.exprs:
            types.update(self(e))
        return types

    def visit_CompOpNode(self, node: "CompOpNode") -> "set[str]":
        left, right = node.left, node.right
        if isinstance(left, TableAttrNode) and left.name == "objectType":
            if isinstance(right, LiteralNode):
                return set([right.value])
        if isinstance(right, TableAttrNode) and right.name == "objectType":
            if isinstance(left, LiteralNode):
                return set([left.value])

        types = set()
        types.update(self(node.left))
        types.update(self(node.right))
        return types

    def visit_BinOpNode(self, node: "BinOpNode") -> "set[str]":
        types = set()
        types.update(self(node.left))
        types.update(self(node.right))
        return types

    def visit_BoolOpNode(self, node: "BoolOpNode") -> "set[str]":
        types = set()
        for e in node.exprs:
            types.update(self(e))
        return types

    def visit_UnaryOpNode(self, node: "UnaryOpNode") -> "set[str]":
        return self(node.expr)

    def visit_LiteralNode(self, node: "LiteralNode") -> "set[str]":
        return set()

    def visit_TableAttrNode(self, node: "TableAttrNode") -> "set[str]":
        return set()

    def visit_CallNode(self, node: "CallNode") -> "set[str]":
        types = set()
        for p in node.params:
            types.update(self(p))
        return types

    def visit_TableNode(self, node: "TableNode") -> "set[str]":
        return set()

    def visit_ObjectTableNode(self, node: "ObjectTableNode") -> "set[str]":
        return set()

    def visit_CameraTableNode(self, node: "CameraTableNode") -> "set[str]":
        return set()

    def visit_CastNode(self, node: "CastNode") -> "set[str]":
        return self(node.expr)
