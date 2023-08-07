from spatialyze.legacy.world import empty_world
from spatialyze.utils import F
from spatialyze.predicate import objects, camera

def test_fig_16():
    o = objects[0]
    c = camera
    world = empty_world().filter(
        F.contained(c.ego, F.road_segment('lanewithrightlane')) &
        F.angle_between(F.facing_relative(c.ego, F.road_direction(c.ego)), -15, 15) &
        F.like(o.type, 'vehicle%') &
        (F.convert_camera(o.traj@c.time, c.ego) > [0, 0]) &
        (F.convert_camera(o.traj@c.time, c.ego) < [4, 5]) &
        F.angle_between(F.facing_relative(o.traj@c.time, F.road_direction(o.traj@c.time)), -30, -15)
    )

    assert world.get_id_time_camId_filename(1) == []
