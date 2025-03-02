from spatialyze.predicate import objects, camera, lit
from spatialyze.utils import F
from spatialyze.database import database
import datetime as datetime
from scenic_common import get_results, prepare_predicate_and_tables, set_results
import pytest


with open('./scripts/pg-extender/minDistance.sql', 'r') as file:
    database.update(file.read())


@pytest.mark.parametrize("distance", [ 1, 5, 10, 20, 30, 40, 50 ])
def test_min_distance_2(distance):
    o = objects[0]
    c = camera
    results = database.predicate(
        F.min_distance(c.ego, lit('intersection')) < distance
    )

    assert set(results) == set(get_results(f"./data/scenic/test-results/min_distance_{distance}.py"))
    # assert set(results) == set([])

@pytest.mark.parametrize("name, o, o_str, o_idx, geog", [
    (name, o, o_str, o_idx, geog)
    for name, o, o_str, o_idx in (('obj', objects[0].trans, 'Item_Trajectory AS t0', 'itemid'), ('cam', camera.cam, 'Camera as c0', 'cameraid, framenum, frameid'))
    for geog in ('intersection', 'lane')
])
def test_min_distance_return_value(name, o, o_str, o_idx, geog):
    predicate = F.min_distance(o, lit(geog))
    pred_str, _, _ = prepare_predicate_and_tables(predicate, True)

    sql_str = (
        f"SELECT {o_idx}, ROUND({pred_str}::numeric, 3)::real\n"
        f"FROM {o_str} \n"
        f"ORDER BY {o_idx}"
    )

    results = [(*row[:-1], round(row[-1], 2)) for row in database.execute(sql_str)]
    
    # set_results(results, f"./data/scenic/test-results/return-values/min_distance_{name}_{geog}.py")
    assert set(results) == set(get_results(f"./data/scenic/test-results/return-values/min_distance_{name}_{geog}.py"))
