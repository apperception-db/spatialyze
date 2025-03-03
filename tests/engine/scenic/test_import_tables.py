from scripts.import_tables import import_tables
from spatialyze.database import database
import datetime
import pytest
import os
import json


@pytest.mark.parametrize("table, index, columns", [
    ("Camera", "cameraId, frameId, frameNum, fileName", "cameraId, frameId, frameNum, filename, ST_AsText(ST_ReducePrecision(cameraTranslation, 0.0001)), cameraRotation, cameraIntrinsic, ST_AsText(ST_ReducePrecision(egoTranslation, 0.0001)), egoRotation, timestamp, cameraHeading, egoHeading"),
    # ("Item_Detection", "itemId, cameraId, objectType, frameNum, timestamp, itemHeading", "itemId, cameraId, objectType, frameNum, ST_AsText(ST_ReducePrecision(translation, 0.0001)), timestamp, itemHeading"),
    ("Item_Trajectory", "itemId, cameraId, frameNum, itemHeading", "itemId, cameraId, objectType, frameNum, ST_AsText(ST_ReducePrecision(translation, 0.0001)), itemHeading")
])
def test_tables_contents(table, index, columns):
    import_tables(database, './data/scenic/database')

    DIR = "./data/scenic/import-tables-test-output"
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    res = database.execute(f"select {columns} from {table} order by {index}")
    # print(res)
    # assert False
    print("types", [type(elm) for elm in res[0]])
    res = [
        [elm.timestamp() if isinstance(elm, datetime.datetime) else elm for elm in row]
        for row in res
    ]
    filename = os.path.join(DIR, f"{table}.jsonl")
    if os.environ.get('GENERATE_ENGINE_TEST_RESULTS', 'false') == 'true':
        with open(filename, "w") as f:
            for r in res:
                f.write(json.dumps(r) + "\n")
    
    with open(filename, "r") as f:
        expected = format(json.loads(line) for line in f.readlines())
        assert format(json.loads(json.dumps(res))) == expected


def _format(elm):
    if isinstance(elm, float):
        return round(elm)
    if isinstance(elm, list) and all(isinstance(e, float) for e in elm):
        return [round(e, 3) for e in elm]
    if isinstance(elm, list) and all(isinstance(e, list) for e in elm):
        return [[round(ee, 3) for ee in e] for e in elm]
    return elm


def format(res):
    return [[*map(_format, row)] for row in res]
