from spatialyze.predicate import objects, camera
from spatialyze.utils import F
# from spatialyze.database import database
import datetime as datetime
from scenic_common import get_results, prepare_predicate_and_tables, database
import pytest


# with open('./scripts/pg-extender/viewAngle.sql', 'r') as file:
#     database.update(file.read())


@pytest.mark.parametrize("angle", [10, 20, 30] + list(range(45, 181, 45)))
def test_view_angle_2(angle):
    o = objects[0]
    c = camera
    results = database.predicate(F.view_angle(o, c) < angle)
    
    assert set(results) == set(get_results(f"./data/scenic/test-results/view_angle_{angle}.py"))


def test_view_angle_return_value():
    predicate = F.view_angle(objects[0], camera)
    pred_str, t_tables, _ = prepare_predicate_and_tables(predicate, True)

    sql_str = (
        f"SELECT c0.cameraId, itemId, c0.frameNum, ROUND({pred_str}::numeric, 1)::real\n"
        f"FROM Camera as c0\n{t_tables}"
        f"ORDER BY c0.cameraId, itemId, c0.frameNum"
    )

    results = database.execute(sql_str)
    
    # set_results(results, f"./data/scenic/test-results/return-values/view_angle.py")
    assert set(results) == set(get_results(f"./data/scenic/test-results/return-values/view_angle.py"))
