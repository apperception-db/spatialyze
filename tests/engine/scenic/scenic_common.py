import duckdb

from spatialyze.database import Database
from spatialyze.data_types.query_result import QueryResult


database = Database(duckdb.connect("/tmp/__spatialyze__test.duckdb"))


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