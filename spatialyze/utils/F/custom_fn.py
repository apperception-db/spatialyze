from ...predicate import GenSqlVisitor, PredicateNode, call_node


def custom_fn(name: str, num_args: int | None = None):
    @call_node
    def fn(
        visitor: GenSqlVisitor,
        args: list[PredicateNode],
        kwargs: dict[str, PredicateNode],
    ):
        assert kwargs is None or len(kwargs) == 0, kwargs
        if num_args is not None and len(args) != num_args:
            raise Exception(f"{name} is expecting {num_args} arguments, but received {len(args)}")
        return f"{name}({','.join(map(visitor, args))})"

    return fn
