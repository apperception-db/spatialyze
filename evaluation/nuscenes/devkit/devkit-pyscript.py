"""
Differences between results due to:
1. Differences in checking if visible
2. Differenc
"""
from nuscenes.nuscenes import NuScenes
import numpy as np

from nuscenes.map_expansion.map_api import NuScenesMap
from nuscenes.map_expansion import arcline_path_utils
import time

from pyquaternion import Quaternion
import math
from nuscenes.utils.geometry_utils import BoxVisibility

import os, psutil

# nusc_map = NuScenesMap(dataroot='/data/raw/map-expansion', map_name='boston-seaport')
nusc_map = NuScenesMap(dataroot='/work/apperception/data/raw/nuScenes/Map-expansion', map_name='boston-seaport')

# nusc = NuScenes(version='v1.0-trainval', dataroot='/data/raw/full-dataset/trainval', verbose=True)
nusc = NuScenes(version='v1.0-mini', dataroot='/work/apperception/data/raw/nuScenes/full-dataset-v1.0/Mini', verbose=True)

class Instance():
  def __init__(self, timestamp, cam_direction, sample_record, annotation_token, ego_pose_token, annotation_token2=None, annotation_token3=None):
    self.timestamp = timestamp
    self.sample_record = sample_record
    self.cam_direction = cam_direction
    self.annotation_token = annotation_token
    self.annotation_token2 = annotation_token2
    self.annotation_token3 = annotation_token3
    self.ego_pose_token = ego_pose_token



def normalizeAngle(angle) -> float:
    while angle > math.pi:
        angle -= math.tau
    while angle < -math.pi:
        angle += math.tau
    assert -math.pi <= angle <= math.pi
    return angle

def get_heading(rotation):
    yaw = Quaternion(rotation).yaw_pitch_roll[0]
    return normalizeAngle(yaw)

def get_camera_heading(ego_rotation, cam_rotation):
  ROT = Quaternion(axis=[1, 0, 0], angle=np.pi / 2)
  ego_heading = get_heading(ego_rotation)
  camera_heading =  -get_heading(ROT.rotate(Quaternion(cam_rotation))) + math.pi / 2 

  return normalizeAngle(camera_heading + ego_heading)

  
 
def get_road_direction(position):
  x, y, z = position
  closest_lane = nusc_map.get_closest_lane(x, y, radius=2)
  if closest_lane:
    lane_record = nusc_map.get_arcline_path(closest_lane)
    poses = arcline_path_utils.discretize_lane(lane_record, resolution_meters=1)
    closest_pose_on_lane, distance_along_lane = arcline_path_utils.project_pose_to_lane((x, y, 0), lane_record)
    yaw = closest_pose_on_lane[2]
    return normalizeAngle(yaw)
  else:
    return None  

 
def is_contained(position, segment_type):
  x, y, z = position
  return nusc_map.layers_on_point(x, y)[segment_type] != ''

 
def is_contained_intersection(position):
  x, y, z = position
  road_segment_token = nusc_map.layers_on_point(x, y)['road_segment']
  if road_segment_token != '':
    road_segment = nusc_map.get('road_segment', road_segment_token)
    return road_segment["is_intersection"]
  else:
    return False


def is_visible(sample_record, annotation_token, cam_direction):
  camera = sample_record["data"][cam_direction]
  _, boxes, _ = nusc.get_sample_data(camera, box_vis_level=BoxVisibility.ANY, selected_anntokens=[annotation_token])
  return len(boxes) > 0

 
def convert_camera(cam_position, cam_heading, obj_point):
    cam_x, cam_y, _ = cam_position
    obj_x, obj_y, _ = obj_point
    
    subtract_x = obj_x - cam_x
    subtract_y = obj_y - cam_y

    subtract_mag = np.sqrt(subtract_x**2 + subtract_y**2)

    res_x = subtract_mag * np.cos(-cam_heading + np.arctan2(subtract_y, subtract_x))
    res_y = subtract_mag * np.sin(-cam_heading + np.arctan2(subtract_y, subtract_x))

    return res_x, res_y

