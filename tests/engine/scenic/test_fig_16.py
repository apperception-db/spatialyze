from spatialyze.database import database
from spatialyze.predicate import AtTimeNode, objects, camera
from spatialyze.utils import F

def test_fig_16():
    o = objects[0]
    c = camera
    results = database.predicate(
        F.contains('lane', c.ego) &
        F.heading_diff(c.ego, F.road_direction(c.ego), between=[-15, 15]) &
        F.like(o.type, 'vehicle%') &
        (F.convert_camera(o, c.ego) > [0, 0]) &
        (F.convert_camera(o, c.ego) < [4, 5]) &
        F.heading_diff(o, F.road_direction(o), between=[-30, -15])
    )

    assert len(results) == 0, results
