# %%
import os
from spatialyze.database import Database, database
from spatialyze.utils import import_tables, ingest_road

# %%
EXPERIMENT = False

# %%
suffix = "_experiment" if EXPERIMENT else ""

# %%
if 'NUSCENES_PROCESSED_ROAD' in os.environ:
    road_data = os.environ['NUSCENES_PROCESSED_ROAD'] + "/boston-old"
else:
    road_data = '/data/processed/road-network/boston-seaport'

# %%
road_data

# %%
ingest_road(database, road_data)

# %%
from spatialyze.legacy.world import empty_world
import os
import pickle
import time

start = time.time()

# %%
world = empty_world("w")

# %%
# del os.environ['NUSCENES_PROCESSED_DATA']

# %%
if 'NUSCENES_PROCESSED_DATA' in os.environ:
    base_dir = os.environ['NUSCENES_PROCESSED_DATA']
else:
    base_dir = '/data/processed/full-dataset/trainval/'
#     base_dir = '/work/apperception/data/nuScenes/full-dataset-v1.0/Trainval'
base_dir

# %%
# Or uncomment this cell
with open(os.path.join(base_dir, f'sample_data{suffix}.pkl'), "rb") as f:
    df_sample_data = pickle.loads(f.read())
with open(os.path.join(base_dir, f'annotation{suffix}.pkl'), "rb") as f:
    df_annotation = pickle.loads(f.read())

# Road network only contains boston seaport data
df_sample_data = df_sample_data[df_sample_data["location"] == "boston-seaport"]

# %%
scenes = df_sample_data['scene_name'].drop_duplicates().values.tolist()

# %%
from spatialyze.utils import df_to_camera_config
from spatialyze.data_types import Camera

with open("/home/youse/apperception/data/evaluation/video-samples/boston-seaport.txt", 'r') as f:
    sceneNumbers = f.readlines()
    sceneNumbers = [x.strip() for x in sceneNumbers]
    sceneNumbers = sceneNumbers[0:80]
    
database.reset()
for scene in scenes:
    sceneNumber = scene[6:10]
    if sceneNumber in sceneNumbers:
        print(scene, scenes[-1])
        config = df_to_camera_config(scene, df_sample_data)
        camera = Camera(config=config, id=scene)
        world <<= (camera, df_annotation)

# %%
try:
    world.get_traj_key()
except Exception:
    pass

end = time.time()
print("Ingest Data Time: ", format(end-start))

# %%
from spatialyze.utils import export_tables

# %%
export_tables(database.connection, "../data/scenic/database/")

# %%



