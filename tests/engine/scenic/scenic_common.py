import duckdb

from spatialyze.database import Database
from spatialyze.data_types.query_result import QueryResult


database = Database(duckdb.connect("/tmp/__spatialyze__test.duckdb"))


def get_results(path: str) -> list[QueryResult]:
    with open(path, "r") as f:
        results = f.readlines()
    return eval("\n".join(results[1:]))