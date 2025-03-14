from spatialyze.predicate import objects, camera
from spatialyze.utils import F
from scenic_common import get_results, database


def test_small_fig_14():
    obj1 = objects[0]
    cam = camera
    results = database.predicate(
        F.like(obj1.type, 'vehicle%') &
        (F.distance(cam.ego, obj1) < 50) &
        (F.view_angle(obj1, cam.ego) < 70 / 2) &
        # F.heading_diff(cam.ego, F.road_direction(cam.ego, cam.ego), between=[-180, -90]) &
        F.contains('road', cam.ego) &
        F.contains('road', obj1) &
        # F.heading_diff(obj1, F.road_direction(obj1, cam.ego), between=[-15, 15]) &
        (F.distance(cam.ego, obj1) < 10)
    )

    # set_results(results, './data/scenic/test-results/small_fig_14.py')
    assert len(results) == len(get_results('./data/scenic/test-results/small_fig_14.py'))
    assert set(results) == set(get_results('./data/scenic/test-results/small_fig_14.py'))
