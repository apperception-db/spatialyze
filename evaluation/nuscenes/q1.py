import time
from os import environ

from spatialyze.database import database
from spatialyze.utils import F
from spatialyze.predicate import camera, objects, lit

o = objects[0]
c = camera
pred1 = (
    (F.like(c.filename, 'samples/CAM_FRONT%')) & 
    (o.type == 'human.pedestrian.adult') &
    # F.contained(c.ego, 'intersection') &
    F.contained(o.trans@c.time, 'intersection') &
    F.angle_excluding(F.facing_relative(o.trans@c.time, c.cam), lit(-70), lit(70)) &
    # F.angle_between(F.facing_relative(c.cam, F.road_direction(c.ego)), lit(-15), lit(15)) &
    (F.distance(c.ego, o.trans@c.time) < lit(50)) & # &
    (F.view_angle(o.trans@c.time, c.cam) < lit(35))
)

start = time.time()
# keys = world.get_traj_key()
# id_time_camI  d_filename = world.get_id_time_camId_filename(num_joined_tables=1)

result = database.predicate(pred1)

end = time.time()
print("Figure 12 (baseline): ", format(end-start))

filenames = list(set([x[3] for x in result if "samples" in x[3]]))
with open('fig12_baseline_results.txt', 'w') as f:
    for line in filenames:
        f.write(f"{line}\n")