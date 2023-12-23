import time
from os import environ

from spatialyze.database import database
from spatialyze.utils import F
from spatialyze.predicate import camera, objects, lit

obj1 = objects[0]
cam = camera
pred3 = (
    (F.like(cam.filename, 'samples/CAM_FRONT%')) & 
    ((obj1.type == 'vehicle.car') | (obj1.type == 'vehicle.truck')) &
    (F.view_angle(obj1.trans@cam.time, cam.cam) < lit(35)) &
    F.angle_between(F.facing_relative(cam.cam, F.road_direction(cam.ego, cam.ego)), 135, 225) &
    F.contained(cam.cam, F.road_segment('lane')) &
    F.contained(obj1.trans@cam.time, F.road_segment('lane')) &
    F.angle_between(F.facing_relative(obj1.trans@cam.time, F.road_direction(obj1.trans@cam.time, cam.ego)), -15, 15) &
    # F.angle_between(F.facing_relative(obj1.trans@cam.time, cam.ego), 135, 225) &
    (F.distance(cam.ego, obj1.trans@cam.time) < 10)
)


start = time.time()

result = database.predicate(pred3)

end = time.time()
print("Figure 14 (baseline): ", format(end-start))

filenames = list(set([x[3] for x in result if "samples" in x[3]]))
with open('fig14_baseline_results.txt', 'w') as f:
    for line in filenames:
        f.write(f"{line}\n")