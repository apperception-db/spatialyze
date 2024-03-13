from spatialyze.world import World
from spatialyze.utils.F import distance, contains, heading_diff, has_types, road_segment, road_direction, min_distance
from spatialyze.predicate import lit

def perpendicular(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[90-margin, 90+margin]) | heading_diff(obj1, obj2, between=[270-margin, 270+margin])

def opposite(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[180-margin, 180+margin])

def sameDirection(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[0-margin, 0+margin])


def fig14():
    """
    The ego vehicle is driving against traffic and another vehicle is visible within 10 meters.
    """

    world = World()
    camera = world.camera()
    car2 = world.object()

    world.filter(
        has_types(car2, 'car') &

        contains('road', [camera.ego, car2]) &
        heading_diff(camera.ego, road_direction(camera.ego), between=[-180, -90]) &
        heading_diff(car2, road_direction(camera.ego), between=[-15, 15]) &

        (distance(camera.ego, car2) < lit(10))
    )