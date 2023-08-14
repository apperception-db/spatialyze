from spatialyze.utils.ingest_road import ingest_road
from spatialyze.database import database

ingest_road(database, './data/scenic/road-network/boston-seaport')
