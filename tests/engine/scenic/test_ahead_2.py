from spatialyze.predicate import objects, camera
from spatialyze.utils import F
import datetime as datetime
from scenic_common import get_results, database
import pytest


# with open('./scripts/pg-extender/ahead.sql', 'r') as file:
#     database.update(file.read())


@pytest.mark.parametrize("o1, o2, idx", [
    (objects[0], camera, 0),
    (objects[0], camera.cam, 2),
    (objects[0], camera.ego, 3),
])
def test_ahead_2(o1, o2, idx):
    results = database.predicate(
        F.ahead(o1, o2)
    )
    
    # set_results(results, f"./data/scenic/test-results/ahead_{idx}.py")
    assert len(results) == len(get_results(f"./data/scenic/test-results/ahead_{idx}.py"))
    assert set(results) == set(get_results(f"./data/scenic/test-results/ahead_{idx}.py"))