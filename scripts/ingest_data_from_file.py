

# %%
from spatialyze.database import Database, database
from spatialyze.utils import import_tables, ingest_road, import_pickle

# %%
CSV_DATA_PATH = 'data/scenic/database'
ROAD_NETWORK_DATA_PATH = '/data/processed/road-network/boston-seaport'
PICKLE_DATA_PATH = '/data/apperception-data/processed/nuscenes/full-dataset-v1.0/Mini/videos'

# %%
# ingest_road(database, ROAD_NETWORK_DATA_PATH)

# %%
import_pickle(database, PICKLE_DATA_PATH)
# import_tables(database=database, data_path=CSV_DATA_PATH)


