from spatialyze.world import World
from spatialyze.utils.F import distance, contains, heading_diff, has_types, view_angle, ahead
from spatialyze.predicate import lit

def perpendicular(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[90-margin, 90+margin]) | heading_diff(obj1, obj2, between=[270-margin, 270+margin])

def opposite(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[180-margin, 180+margin])

def sameDirection(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[0-margin, 0+margin])


def fig11():
    """
    Simulates bumper to bumper traffic with two lanes of cars and a bike lane.
    """
    
    world = World()
    camera = world.camera()
    objects = {}

    numPeds = 3
    for i in range(numPeds):
        ped = world.object()
        objects[i] = {'ped': ped}

        world.filter(
            has_types(ped, 'person') &
            heading_diff(ped, camera.cam, between=[-120, 120]) &

            (distance(camera.cam, ped) < lit(200))
        )