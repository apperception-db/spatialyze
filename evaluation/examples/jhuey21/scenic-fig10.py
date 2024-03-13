from spatialyze.world import World
from spatialyze.utils.F import distance, contains, heading_diff, has_types, view_angle, ahead
from spatialyze.predicate import lit

def sameDirection(obj1, obj2, margin=20):
    return heading_diff(obj1, obj2, between=[0-margin, 0+margin])


def fig10():
    """
    Simulates bumper to bumper traffic with two lanes of cars and a bike lane.

    Figure 10 and Figure 11 of the Scenic program is for a scalability experiment. To scale the number of cars, I would
        move the ahead() and sameDirection() predicates into a loop. 
    In future examples, we see contains('intersection', obj). In the implementation of contains, it looks like
        a specific set of ROAD_TYPES are accepted. Specifying a single intersection here rather than passing an 
        intersection object is understandable, as there are unlikely to be multiple intersections in the scene. 
        However, this logic cannot be applied to multi-lane traffic. 
        If this isn't already implemented, it may be helpful to allow `contains` and other functions to
        accept objects that can differentiate between multiple instances of a single type (ie. left lane, right lane, etc)
    """
    world = World()

    numCars = 2

    camera = world.camera()
    objects = {}

    for i in range(numCars):
        car = world.object()
        leftCar = world.object()
        rightBike = world.object()
        objects[i] = {'car': car, 'leftCar': leftCar, 'rightBike': rightBike}

        world.filter(
            has_types(objects[i]['car'], 'car') &
            has_types(objects[i]['leftCar'], 'car') &
            has_types(objects[i]['rightBike'], 'bike') &

            (view_angle(camera.cam, objects[i]['rightBike']) < lit(10))
        )

    lane = world.geogConstruct(type='lane') 
    leftLane = world.geogConstruct(type='lane')
    rightLane = world.geogConstruct(type='lane')

    world.filter(
        contains(lane, [camera.cam, objects[0]['car'], objects[1]['car']]) &
        contains(leftLane, [objects[0]['leftCar'], objects[1]['leftCar']]) &
        contains(rightLane, [objects[0]['rightBike'], objects[1]['rightBike']]) &

        ahead(objects[1]['car'], objects[0]['car']) &
        ahead(objects[0]['car'], camera.cam) &

        ahead(objects[1]['leftCar'], objects[0]['leftCar']) &
        ahead(objects[1]['rightBike'], objects[0]['rightBike']) &

        sameDirection(camera.cam, objects[0]['car'], objects[0]['leftCar'], objects[1]['car'], objects[1]['leftCar'])

        (distance(camera.cam, objects[0]['car']) < 5) &
        (distance(objects[0]['car'], objects[1]['car']) < 5) &

        (distance(camera.cam, objects[numCars - 1]['leftCar']) < 200) &
        (distance(camera.cam, objects[numCars - 1]['rightBike']) < 200)
    )
