from spatialyze.data_types.query_result import QueryResult
from spatialyze.database import database
from spatialyze.predicate import objects, camera
from spatialyze.utils import F


def test_fig_14():
    obj1 = objects[0]
    cam = camera
    results = database.predicate(
        F.like(obj1.type, 'vehicle%') &
        (F.distance(cam.ego, obj1) < 50) &
        (F.view_angle(obj1, cam.ego) < 70 / 2) &
        F.heading_diff(cam.ego, F.road_direction(cam.ego, cam.ego), between=[-180, -90]) &
        F.contains('road', cam.ego) &
        F.contains('road', obj1) &
        F.heading_diff(obj1, F.road_direction(obj1, cam.ego), between=[-15, 15]) &
        (F.distance(cam.ego, obj1) < 10)
    )

    assert set(results) == set([
        QueryResult(frame_number=1, camera_id='scene-0769', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657491612404.jpg', item_ids=('9e02e0dcb5f04d01a4b8f0559d0e7d95',)),
        QueryResult(frame_number=2, camera_id='scene-0769', filename='samples/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657492112404.jpg', item_ids=('9e02e0dcb5f04d01a4b8f0559d0e7d95',)),
    ])