# Used to debug why fig15 killed
def print_mem_usage():
  process = psutil.Process(os.getpid())
  print(process.memory_info().rss, end="\r", flush=True) 


CAM_DIRECTIONS = ["CAM_FRONT", "CAM_FRONT_LEFT", "CAM_FRONT_RIGHT"]

with open("../../../data/evaluation/video-samples/boston-seaport.txt", 'r') as f:
    sceneNumbers = f.readlines()
    sceneNumbers = [x.strip() for x in sceneNumbers]
    # sceneNumbers = sceneNumbers[0:80]

####################### Figure 12 #######################
# world = world.filter(
#     F.like(o.type, lit('human.pedestrian%')) &
#     F.contained(c.ego, 'road') &
#     (F.contained_margin(o.bbox@c.time, F.road_segment('road'), lit(0.50)) | F.contained(o.trans@c.time, 'road')) &
#     F.angle_excluding(F.facing_relative(o.traj@c.time, c.ego), lit(-70), lit(70)) &
#     F.angle_between(F.facing_relative(c.ego, c.roadDirection), lit(-15), lit(15)) &
#     (F.distance(c.camAbs, o.traj@c.time) < lit(50)) &
#     (F.view_angle(o.trans@c.time, c.camAbs) < lit(35))
# )

 
# ego = Car on drivableRoad,
#         facing Range(-15, 15) deg relative to roadDirection,
#         with visibleDistance 50, 
#         with viewAngle 135 deg
# ped = Pedestrian on roadsOrIntersections,
#         with regionContainedIn roadRegion,
#         facing Range(-180, 180) deg

# require abs(relative heading of ped from ego) > 70 deg

 
### Devkit Plan
# 1. Get all instances of Egos
#     - such that on road (prob not needed)
#     - such that facing Range(-15, 15) relative to roadDirection
# 2. Geet all instances of pedestrians wrt egos
#     - such that withitn 50 meters of ego
#     - such that on road
#     - such that visibile from ego (viewAngle if needed)

 
## Get all possible pedestrian + ego instances
print("Figure 12")

start_fig12 = time.time()

instances = []
for sample in nusc.sample:
  scene = nusc.get('scene', sample['scene_token'])
  sceneNumber = scene["name"][6:10]
  if sceneNumber not in sceneNumbers:
    continue
  log = nusc.get('log', scene['log_token'])
  if log['location'] == 'boston-seaport':
    for annotation in sample['anns']:
      annotation_metadata = nusc.get('sample_annotation', annotation)
      if annotation_metadata['category_name'] == 'human.pedestrian.adult':
        CAM_FRONT_SENSOR = sample['data']['CAM_FRONT']
        sample_data = nusc.get('sample_data', CAM_FRONT_SENSOR)
        ego_pose_token = sample_data['ego_pose_token']
        for CAM_DIRECTION in CAM_DIRECTIONS:
          instances.append(Instance(timestamp=sample_data['timestamp'], cam_direction=CAM_DIRECTION, sample_record=sample, annotation_token=annotation, ego_pose_token=ego_pose_token))
len(instances)

 
# Filter for pedestrians that are within 50 meters of the ego
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation = nusc.get('sample_annotation', instance.annotation_token)

  ped_trans = np.array(annotation['translation'])
  ego_trans = np.array(ego_pose['translation'])
  distance = np.linalg.norm(ped_trans - ego_trans)
 
  if distance < 50:
    new_instances.append(instance)
instances = new_instances
len(instances)
 

 ## require abs(relative heading of ped from ego) > 70 deg
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation = nusc.get('sample_annotation', instance.annotation_token)

  ped_trans = np.array(annotation['translation'])
  ego_trans = np.array(ego_pose['translation'])

  camera_token = instance.sample_record['data'][instance.cam_direction]
  camera_data = nusc.get('sample_data', camera_token)
  cal_sensor = nusc.get('calibrated_sensor', camera_data['calibrated_sensor_token'])

  cam_heading = get_camera_heading(ego_rotation=ego_pose['rotation'], cam_rotation=cal_sensor['rotation'])
  ped_heading = get_heading(annotation['rotation'])
  if abs(normalizeAngle(ped_heading - cam_heading)) > math.radians(70):
    new_instances.append(instance)
