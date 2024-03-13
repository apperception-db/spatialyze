import pickle
import os
from pathlib import Path
from spatialyze.world import World
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.utils.F import distance, contains, heading_diff, has_types, view_angle, road_direction
from spatialyze.predicate import lit
from spatialyze.geospatial_video import GeospatialVideo
from spatialyze.road_network import RoadNetwork

def perpendicular(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[90-margin, 90+margin]) | heading_diff(obj1, obj2, between=[270-margin, 270+margin])

def opposite(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[180-margin, 180+margin])

def sameDirection(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[0-margin, 0+margin])


if __name__ == '__main__':
    """
    A pedestrian in an intersection facing nearly perpendicularly or towards the ego.

    As in other example Scenic queries, the car's visible distance is 50 which we cannot explicitly define, so we
        substitute this with a max distance to the furthest object.
    Note: I tried running this query with the provided data, but got no output after several permutations of the filter query.
    """
    path = os.getcwd()
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(path))), 'data')
    OUTPUT_DIR = os.path.join(DATA_DIR, 'pipeline/outputs')
    VIDEO_DIR = os.path.join(DATA_DIR, 'pipeline/videos')
    ROAD_DIR = os.path.join(DATA_DIR, 'scenic/road-network/boston-seaport')

    files = os.listdir(VIDEO_DIR)
    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)

    world = World()
    world.addGeogConstructs(RoadNetwork('Boston-Seaport', ROAD_DIR))

    for file in os.listdir(VIDEO_DIR):
        if not file.endswith('.camera.pkl'):
            continue

        with open(os.path.join(VIDEO_DIR, file), 'rb') as f:
            camera = pickle.load(f)
        videofile = os.path.join(VIDEO_DIR, camera['filename'])
        camera = [camera_config(*c) for c in camera['frames']]

        world.addVideo(GeospatialVideo(videofile, camera))

    camera = world.camera()
    ped = world.object()

    lane = world.geogConstruct(type='lane')
    intersection = world.geogConstruct(type='intersection')

    world.filter(
        has_types(ped, 'person') &
        (contains('lane', ped) | contains('intersection', ped)) &
        heading_diff(ped, camera.ego, between=[-70, 70]) &
        heading_diff(camera.ego, road_direction(camera.ego), between=[-15, 15]) &

        (distance(camera.ego, ped) < lit(50))
    )

    world.saveVideos(os.path.join(OUTPUT_DIR, 'q12'), addBoundingBoxes=True)