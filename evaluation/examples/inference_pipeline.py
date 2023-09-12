import os

from spatialyze.world import World
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.video_processor.cache import disable_cache

from spatialyze.video_processor.cache import disable_cache

disable_cache()

VIDEO_DIR =  './data/pipeline/videos'
SCENES = ['0655', '0757']
world = World()
for scene in SCENES:
    world.addVideo(GeospatialVideo(
        os.path.join(VIDEO_DIR, f'boston-seaport-scene-{scene}-CAM_FRONT.mp4'),
        os.path.join(VIDEO_DIR, f'boston-seaport-scene-{scene}-CAM_FRONT.camera.pkl')
    ))
obj = world.object()
world.filter((obj.type == 'bus') | (obj.type == 'car'))
objects = world.saveVideos('./evaluation/examples/videos/', addBoundingBoxes=True)