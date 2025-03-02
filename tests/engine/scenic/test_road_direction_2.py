from spatialyze.predicate import FindAllTablesVisitor, GenSqlVisitor, MapTablesTransformer, ObjectTableNode, normalize, objects, camera
from spatialyze.utils import F
import datetime as datetime
from scenic_common import get_results, database
import pytest


# with open('./scripts/pg-extender/roadDirection.sql', 'r') as file:
#     database.update(file.read())


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


@pytest.mark.parametrize("o", [objects[0], camera])
def test_road_direction_raw(o):
    predicate = F.road_direction(o)
    tables, _ = FindAllTablesVisitor()(predicate)
    tables = sorted(tables)
    mapping = {t: i for i, t in enumerate(tables)}
    temporal = isinstance(o, ObjectTableNode)
    predicate = normalize(predicate, temporal)
    predicate = MapTablesTransformer(mapping)(predicate)
    
    idx = 'itemid' if isinstance(o, ObjectTableNode) else 'cameraid, framenum, frameid'
    table = 'Item_Trajectory AS t0' if isinstance(o, ObjectTableNode) else "Camera as c0"

    sql_str = (
        f"SELECT {idx}, ROUND({GenSqlVisitor()(predicate)}::numeric, 1)::real\n"
        f"FROM {table}\n"
        f"ORDER BY {idx}"
    )

    results = [tuple(round(e, 1) if isinstance(e, float) else e for e in row) for row in database.execute(sql_str)]
    
    o_str = f'{o}'.replace('[', '').replace(']', '')
    # set_results(results, f"./data/scenic/test-results/road_direction_{o_str}.py")
    assert set(results) == set(get_results(f"./data/scenic/test-results/road_direction_{o_str}.py"))