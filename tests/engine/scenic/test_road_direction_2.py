from spatialyze.predicate import objects, camera
from spatialyze.utils import F
import datetime as datetime
from scenic_common import get_results, database
import pytest


# with open('./scripts/pg-extender/roadDirection.sql', 'r') as file:
#     database.update(file.read())


ANGLE_STEP = 45


def generate_case(o, angle):
    return o, angle, angle + ANGLE_STEP


@pytest.mark.parametrize("o, sangle, eangle", [
    generate_case(o, angle)
    for o in (objects[0], camera)
    for angle in range(0, 360, ANGLE_STEP)
])
def test_road_direction_2(o, sangle, eangle):
    results = database.predicate((sangle <= F.road_direction(o)) & (F.road_direction(o) < eangle))
    
    # set_results(results, f"./data/scenic/test-results/road_direction_{o}_{sangle}.py")
    assert set(results) == set(get_results(f"./data/scenic/test-results/road_direction_{o}_{sangle}.py"))