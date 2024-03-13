from spatialyze.world import World
from spatialyze.utils.F import distance, heading_diff, has_types, view_angle, ahead, road_direction, contains
from spatialyze.predicate import lit

def fig15():
    """
    Four vehicles in two lane road, with two vehicles going in each direction.

    My interpretation of a Range() offset in this scenario was that the opposite car
        could be offset by some amount between -10 and -1 meters in one axis, 
        and 0 and 50 meters in the other axis.
        I did not find a direct implementation of this in S-Flow. convert_camera which might be
        the best fit for orienting the "camera ego" to Scenic's "opposite point". 
        However, it seems that convert_camera changes the heading of a camera, which 
        I understand to be the angle of the camera.
        A potentially more intuitive way to implement this would be to define a car with the same
            location as an exisiting object and then offset it relative to the camera.
    """

    world = World()

    camera = world.camera()
    point1 = world.object()
    oppositeCar = world.object()
    point2 = world.object()

    world.filter(
        has_types(point1, 'car') &
        has_types(oppositeCar, 'car') &
        has_types(point2, 'car') &

        contains('lane', camera.ego) &

        (heading_diff(camera.ego, road_direction(camera.ego), between=[-15, 15])) &
        (view_angle(camera.ego, point1) < lit(135)) &

        (distance(camera.ego, point1) < lit(40)) &
        (heading_diff(point1, road_direction(camera.ego), between=[-15, 15])) &
        (ahead(point1, camera.ego)) &

        # TODO: define a car that has the location of point1 and offset it

        (heading_diff(oppositeCar, road_direction(camera.ego), between=[140, 180])) &
        (distance(oppositeCar, point2) < lit(40)) &
        (heading_diff(point2, road_direction(camera.ego), between=[-15, 15])) &
        (ahead(point2, oppositeCar))
    )
