from spatialyze.predicate import objects, camera
from spatialyze.utils import F
from spatialyze.database import database
import datetime as datetime
from scenic_common import get_results
import pytest


with open('./scripts/pg-extender/viewAngle.sql', 'r') as file:
    database.update(file.read())


@pytest.mark.parametrize("angle", [10, 20, 30] + list(range(45, 181, 45)))
def test_min_distance(angle):
    o = objects[0]
    c = camera
    results = database.predicate(F.view_angle(o, c) < angle)
    
    assert set(results) == set(get_results(f"./data/scenic/test-results/view_angle_{angle}.py"))