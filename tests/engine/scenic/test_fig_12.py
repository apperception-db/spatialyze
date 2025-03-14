from spatialyze.predicate import objects, camera
from spatialyze.utils import F
import datetime as datetime
from scenic_common import get_results, database


def test_fig_12():
    o = objects[0]
    c = camera
    results = database.predicate(
        F.like(o.type, 'human.pedestrian%') &
        F.contains('road', c.ego) &
        F.contains('road', o) &
        F.heading_diff(o, c.ego, excluding=[-70, 70]) &
        F.heading_diff(c.ego, F.road_direction(c.ego, c.ego), between=[-15, 15]) &
        (F.distance(c, o) < 50) &
        (F.view_angle(o, c) < 35)
    )

    assert set(results) == set([])


def test_fig_12_new():
    o = objects[0]
    c = camera
    results = database.predicate(
        F.like(o.type, 'human.pedestrian%') &
        F.contains('road', c.ego) &
        F.contains('road', o) &
        F.heading_diff(o, c.ego, between=[-70, 70]) &
        F.heading_diff(c.ego, F.road_direction(c.ego, c.ego), between=[-15, 15]) &
        (F.distance(c, o) < 50) &
        (F.view_angle(o, c) < 35)
    )

    assert set(results) == set(get_results('./data/scenic/test-results/fig_12.py'))