instances = new_instances
len(instances)


## Filter so that pedestrian is visible from ego
new_instances = []
for instance in instances:
  ped_visible = is_visible(sample_record=instance.sample_record, annotation_token=instance.annotation_token, cam_direction=instance.cam_direction)
  annotation = nusc.get('sample_annotation', instance.annotation_token)
  
  if ped_visible:
    new_instances.append(instance)
instances = new_instances
len(instances)


## Filter so that for pedestrians that are in an intersection
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation = nusc.get('sample_annotation', instance.annotation_token)

  ped_trans = np.array(annotation['translation'])
  ego_trans = np.array(ego_pose['translation'])
  
  if is_contained_intersection(ped_trans):
    new_instances.append(instance)
instances = new_instances
len(instances)

# ## Filter so that all egos are in a lane
# new_instances = []
# for instance in instances:
#   ego_pose = nusc.get('ego_pose', instance.ego_pose_token)

#   ego_trans = np.array(ego_pose['translation'])
#   if is_contained(ego_trans, "lane"):
#     new_instances.append(instance)
# instances = new_instances
# len(instances)
 
# ## Filter for egos whos heading is aligned with the road direction
# new_instances = []
# for instance in instances:
#   ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
#   annotation = nusc.get('sample_annotation', instance.annotation_token)

#   ped_trans = np.array(annotation['translation'])
#   ego_trans = np.array(ego_pose['translation'])
  
#   ego_heading = get_heading(ego_pose['rotation'])
#   road_direction = get_road_direction(ego_trans)
#   if road_direction == None:
#     new_instances.append(instance)
#   elif normalizeAngle(abs(ego_heading - road_direction)) < math.radians(15) \
#     and math.radians(-15) < normalizeAngle(abs(ego_heading - road_direction)):
#     new_instances.append(instance)
# instances = new_instances
# len(instances)

end_fig12 = time.time()
print("Figure 12 time: ", format(end_fig12-start_fig12))
 
results = {}
for instance in instances:
  camera_token = instance.sample_record['data'][instance.cam_direction]
  camera_data = nusc.get('sample_data', camera_token)
  results[camera_data['token']] = camera_data['filename']

with open('fig12_results.txt', 'w') as f:
    for line in results.values():
        f.write(f"{line}\n")

####################### Figure 13 #######################

# ego = Car on drivableRoad,
#         facing Range(-15, 15) deg relative to roadDirection,
#         with visibleDistance 50,
#         with viewAngle 135 deg

# other1 = Car on intersection,
#             facing Range(50, 135) deg relative to ego.heading

# other2 = Car on intersection,
#             facing -1 * Range(50, 135) deg relative to ego.heading

# require abs(relative heading of other1 from other2) > 100 deg
# require (distance from ego to intersectionRegion) < 10

 
# world = world.filter(
#     (obj1.id != obj2.id) &
#     F.like(obj1.type, 'vehicle%') &
#     F.like(obj2.type, 'vehicle%') &
#     F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -15, 15) &
#     (F.distance(cam.ego, obj1.trans@cam.time) < 50) &
#     (F.view_angle(obj1.trans@cam.time, cam.ego) < 70 / 2.0) &
#     (F.distance(cam.ego, obj2.trans@cam.time) < 50) &
#     (F.view_angle(obj2.trans@cam.time, cam.ego) < 70 / 2.0) &
#     F.contains_all('intersection', [obj1.trans, obj2.trans]@cam.time) &
#     F.angle_between(F.facing_relative(obj1.trans@cam.time, cam.ego), 50, 135) &
#     F.angle_between(F.facing_relative(obj2.trans@cam.time, cam.ego), -135, -50) &
#     (F.min_distance(cam.ego, F.road_segment('intersection')) < 10) &
#     F.angle_between(F.facing_relative(obj1.trans@cam.time, obj2.trans@cam.time), 100, -100)
# )

 
## Get all possible car1 + car2 instances
print("Figure 13")

start_fig13 = time.time()

