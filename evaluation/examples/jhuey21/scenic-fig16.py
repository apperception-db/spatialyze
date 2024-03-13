from spatialyze.world import World
from spatialyze.utils.F import distance, heading_diff, has_types, view_angle, ahead, road_direction, contains
from spatialyze.predicate import lit

def fig16():
    """
    A cut-in scenario where a car in adjacent lane ot the right cuts in front of the ego.
    """

    world = World()

    camera = world.camera()
    cutInCar = world.object()

    world.filter(
        has_types(cutInCar, 'car') &

        contains('lane', camera.ego) &

        (heading_diff(camera.ego, road_direction(camera.ego), between=[-15, 15])) &
        (heading_diff(cutInCar, road_direction(camera.ego), between=[-30, -15])) &
        (ahead(cutInCar, camera.ego))

        # TODO: define a car that has the location of camera.ego and offset it (same as fig15)

    )