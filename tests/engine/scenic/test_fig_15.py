from spatialyze.data_types.query_result import QueryResult
from spatialyze.database import database
from spatialyze.predicate import objects, camera
from spatialyze.utils import F


def test_fig_15():
    cam = camera
    car1 = objects[0]
    opposite_car = objects[1]
    car2 = objects[2]

    results = database.predicate(
        F.like(car1.type, 'vehicle%') &
        F.like(car2.type, 'vehicle%') &
        F.like(opposite_car.type, 'vehicle%') &
        (opposite_car.id != car2.id) &
        (car1.id != car2.id) &
        (car1.id != opposite_car.id) &

        F.heading_diff(cam.ego, F.road_direction(cam.ego, cam.ego), between=[-15, 15]) &
        (F.view_angle(car1, cam.ego) < 70 / 2) &
        (F.distance(cam.ego, car1) < 40) &
        F.heading_diff(car1, cam.ego, between=[-15, 15]) &
        F.heading_diff(car1, F.road_direction(car1, cam.ego), between=[-15, 15]) &
        F.ahead(car1, cam.ego) &
        F.heading_diff(cam.ego, F.road_direction(cam.ego, cam.ego), between=[-15, 15]) &
        (F.convert_camera(opposite_car, cam.ego) > [-10, 0]) &
        (F.convert_camera(opposite_car, cam.ego) < [-1, 50]) &
        F.heading_diff(opposite_car, cam.ego, between=[140, 180]) &
        (F.distance(opposite_car, car2) < 40) &
        F.heading_diff(car2, F.road_direction(car2, cam.ego), between=[-15, 15]) &
        F.ahead(car2, opposite_car)
    )

    assert set(results) == set([
        QueryResult(frame_number=2, camera_id='scene-0207', filename='samples/CAM_FRONT/n008-2018-07-26-12-13-50-0400__CAM_FRONT__1532621920162404.jpg', item_ids=('6a81ab78eee3477e8509569a5d0a2217', '679391fb87db41cc97b4b6233c8795f5', 'fd2437defb374b4a96cbd6cf3d79be26')),
        QueryResult(frame_number=3, camera_id='scene-0207', filename='samples/CAM_FRONT/n008-2018-07-26-12-13-50-0400__CAM_FRONT__1532621920662404.jpg', item_ids=('6a81ab78eee3477e8509569a5d0a2217', '679391fb87db41cc97b4b6233c8795f5', 'fd2437defb374b4a96cbd6cf3d79be26')),
    ])