instances = []
for sample in nusc.sample:
  scene = nusc.get('scene', sample['scene_token'])
  sceneNumber = scene["name"][6:10]
  if sceneNumber not in sceneNumbers:
    continue
  log = nusc.get('log', scene['log_token'])
  if log['location'] == 'boston-seaport':
    if log['location'] == 'boston-seaport':
      for annotation1 in sample['anns']:
        for annotation2 in sample['anns']:
          annotation_metadata1 = nusc.get('sample_annotation', annotation1)
          annotation_metadata2 = nusc.get('sample_annotation', annotation2)
          if annotation_metadata1['category_name'] == 'vehicle.car' or annotation_metadata1['category_name'] == 'vehicle.truck':
            if annotation_metadata2['category_name'] == 'vehicle.car' or annotation_metadata2['category_name'] == 'vehicle.truck':
              CAM_FRONT_SENSOR = sample['data']['CAM_FRONT']
              sample_data = nusc.get('sample_data', CAM_FRONT_SENSOR)
              ego_pose_token = sample_data['ego_pose_token']
              for CAM_DIRECTION in CAM_DIRECTIONS:
                instances.append(Instance(timestamp=sample_data['timestamp'], cam_direction=CAM_DIRECTION, sample_record=sample, annotation_token=annotation1, annotation_token2=annotation2, ego_pose_token=ego_pose_token))
len(instances)

 
## Filter for cars based on distace to ego
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation1 = nusc.get('sample_annotation', instance.annotation_token)
  annotation2 = nusc.get('sample_annotation', instance.annotation_token2)

  car1_trans = np.array(annotation1['translation'])
  car2_trans = np.array(annotation2['translation'])
  ego_trans = np.array(ego_pose['translation'])
  distance1 = np.linalg.norm(car1_trans - ego_trans)
  distance2 = np.linalg.norm(car2_trans - ego_trans)

  if distance1 < 50 and distance2 < 50:
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter for relative headings wrt to ego
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation1 = nusc.get('sample_annotation', instance.annotation_token)
  annotation2 = nusc.get('sample_annotation', instance.annotation_token2)

  car1_heading = get_heading(annotation1['rotation'])
  car2_heading = get_heading(annotation2['rotation'])
  
  diff = normalizeAngle(car1_heading - car2_heading)
  if (math.radians(-180) < diff and diff < math.radians(-90)): 
    new_instances.append(instance)
instances = new_instances
len(instances)



## Filter for egos whos heading is aligned with the road direction
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  ego_trans = np.array(ego_pose['translation'])
  
  camera_token = instance.sample_record['data'][instance.cam_direction]
  camera_data = nusc.get('sample_data', camera_token)
  cal_sensor = nusc.get('calibrated_sensor', camera_data['calibrated_sensor_token'])
  cam_heading = get_camera_heading(ego_rotation=ego_pose['rotation'], cam_rotation=cal_sensor['rotation'])  
  
  road_direction = get_road_direction(ego_trans)
  if road_direction == None:
    new_instances.append(instance)
  elif math.radians(-15) < normalizeAngle(cam_heading - road_direction) and normalizeAngle(cam_heading - road_direction) < math.radians(15):
    new_instances.append(instance)
instances = new_instances
len(instances)


## Filter so that cars are visible from ego
new_instances = []
for instance in instances:
  car1_visible = is_visible(sample_record=instance.sample_record, annotation_token=instance.annotation_token, cam_direction=instance.cam_direction)
  car2_visible = is_visible(sample_record=instance.sample_record, annotation_token=instance.annotation_token2, cam_direction=instance.cam_direction)
  if car1_visible and car2_visible:
    new_instances.append(instance)
instances = new_instances
len(instances)


## Filter so that for cars that are in an intersection
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation1 = nusc.get('sample_annotation', instance.annotation_token)
  annotation2 = nusc.get('sample_annotation', instance.annotation_token2)

  car1_trans = np.array(annotation1['translation'])
  car2_trans = np.array(annotation2['translation'])
  ego_trans = np.array(ego_pose['translation'])
  
  if is_contained_intersection(car1_trans) and is_contained_intersection(car2_trans):
    new_instances.append(instance)
