from spatialyze.world import World
from spatialyze.utils.F import distance, contains, heading_diff, has_types, road_segment, road_direction, min_distance
from spatialyze.predicate import lit

def perpendicular(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[90-margin, 90+margin]) | heading_diff(obj1, obj2, between=[270-margin, 270+margin])

def opposite(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[180-margin, 180+margin])

def sameDirection(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[0-margin, 0+margin])


def fig13():
    """
    Two vehicles in an intersection, travelling perpendicular to the ego.

    It was unclear how to implement viewAngle of 135 deg for a car, so I simplified it and combined
        with the view_angle range of 50-135 degrees between the car and ego.heading.
    """

    world = World()
    camera = world.camera()
    car1 = world.object()
    car2 = world.object()
    

    world.filter(
        has_types(car1, 'car') &
        has_types(car2, 'car') &

        heading_diff(camera.cam, road_direction(camera.ego), between=[-15, 15]) &
        (distance(camera.cam, car1) < lit(50)) &
        (distance(camera.cam, car2) < lit(50)) &

        contains('intersection', [car1, car2]) &
        heading_diff(car1, camera.cam, between=[50, 135]) &
        heading_diff(car2, camera.cam, between=[-135, -50]) &

        opposite(car1, car2) &
        (min_distance(camera.cam, road_segment('intersection')) < lit(10))
    )