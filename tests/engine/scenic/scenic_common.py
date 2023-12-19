from spatialyze.data_types.query_result import QueryResult


def get_results(path: str) -> list[QueryResult]:
    with open(path, "r") as f:
        results = f.readlines()
    return eval("\n".join(results[1:]))