instances = new_instances
len(instances)


end_fig13 = time.time()
print("Figure 13 time: ", format(end_fig13-start_fig13))
 
results = {}
for instance in instances:
  camera_token = instance.sample_record['data'][instance.cam_direction]
  camera_data = nusc.get('sample_data', camera_token)
  results[camera_data['token']] = camera_data['filename'] # .split('/')[2]

with open('fig13_results.txt', 'w') as f:
    for line in results.values():
        f.write(f"{line}\n")


 
################# Figure 14 #################

# ego = Car on drivableRoad,
#         facing offset relative to roadDirection,
#         with visibleDistance 50,
#         with viewAngle 135 deg

# otherCar = Car on visible road,
#             facing Range(-15, 15) deg relative to roadDirection

# require (distance from ego to otherCar) < 10

 
# world = world.filter("lambda obj1, cam: " + 
#         "F.like(obj1.object_type, 'vehicle%') and " +
#         "F.distance(cam.ego, obj1, cam.timestamp) < 50 and " +
#         "F.view_angle(obj1, cam.ego, cam.timestamp) < 70 / 2 and " +
#         "F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.timestamp, cam.ego), cam.timestamp), -180, -90) and " +
#         "F.contained(cam.ego, F.road_segment('road')) and " +
#         "F.contained(obj1.traj, F.road_segment('road'), cam.timestamp) and " +
#         "F.angle_between(F.facing_relative(obj1, F.road_direction(obj1.traj, cam.timestamp, cam.ego), cam.timestamp), -15, 15) and " +
#         "F.distance(cam.ego, obj1, cam.timestamp) < 10"
# )

 
## Get all possible car + ego instances
print("Figure 14")

start_fig14 = time.time()

instances = []
for sample in nusc.sample:
  scene = nusc.get('scene', sample['scene_token'])
  sceneNumber = scene["name"][6:10]
  if sceneNumber not in sceneNumbers:
    continue
  log = nusc.get('log', scene['log_token'])
  if log['location'] == 'boston-seaport':
    for annotation in sample['anns']:
      annotation_metadata = nusc.get('sample_annotation', annotation)
      if annotation_metadata['category_name'] == 'vehicle.car' or annotation_metadata['category_name'] == 'vehicle.truck':
        CAM_FRONT_SENSOR = sample['data']['CAM_FRONT']
        sample_data = nusc.get('sample_data', CAM_FRONT_SENSOR)
        ego_pose_token = sample_data['ego_pose_token']
        for CAM_DIRECTION in CAM_DIRECTIONS:
          instances.append(Instance(timestamp=sample_data['timestamp'], cam_direction=CAM_DIRECTION, sample_record=sample, annotation_token=annotation, ego_pose_token=ego_pose_token))
len(instances)

 
## Filter for cars  that are within 10 meters of the ego
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation1 = nusc.get('sample_annotation', instance.annotation_token)

  car1_trans = np.array(annotation1['translation'])
  ego_trans = np.array(ego_pose['translation'])
  distance1 = np.linalg.norm(car1_trans - ego_trans)

  if distance1 < 10:
    new_instances.append(instance)
instances = new_instances
len(instances)

## Filter for cars whos heading is aligned with the road direction
new_instances = []
for instance in instances:
  annotation = nusc.get('sample_annotation', instance.annotation_token)

  car_trans = np.array(annotation['translation'])  
  
  car_heading = get_heading(annotation['rotation'])
  road_direction = get_road_direction(car_trans)
  if road_direction == None:
    new_instances.append(instance)
  elif math.radians(-15) < normalizeAngle(car_heading - road_direction) and normalizeAngle(car_heading - road_direction) < math.radians(15):
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter for egos who are moving in opposite direction
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation = nusc.get('sample_annotation', instance.annotation_token)
  
  ego_trans = np.array(ego_pose['translation'])

  road_direction = get_road_direction(ego_trans)
  camera_token = instance.sample_record['data'][instance.cam_direction]
  camera_data = nusc.get('sample_data', camera_token)
  cal_sensor = nusc.get('calibrated_sensor', camera_data['calibrated_sensor_token'])
  cam_heading = get_camera_heading(ego_rotation=ego_pose['rotation'], cam_rotation=cal_sensor['rotation'])  
  if road_direction == None:
    # In this case, we do not keep the instance, since a return value of None means
    # that the current road direction is to be interpreted as the egoHeading
    # new_instances.append(instance)
    continue
  diff = normalizeAngle(cam_heading - road_direction) 
  if (math.radians(135) < diff and diff < math.radians(225)) or (math.radians(-180) < diff and diff < math.radians(-135)):
    new_instances.append(instance)
