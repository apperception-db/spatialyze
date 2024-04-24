from spatialyze.world import World
from spatialyze.utils.F import distance, contains, heading_diff, has_types, road_segment, road_direction, min_distance
from spatialyze.predicate import lit

def fig5a():
    """
    S-FLow does not have a way to detect all instances of a type of object and aggregate them --
        users must define an object that they want to detect and track.
        We can modify the hasTypes() function signature to allow for a single car object to be passed in and
            specify either number of cars to detect or to detect all cars.
    
    """

    world = World()
    camera = world.camera()

    # (lines 1, 2) define the object to track
    car = world.object() 
    car2 = world.object()
    car3 = world.object()
        # modify the hasTypes function to allow for multiple objects or "all detected objects"

    # (line 3) select all cars within 3 meters of each other
    world.filter(distance(car, [car2, car3]) < 3)

    # (line 4) select cars that have been stopped for >120 sec
        # modify world.py to track the time a object has been stopped (TrackingResult.timestamp)    
        # over some confidence level determined by strongsort

    # (line 5) construct matrix of all cars that have been stopped for >120 sec
        # use the ObjectTableNode.trans attribute for each car object
        # SkyQuery ToMatrix implementation divides regions using a user-configurable cell size (e.g. 10m x 10m)
        # this feature doesn't seem too useful for Spatialyze's use case, so
            # we might keep the implementation separate from world.py

    # (line 6, 7) aggregate over the matrix to determine the number of cars in each cell
        # sum over our matrix from previous step
        # need to do some extra work for the thinning step 

    # (line 8) forecast future values of each cell in matrix (parking spot)
        # still reading about this in the SkyQuery paper!
        # general concept: aggregate time series binary matrix over previous frames 
            # and predict future values


    return NotImplementedError