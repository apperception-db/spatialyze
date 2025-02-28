from spatialyze.predicate import objects, camera
from spatialyze.utils import F
from scenic_common import database, get_results


def test_fig_16():
    o = objects[0]
    c = camera
    results = database.predicate(
        F.contains('lane', c.ego) &
        # F.heading_diff(c.ego, F.road_direction(c.ego), between=[-15, 15]) &
        F.like(o.type, 'vehicle%') &
        (F.distance(o, c.ego) < 10) &  # replace convert_camera
        # (F.convert_camera(o, c.ego) > [0, 0]) &
        # (F.convert_camera(o, c.ego) < [4, 5]) &
        # F.heading_diff(o, F.road_direction(o), between=[-30, -15]) &
        True
    )

    assert len(results) == len(get_results('./data/scenic/test-results/fig_16.py'))
    assert set(results) == set(get_results('./data/scenic/test-results/fig_16.py'))