instances = new_instances
len(instances)

## Filter so that cars are visible from ego
new_instances = []
for instance in instances:
  car1_visible = is_visible(sample_record=instance.sample_record, annotation_token=instance.annotation_token, cam_direction=instance.cam_direction)
  if car1_visible:
    new_instances.append(instance)
instances = new_instances
len(instances)


## Filter so that all egos and cars are in a lane
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation1 = nusc.get('sample_annotation', instance.annotation_token)
  car1_trans = np.array(annotation1['translation'])


  ego_trans = np.array(ego_pose['translation'])
  if is_contained(ego_trans, "lane") and is_contained(car1_trans, "lane"):
    new_instances.append(instance)
instances = new_instances
len(instances)


end_fig14 = time.time()
print("Figure 14 time: ", format(end_fig14-start_fig14))
 
results = {}
for instance in instances:
  camera_token = instance.sample_record['data'][instance.cam_direction]
  camera_data = nusc.get('sample_data', camera_token)
  results[camera_data['token']] = camera_data['filename'] #.split('/')[2]

 
with open('fig14_results.txt', 'w') as f:
    for line in results.values():
        f.write(f"{line}\n")
 
 

############### Figure 15 ###############

# ego = Car on drivableRoad,
#         facing Range(-15, 15) deg relative to roadDirection,
#         with visibleDistance 50,
#         with viewAngle 135 deg

# point1 = OrientedPoint ahead of ego by Range(0, 40)
# Car at (point1 offset by Range(-1, 1) @ 0),
#     facing Range(-15, 15) deg relative to roadDirection

 
# world = world.filter(
#     (F.like(car1.type, 'car') | F.like(car1.type, 'truck')) &
#     (F.like(car2.type, 'car') | F.like(car2.type, 'truck')) &
#     (F.like(opposite_car.type, 'car') | F.like(opposite_car.type, 'truck')) &
#     (opposite_car.id != car2.id) &
#     (car1.id != car2.id) &
#     (car1.id != opposite_car.id) &

#     F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -15, 15) &
#     (F.view_angle(car1.traj@cam.time, cam.ego) < 70 / 2) &
#     (F.distance(cam.ego, car1.traj@cam.time) < 50) &
# #     F.angle_between(F.facing_relative(car1.traj@cam.time, cam.ego), -15, 15) &
# #     F.angle_between(F.facing_relative(car1.traj@cam.time, F.road_direction(car1.traj@cam.time, cam.ego)), -15, 15) &
#     F.ahead(car1.traj@cam.time, cam.ego) &
#     F.angle_between(F.facing_relative(cam.ego, F.road_direction(cam.ego, cam.ego)), -15, 15) &
#     (F.convert_camera(opposite_car.traj@cam.time, cam.ego) > [-10, 0]) &
#     (F.convert_camera(opposite_car.traj@cam.time, cam.ego) < [-1, 50]) &
#     F.angle_between(F.facing_relative(opposite_car.traj@cam.time, cam.ego), 140, 180) &
#     (F.distance(opposite_car@cam.time, car2@cam.time) < 40) &
# #     F.angle_between(F.facing_relative(car2.traj@cam.time, F.road_direction(car2.traj@cam.time, cam.ego)), -15, 15) &
#     F.ahead(car2.traj@cam.time, opposite_car.traj@cam.time)
# )

 
## Get all possible car + car + car + ego instances
print("Figure 15")

start_fig15 = time.time()

