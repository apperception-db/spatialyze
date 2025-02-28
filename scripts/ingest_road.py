import sys
import duckdb

from spatialyze.utils import ingest_road
from spatialyze.database import database, Database


if len(sys.argv) == 2:
    print('ingest road at ', sys.argv[1])
    database = Database(duckdb.connect(sys.argv[1]))
ingest_road(database, './data/scenic/road-network/boston-seaport')
