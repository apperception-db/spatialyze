from .database import Database
from .utils.ingest_road import ROAD_TYPES, add_segment_type, ingest_location


class RoadNetwork:
    def __init__(self, location: "str", road_network_dir: "str"):
        self.location = location
        self.road_network_dir = road_network_dir

    def ingest(self, database: "Database"):
        ingest_location(database, self.road_network_dir, self.location)
        add_segment_type(database, ROAD_TYPES)
        database._commit()
