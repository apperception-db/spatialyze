from spatialyze.predicate import objects, camera
from spatialyze.utils import F
from scenic_common import get_results, database



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

        # F.heading_diff(cam.ego, F.road_direction(cam.ego, cam.ego), between=[-15, 15]) &
        (F.view_angle(car1, cam.ego) < 70 / 2) &
        (F.distance(cam.ego, car1) < 40) &
        F.heading_diff(car1, cam.ego, between=[-15, 15]) &
        # F.heading_diff(car1, F.road_direction(car1, cam.ego), between=[-15, 15]) &
        (F.distance(car1, cam.ego) < 15) &  # replace ahead
        # F.ahead(car1, cam.ego) &
        # F.heading_diff(cam.ego, F.road_direction(cam.ego, cam.ego), between=[-15, 15]) &
        (F.distance(opposite_car, cam.ego) < 50) &  # replace convert_camera
        # (F.convert_camera(opposite_car, cam.ego) > [-10, 0]) &
        # (F.convert_camera(opposite_car, cam.ego) < [-1, 50]) &
        F.heading_diff(opposite_car, cam.ego, between=[140, 180]) &
        (F.distance(opposite_car, car2) < 40) &
        # F.heading_diff(car2, F.road_direction(car2, cam.ego), between=[-15, 15]) &
        (F.distance(car2, opposite_car) < 15) &  # replace ahead
        # F.ahead(car2, opposite_car) &
        True
    )

    assert len(results) == len(get_results('./data/scenic/test-results/fig_15.py'))
    assert set(results) == set(get_results('./data/scenic/test-results/fig_15.py'))
