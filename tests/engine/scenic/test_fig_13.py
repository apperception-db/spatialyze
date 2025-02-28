from spatialyze.predicate import camera, objects
from spatialyze.utils import F
from scenic_common import get_results, database


def test_fig_13():
    obj1 = objects[0]
    obj2 = objects[1]
    cam = camera

    results = database.predicate(
        (obj1.id != obj2.id) &
        F.like(obj1.type, 'vehicle%') &
        F.like(obj2.type, 'vehicle%') &
        # F.heading_diff(cam.ego, F.road_direction(cam.ego, cam.ego), between=[-15, 15]) &
        (F.distance(cam.ego, obj1) < 50) &
        # (F.view_angle(obj1, cam.ego) < 70 / 2.0) &
        (F.distance(cam.ego, obj2) < 50) &
        # (F.view_angle(obj2, cam.ego) < 70 / 2.0) &
        F.contains('intersection', [obj1, obj2]) &
        F.heading_diff(obj1, cam.ego, between=[50, 135]) &
        F.heading_diff(obj2, cam.ego, between=[-135, -50]) &
        (F.min_distance(cam.ego, F.road_segment('intersection')) < 10) &
        F.heading_diff(obj1, obj2, between=[100, -100])
    )
    assert len(results) == len(get_results('./data/scenic/test-results/fig_13.py'))
    assert set(results) == set(get_results('./data/scenic/test-results/fig_13.py'))