instances = []
for sample in nusc.sample:
  scene = nusc.get('scene', sample['scene_token'])
  sceneNumber = scene["name"][6:10]
  if sceneNumber not in sceneNumbers:
    continue
  log = nusc.get('log', scene['log_token'])
  if log['location'] == 'boston-seaport':
    for annotation1 in sample['anns']:
      for annotation2 in sample['anns']:
        for annotation3 in sample['anns']:
          annotation1_metadata = nusc.get('sample_annotation', annotation1)
          annotation2_metadata = nusc.get('sample_annotation', annotation2)
          annotation3_metadata = nusc.get('sample_annotation', annotation3)
          if annotation1 != annotation2 and annotation2 != annotation3 and annotation1 != annotation3:
            if (annotation1_metadata['category_name'] == 'vehicle.car' or annotation1_metadata['category_name'] == 'vehicle.truck') \
              and (annotation2_metadata['category_name'] == 'vehicle.car' or annotation2_metadata['category_name'] == 'vehicle.truck') \
              and (annotation3_metadata['category_name'] == 'vehicle.car' or annotation3_metadata['category_name'] == 'vehicle.truck'):
              CAM_FRONT_SENSOR = sample['data']['CAM_FRONT']
              sample_data = nusc.get('sample_data', CAM_FRONT_SENSOR)
              ego_pose_token = sample_data['ego_pose_token']
              for CAM_DIRECTION in CAM_DIRECTIONS:
                instances.append(Instance(timestamp=sample_data['timestamp'], cam_direction=CAM_DIRECTION, sample_record=sample, annotation_token=annotation1, ego_pose_token=ego_pose_token, annotation_token2=annotation2, annotation_token3=annotation3))
len(instances)

 
## Filter for distances
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation1 = nusc.get('sample_annotation', instance.annotation_token)
  annotation2 = nusc.get('sample_annotation', instance.annotation_token2)
  annotation3 = nusc.get('sample_annotation', instance.annotation_token3)

  oppposite_car_trans = np.array(annotation3['translation'])
  car_2_trans = np.array(annotation2['translation'])
  car_1_trans = np.array(annotation1['translation'])
  ego_trans = np.array(ego_pose['translation'])
  distance1 = np.linalg.norm(oppposite_car_trans - car_2_trans)
  distance2 = np.linalg.norm(car_1_trans - ego_trans)

  if distance1 < 40 and distance2 < 50:
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter so that car 1s are visible from ego
new_instances = []
for instance in instances:
  car1_visible = is_visible(sample_record=instance.sample_record, annotation_token=instance.annotation_token, cam_direction=instance.cam_direction)
  car2_visible = is_visible(sample_record=instance.sample_record, annotation_token=instance.annotation_token2, cam_direction=instance.cam_direction)
  car3_visible = is_visible(sample_record=instance.sample_record, annotation_token=instance.annotation_token3, cam_direction=instance.cam_direction)

  if car1_visible and car2_visible and car3_visible:
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter so that car1s that are ahead of ego
new_instances = []
for instance in instances:
  # convert_camera(cam_position, cam_heading, obj_point)
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation1 = nusc.get('sample_annotation', instance.annotation_token)
  car_1_trans = np.array(annotation1['translation'])
  ego_trans = np.array(ego_pose['translation'])
  ego_heading = get_heading(ego_pose['rotation'])
  
  conv_x, conv_y = convert_camera(ego_trans, ego_heading, car_1_trans)
  if conv_y > 0:
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter so that car2s that are ahead of opposite_car
new_instances = []
for instance in instances:
  # convert_camera(cam_position, cam_heading, obj_point)
  annotation2 = nusc.get('sample_annotation', instance.annotation_token2)
  annotation3 = nusc.get('sample_annotation', instance.annotation_token3)
  car_2_trans = np.array(annotation2['translation'])
  opposite_car_trans = np.array(annotation3['translation'])
  opposite_car_heading = get_heading(annotation3['rotation'])
  
  conv_x, conv_y = convert_camera(opposite_car_trans, opposite_car_heading, car_2_trans)
  if conv_y > 0:
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter for convertCameras
new_instances = []
for instance in instances:
  # convert_camera(cam_position, cam_heading, obj_point)
  annotation3 = nusc.get('sample_annotation', instance.annotation_token3)

  opposite_car_trans = np.array(annotation3['translation'])
  opposite_car_heading = get_heading(annotation3['rotation'])
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  ego_trans = np.array(ego_pose['translation'])
  ego_heading = get_heading(ego_pose['rotation'])
  
  conv_x, conv_y = convert_camera(ego_trans, ego_heading, opposite_car_trans)
  # print(conv_x, conv_y)
  if 1 < conv_y and conv_y < 10 and 0 < conv_x and conv_x < 50:
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter for egos whos heading is aligned with the road direction
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation = nusc.get('sample_annotation', instance.annotation_token)

  ped_trans = np.array(annotation['translation'])
  ego_trans = np.array(ego_pose['translation'])
  
  ego_heading = get_heading(ego_pose['rotation'])
  road_direction = get_road_direction(ego_trans)
  if road_direction == None:
    new_instances.append(instance)
  elif normalizeAngle(abs(ego_heading - road_direction)) < math.radians(15):
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter for car1 heading is aligned with the road direction
new_instances = []
for instance in instances:
  annotation = nusc.get('sample_annotation', instance.annotation_token)

  car_trans = np.array(annotation['translation'])
  
  car_heading = get_heading(annotation['rotation'])
  road_direction = get_road_direction(ego_trans)
  if road_direction == None:
    new_instances.append(instance)
  elif normalizeAngle(abs(car_heading - road_direction)) < math.radians(15):
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter for car2 heading is aligned with the road direction
new_instances = []
for instance in instances:
  annotation2 = nusc.get('sample_annotation', instance.annotation_token2)

  car_trans = np.array(annotation2['translation'])
  
  car_heading = get_heading(annotation2['rotation'])
  road_direction = get_road_direction(ego_trans)
  if road_direction == None:
    new_instances.append(instance)
  elif normalizeAngle(abs(car_heading - road_direction)) < math.radians(15):
    new_instances.append(instance)
