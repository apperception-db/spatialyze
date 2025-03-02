from spatialyze.predicate import objects, camera
from spatialyze.utils import F
import datetime as datetime
from scenic_common import get_results, database
import pytest


# with open('./scripts/pg-extender/convertCamera.sql', 'r') as file:
#     database.update(file.read())


def generate_case(distance):
    return [
        [(1, 1), (distance, distance)],
        [(-distance, 1), (-1, distance)],
        [(-distance, -distance), (-1, -1)],
        [(1, -distance), (distance, -1)]
    ]


@pytest.mark.parametrize("bl, tr", [
    *generate_case(2),
    *generate_case(5),
    *generate_case(10),
    *generate_case(20),
    *generate_case(40),
    *generate_case(80),
])
def test_convert_camera_2(bl, tr):
    o = objects[0]
    c = camera
    results = database.predicate(
        F.plt(f'Point ({" ".join(map(str, bl))})', F.convert_camera(o, c.ego)) &
        F.plt(F.convert_camera(o, c.ego), f'Point ({" ".join(map(str, tr))})')
    )
    
    # set_results(results, f"./data/scenic/test-results/convert_camera_{'_'.join(map(str, bl))}_{'_'.join(map(str, tr))}.py")
    assert set(results) == set(get_results(f"./data/scenic/test-results/convert_camera_{'_'.join(map(str, bl))}_{'_'.join(map(str, tr))}.py"))