import time
from os import environ

from spatialyze.database import database
from spatialyze.utils import F
from spatialyze.predicate import camera, objects, lit
database.connection

cam = camera
car1 = objects[0]
opposite_car_1 = objects[1]
opposite_car_2 = objects[2]

pred4 = (
    (F.like(cam.filename, 'samples/CAM_FRONT%')) & 
    ((car1.type == 'vehicle.car') | (car1.type == 'vehicle.truck')) &
    ((opposite_car_2.type == 'vehicle.car') | (opposite_car_2.type == 'vehicle.truck')) &
    ((opposite_car_1.type == 'vehicle.car') | (opposite_car_1.type == 'vehicle.truck')) &
    (opposite_car_1.id != opposite_car_2.id) &
    (car1.id != opposite_car_2.id) &
    (car1.id != opposite_car_1.id) &

    F.contained(cam.cam, F.road_segment('lane')) &
    F.contained(car1.trans@cam.time, F.road_segment('lane')) &
    F.contained(opposite_car_1.trans@cam.time, F.road_segment('lane')) &
    F.contained(opposite_car_2.trans@cam.time, F.road_segment('lane')) &
    F.angle_between(F.facing_relative(cam.cam, F.road_direction(cam.cam, cam.cam)), -15, 15) &
    (F.view_angle(car1.trans@cam.time, cam.cam) < lit(35)) &
    (F.distance(cam.cam, car1.traj@cam.time) < 40) &
    F.angle_between(F.facing_relative(car1.traj@cam.time, cam.ego), -15, 15) &
    # F.angle_between(F.facing_relative(car1.traj@cam.time, F.road_direction(car1.traj@cam.time, cam.ego)), -15, 15) &
    F.ahead(car1.traj@cam.time, cam.cam) &
    # (F.convert_camera(opposite_car.traj@cam.time, cam.ego) > [-10, 0]) &
    # (F.convert_camera(opposite_car.traj@cam.time, cam.ego) < [-1, 50]) &
    F.angle_between(F.facing_relative(opposite_car_1.traj@cam.time, cam.ego), 135, 225) &
    # (F.distance(opposite_car@cam.time, car2@cam.time) < 40)# &
    F.angle_between(F.facing_relative(opposite_car_2.traj@cam.time, opposite_car_1.traj@cam.time), -15, 15) &
    F.angle_between(F.facing_relative(opposite_car_2.traj@cam.time, F.road_direction(opposite_car_2.traj@cam.time, cam.ego)), -15, 15) &
    F.ahead(opposite_car_2.traj@cam.time, opposite_car_1.traj@cam.time)
    )

start = time.time()

result = database.predicate(pred4)

end = time.time()
print("Figure 15 (baseline): ", format(end-start))

filenames = list(set([x[3] for x in result if "samples" in x[3]]))
with open('fig15_baseline_results.txt', 'w') as f:
    for line in filenames:
        f.write(f"{line}\n")