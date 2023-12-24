import os
import pickle

from bitarray import bitarray

from spatialyze.world import World
from spatialyze.utils.F import heading_diff
from spatialyze.geospatial_video import GeospatialVideo


VIDEO_DIR =  './data/pipeline/videos'
SCENES = ['0655', '0757']
world = World()
for scene in SCENES:
    camera_config_path = os.path.join(VIDEO_DIR, f'boston-seaport-scene-{scene}-CAM_FRONT.camera.pkl')
    with open(camera_config_path, 'rb') as f:
        camera_config = pickle.load(f)
    num_frames = len(camera_config['frames'])
    keep = bitarray(num_frames)
    keep.setall(0)
    keep[(num_frames * 1 // 2):] = 1
    world.addVideo(GeospatialVideo(
        os.path.join(VIDEO_DIR, f'boston-seaport-scene-{scene}-CAM_FRONT.mp4'),
        os.path.join(VIDEO_DIR, f'boston-seaport-scene-{scene}-CAM_FRONT.camera.pkl'),
        keep
    ))
obj = world.object()
world.filter((obj.type == 'bus') | (obj.type == 'car'))
world.filter((heading_diff(obj, obj) != -400) | True)
objects = world.saveVideos('./evaluation/examples/videos/', addBoundingBoxes=True)
