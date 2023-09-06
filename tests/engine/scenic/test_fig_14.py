from spatialyze.database import database
from spatialyze.predicate import objects, camera
from spatialyze.utils import F
from datetime import datetime, timezone


def test_fig_14():
    obj1 = objects[0]
    cam = camera
    results = database.predicate(
        F.like(obj1.type, 'vehicle%') &
        (F.distance(cam.ego, obj1.trans@cam.timestamp) < 50) &
        (F.view_angle(obj1.trans@cam.time, cam.ego) < 70 / 2) &
        F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -180, -90) &
        F.contained(cam.ego, F.road_segment('road')) &
        F.contained(obj1.trans@cam.time, F.road_segment('road')) &
        F.angle_between(F.facing_relative(obj1.trans@cam.time, F.road_direction(obj1.traj@cam.time, cam.ego)), -15, 15) &
        (F.distance(cam.ego, obj1.trans@cam.time) < 10)
    )

    assert set(results) == set([
        (
            '9e02e0dcb5f04d01a4b8f0559d0e7d95',
            datetime(2018, 8, 30, 12, 31, 31, 612404, tzinfo=timezone.utc),
            'scene-0769',
            'samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657491612404.jpg'
        ),
        (
            '9e02e0dcb5f04d01a4b8f0559d0e7d95',
            datetime(2018, 8, 30, 12, 31, 32, 112404, tzinfo=timezone.utc),
            'scene-0769',
            'samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657492112404.jpg'
        ),
    ])
