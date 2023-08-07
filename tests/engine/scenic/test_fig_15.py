from spatialyze.legacy.world import empty_world
from spatialyze.utils import F
from spatialyze.predicate import objects, camera
from datetime import datetime, timezone


def test_fig_15():
    cam = camera
    car1 = objects[0]
    opposite_car = objects[1]
    car2 = objects[2]

    world = empty_world().filter(
        F.like(car1.type, 'vehicle%') &
        F.like(car2.type, 'vehicle%') &
        F.like(opposite_car.type, 'vehicle%') &
        (opposite_car.id != car2.id) &
        (car1.id != car2.id) &
        (car1.id != opposite_car.id) &

        F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -15, 15) &
        (F.view_angle(car1.traj@cam.time, cam.ego) < 70 / 2) &
        (F.distance(cam.ego, car1.traj@cam.time) < 40) &
        F.angle_between(F.facing_relative(car1.traj@cam.time, cam.ego), -15, 15) &
        F.angle_between(F.facing_relative(car1.traj@cam.time, F.road_direction(car1.traj@cam.time, cam.ego)), -15, 15) &
        F.ahead(car1.traj@cam.time, cam.ego) &
        F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -15, 15) &
        (F.convert_camera(opposite_car.traj@cam.time, cam.ego) > [-10, 0]) &
        (F.convert_camera(opposite_car.traj@cam.time, cam.ego) < [-1, 50]) &
        F.angle_between(F.facing_relative(opposite_car.traj@cam.time, cam.ego), 140, 180) &
        (F.distance(opposite_car@cam.time, car2@cam.time) < 40) &
        F.angle_between(F.facing_relative(car2.traj@cam.time, F.road_direction(car2.traj@cam.time, cam.ego)), -15, 15) &
        F.ahead(car2.traj@cam.time, opposite_car.traj@cam.time)
    )

    assert set(world.get_id_time_camId_filename(1)) == set([
        (
            '6a81ab78eee3477e8509569a5d0a2217',
            datetime(2018, 7, 26, 9, 18, 40, 162404, tzinfo=timezone.utc),
            'scene-0207',
            'samples/CAM_FRONT/n008-2018-07-26-12-13-50-0400__CAM_FRONT__1532621920162404.jpg'
        ),
        (
            '6a81ab78eee3477e8509569a5d0a2217',
            datetime(2018, 7, 26, 9, 18, 40, 662404, tzinfo=timezone.utc),
            'scene-0207',
            'samples/CAM_FRONT/n008-2018-07-26-12-13-50-0400__CAM_FRONT__1532621920662404.jpg'
        ),
    ])
