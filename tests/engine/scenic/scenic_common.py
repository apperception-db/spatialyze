from spatialyze.data_types.query_result import QueryResult
from spatialyze.database import _join_table
from spatialyze.predicate import FindAllTablesVisitor, GenSqlVisitor, MapTablesTransformer, normalize


def get_results(path: str) -> list[QueryResult]:
    with open(path, "r") as f:
        results = f.readlines()
    return eval("\n".join(results[1:]))


def set_results(results: list, path: str):
    with open(path, "w") as f:
        f.write('from spatialyze.data_types.query_result import QueryResult\n')
        f.write("[\n")
        for r in results:
            f.write(f"{r},\n")
        f.write("]\n")


def prepare_predicate_and_tables(predicate, temporal):
    tables, _ = FindAllTablesVisitor()(predicate)
    tables = sorted(tables)
    mapping = {t: i for i, t in enumerate(tables)}
    predicate = normalize(predicate, temporal)
    predicate = MapTablesTransformer(mapping)(predicate)
    join_table = _join_table(temporal)

    t_tables = ""
    t_outputs = ""
    for i in range(len(tables)):
        t_tables += join_table(i)
        t_outputs += f",\n   t{i}.itemId"

    return GenSqlVisitor()(predicate), t_tables, t_outputs