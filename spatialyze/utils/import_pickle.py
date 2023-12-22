import os
import pickle

from spatialyze.database import Database
from spatialyze.geospatial_video import _camera_config


def import_pickle(database: "Database", data_path: str):
    with open(os.path.join(data_path, "frames.pkl"), "rb") as f:
        data_frames = pickle.loads(f.read())

    with open(
        "/work/apperception/shared/spatialyze-yousef/data/evaluation/video-samples/boston-seaport.txt",
        "r",
    ) as f:
        sceneNumbers = f.readlines()
        sceneNumbers = [x.strip() for x in sceneNumbers]
        sceneNumbers = sceneNumbers[0:150]

    database.reset(True)
    for scene, val in data_frames.items():
        sceneNumber = scene[6:10]
        if val["location"] == "boston-seaport" and sceneNumber in sceneNumbers:
            configs = [*map(_camera_config, val["frames"])]
            database.insert_camera(configs)

    database._commit()
