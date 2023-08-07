from .database import Database
from .database import database as default_database
from .geospatial_video import GeospatialVideo
from .predicate import BoolOpNode, CameraTableNode, ObjectTableNode, PredicateNode
from .road_network import RoadNetwork


class World:
    def __init__(
        self,
        database: "Database | None" = None,
        predicates: "list[PredicateNode] | None" = None,
        videos: "list[GeospatialVideo] | None" = None,
        geogConstructs: "list[RoadNetwork] | None" = None,
    ):
        self.database = database or default_database
        self.predicates = predicates or []
        self.videos = videos or []
        self.geogConstructs = geogConstructs or []
        self._objectCounts = 0
        # self._cameraCounts = 0

    def filter(self, predicate: "PredicateNode") -> "World":
        return World(self.database, self.predicates + [predicate], self.videos, self.geogConstructs)

    def addVideo(self, video: "GeospatialVideo") -> "World":
        return World(self.database, self.predicates, self.videos + [video], self.geogConstructs)

    def addGeogConstructs(self, geogConstructs: "RoadNetwork"):
        return World(self.database, self.predicates, self.videos, self.geogConstructs + [geogConstructs])

    def object(self, index: "int | None" = None):
        if index is not None:
            node = ObjectTableNode(self._objectCounts)
            self._objectCounts += 1
        else:
            node = ObjectTableNode(index)
        return node

    def camera(self):
        return CameraTableNode()

    def geogConstruct(self, type: "str"):
        pass

    def saveVideos(self, addBoundingBoxes: "bool" = False):
        objects = self._execute()
        return objects

    def getObjects(self):
        objects = self._execute()
        return objects

    def _execute(self):
        # add geospatial videos
        for v in self.videos:
            pass
        # add geographic constructs
        for gc in self.geogConstructs:
            gc.ingest(self.database)
        return self.database.predicate(BoolOpNode("and", self.predicates))
