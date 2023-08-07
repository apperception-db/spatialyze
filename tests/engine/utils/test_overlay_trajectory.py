from spatialyze.legacy.world import empty_world
from spatialyze.database import database
from spatialyze.utils import overlay_trajectory, F
from spatialyze.predicate import objects, camera


def test_fig_13():
    obj1 = objects[0]
    obj2 = objects[1]
    cam = camera

    world = empty_world().filter(
        (obj1.id != obj2.id) &
        F.like(obj1.type, 'vehicle%') &
        F.like(obj2.type, 'vehicle%') &
        F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -15, 15) &
        (F.distance(cam.ego, obj1.trans@cam.time) < 50) &
        (F.view_angle(obj1.trans@cam.time, cam.ego) < 70 / 2.0) &
        (F.distance(cam.ego, obj2.trans@cam.time) < 50) &
        (F.view_angle(obj2.trans@cam.time, cam.ego) < 70 / 2.0) &
        F.contains_all('intersection', [obj1.trans, obj2.trans]@cam.time) &
        F.angle_between(F.facing_relative(obj1.trans@cam.time, cam.ego), 50, 135) &
        F.angle_between(F.facing_relative(obj2.trans@cam.time, cam.ego), -135, -50) &
        (F.min_distance(cam.ego, F.road_segment('intersection')) < 10) &
        F.angle_between(F.facing_relative(obj1.trans@cam.time, obj2.trans@cam.time), 100, -100)
    )

    data_dir =  "data/scenic/images"
    overlay_trajectory(world=world, database=database, images_data_path=data_dir, is_overlay_headings=True, is_overlay_objects=True, is_overlay_road=True, is_keep_whole_video=True)
    overlay_trajectory(world=world, database=database, images_data_path=data_dir, is_overlay_headings=True, is_overlay_objects=True, is_overlay_road=True, is_keep_whole_video=False)
