from spatialyze.predicate import ObjectTableNode, objects, camera
from spatialyze.utils import F
from spatialyze.database import database
import datetime as datetime
from scenic_common import get_results, prepare_predicate_and_tables
import pytest


with open('./scripts/pg-extender/roadDirection.sql', 'r') as file:
    database.update(file.read())


ANGLE_STEP = 90


def generate_case(o, angle):
    return o, angle


@pytest.mark.parametrize("o, angle", [
    generate_case(o, angle)
    for o in (objects[0], camera)
    for angle in range(0, 360, ANGLE_STEP)
])
def test_road_direction_2(o, angle):
    results = database.predicate((angle <= F.road_direction(o)) & (F.road_direction(o) < (angle + ANGLE_STEP)))
    
    o_str = f'{o}'.replace('[', '').replace(']', '')
    # set_results(results, f"./data/scenic/test-results/road_direction_{o_str}_{angle}.py")
    assert set(results) == set(get_results(f"./data/scenic/test-results/road_direction_{o_str}_{angle}.py"))


@pytest.mark.parametrize("o, idx, table", [
    (objects[0], 'itemid', 'Item_Trajectory AS t0'),
    (camera, 'cameraid, framenum, frameid', 'Camera as c0'),
])
def test_road_direction_return_value(o, idx, table):
    predicate = F.road_direction(o)
    pred_str, _, _ = prepare_predicate_and_tables(predicate, isinstance(o, ObjectTableNode))

    sql_str = (
        f"SELECT {idx}, ROUND({pred_str}::numeric, 1)::real\n"
        f"FROM {table}\n"
        f"ORDER BY {idx}"
    )

    results = database.execute(sql_str)
    
    o_str = f'{o}'.replace('[', '').replace(']', '')
    # set_results(results, f"./data/scenic/test-results/return-values/road_direction_{o_str}.py")
    assert set(results) == set(get_results(f"./data/scenic/test-results/return-values/road_direction_{o_str}.py"))