instances = new_instances
len(instances)

 
## Filter for ego and opposite car headings
new_instances = []
for instance in instances:
  ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
  annotation3 = nusc.get('sample_annotation', instance.annotation_token3)
  
  ego_heading = get_heading(ego_pose['rotation'])
  opposite_car_heading = get_heading(annotation3['rotation'])
  if math.radians(140) < abs(normalizeAngle(ego_heading - opposite_car_heading)) and abs(normalizeAngle(ego_heading - opposite_car_heading)) < math.radians(180):
    new_instances.append(instance)
instances = new_instances
len(instances)

 
# for instance in instances:
#   camera_token = instance.sample_record['data']['CAM_FRONT']
#   camera_data = nusc.get('sample_data', camera_token) 
#   ego_pose = nusc.get('ego_pose', instance.ego_pose_token)
#   annotation1 = nusc.get('sample_annotation', instance.annotation_token)
#   annotation2 = nusc.get('sample_annotation', instance.annotation_token2)
#   annotation3 = nusc.get('sample_annotation', instance.annotation_token3)

#   oppposite_car_trans = np.array(annotation3['translation'])
#   car_2_trans = np.array(annotation2['translation'])
#   car_1_trans = np.array(annotation1['translation'])
#   ego_trans = np.array(ego_pose['translation'])
#   distance1 = np.linalg.norm(oppposite_car_trans - car_2_trans)
#   distance2 = np.linalg.norm(car_1_trans - ego_trans)
#   if camera_data['filename'] == "samples/CAM_FRONT/n008-2018-07-26-12-13-50-0400__CAM_FRONT__1532621915112404.jpg":
#     print(distance1, distance2)

end_fig15 = time.time()
print("Figure 15 time: ", format(end_fig15-start_fig15))
 
results = {}
for instance in instances:
  camera_token = instance.sample_record['data'][instance.cam_direction]
  camera_data = nusc.get('sample_data', camera_token)
  results[camera_data['token']] = camera_data['filename'] #.split('/')[2]

 
with open('fig15_results.txt', 'w') as f:
    for line in results.values():
        f.write(f"{line}\n")