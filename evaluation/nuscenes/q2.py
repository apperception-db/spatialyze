import time
from os import environ

from spatialyze.database import database
from spatialyze.legacy.world import empty_world
from spatialyze.utils import F
from spatialyze.predicate import camera, objects, lit
database.connection

name = 'ScenicWorld'
world = empty_world(name=name)

obj1 = objects[0]
obj2 = objects[1]
cam = camera
pred2 =(
    (F.like(cam.filename, 'samples/CAM_FRONT%')) & 
    (obj1.id != obj2.id) &
    ((obj1.type == 'vehicle.car') | (obj1.type == 'vehicle.truck')) &
    ((obj2.type == 'vehicle.car') | (obj2.type == 'vehicle.truck')) &
    # F.angle_between(F.facing_relative(cam.cam, F.road_direction(cam.cam)), -15, 15) &
    (F.distance(cam.ego, obj1.trans@cam.time) < 50) &
    (F.view_angle(obj1.trans@cam.time, cam.cam) < lit(35)) &
    (F.distance(cam.ego, obj2.trans@cam.time) < 50) &
    (F.view_angle(obj2.trans@cam.time, cam.cam) < lit(35)) &
    F.contained(obj1.trans@cam.time, 'intersection') &
    F.contained(obj2.trans@cam.time, 'intersection') &
    # F.angle_between(F.facing_relative(obj1.trans@cam.time, cam.cam), 40, 135) &
    # F.angle_between(F.facing_relative(obj2.trans@cam.time, cam.cam), -135, -50) &
    F.angle_between(F.facing_relative(obj1.traj@cam.time, obj2.traj@cam.time), -180, -90)
    # (F.min_distance(cam.ego, 'intersection') < 10) &
    # F.angle_between(F.facing_relative(obj1.trans@cam.time, obj2.trans@cam.time), 100, -100)
)


start = time.time()

result = database.predicate(pred2)

end = time.time()
print("Figure 13 (baseline): ", format(end-start))

filenames = list(set([x[4] for x in result if "samples" in x[4]]))
with open('fig13_baseline_results.txt', 'w') as f:
    for line in filenames:
        f.write(f"{line}\n")