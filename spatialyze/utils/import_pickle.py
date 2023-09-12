import os
import pickle

from spatialyze.data_types import Camera, CameraConfig
from spatialyze.database import Database


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
            configs = [
                CameraConfig(
                    frame_id=frame[1],
                    frame_num=int(frame[2]),
                    filename=frame[3],
                    camera_translation=frame[4],
                    camera_rotation=frame[5],
                    camera_intrinsic=frame[6],
                    ego_translation=frame[7],
                    ego_rotation=frame[8],
                    timestamp=frame[9],
                    cameraHeading=frame[10],
                    egoHeading=frame[11],
                )
                for frame in val["frames"]
            ]
            camera = Camera(config=configs, id=scene)
            database.insert_cam(camera)

    database._commit()
