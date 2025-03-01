from spatialyze.predicate import objects, camera, lit
from spatialyze.utils import F
from spatialyze.database import database
import datetime as datetime
from scenic_common import get_results
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