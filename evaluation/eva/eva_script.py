import sys
import shutil
import os
import time
import warnings
import pickle
from pathlib import Path

import shutup;
import evadb
import pandas as pd
import torch
torch.cuda.empty_cache()

shutup.please()
warnings.filterwarnings("ignore", category=DeprecationWarning) 
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from spatialyze.database import database

EVA = ROOT / "evaluation" / "eva"
VIDEO_PATH = "/home/chanwutk/data/processed/videos/"


def delete_db():
    try:
        shutil.rmtree(os.path.join(EVA, "evadb_data"), ignore_errors=True)
    except Exception:
        print("Dir does not exist")
    print("deleting db")


def create_udf(cursor, name: str, impl: str):
    cursor.query(f"DROP UDF IF EXISTS {name}").df()
    cursor.query(f"CREATE UDF IF NOT EXISTS {name} IMPL'{str(EVA)}/udfs/{impl}.py';").df()


def setup_udfs():
    cursor = evadb.connect().cursor()
    print("setting up udfs")
    ### Set up Yolo UDF
    cursor.query("DROP UDF IF EXISTS Yolo").df()
    cursor.query("""
            CREATE UDF IF NOT EXISTS Yolo
            TYPE  ultralytics
            'model' 'yolov5s.pt';
    """).df() 

    ### Set up Monodepth UDF
    create_udf(cursor, "MonodepthDetection", "monodepth_detection")

    ### Set up Location UDF
    create_udf(cursor, "LocationDetection", "location_detection")

    for i in [1, 2, 3, 4]:
        ### Set up Qi Query UDF
        create_udf(cursor, f"QE{i}", f"QE{i}")

    ### Set up SameVideo UDF
    create_udf(cursor, "SameVideo", "same_video")

def load_data(sceneNumbers):
    cursor = evadb.connect().cursor()
    print("loading data")
    # Certain attributes are made TEXTs due to issues Eva has with negative numbers
    cursor.query("DROP TABLE IF EXISTS CameraConfigs;").df()
    cursor.create_table("CameraConfigs", if_not_exists=True, columns="""
                cameraid TEXT(15),
                framenum INTEGER,
                cameratranslation NDARRAY FLOAT32(ANYDIM),
                camerarotation TEXT(100),
                cameraintrinsic NDARRAY FLOAT32(ANYDIM),
                egoheading TEXT(15),
                filename TEXT(30)
            """).df()

    ### Load Data
    cursor.query("DROP TABLE IF EXISTS ObjectDetectionVideos;").df()
    for sceneNumber in sceneNumbers:
        sceneNumber = sceneNumber.strip()
        # Load videos
        video_name = f"boston-seaport-scene-{sceneNumber}-CAM_FRONT_LEFT.mp4"
        camera_name = f"boston-seaport-scene-{sceneNumber}-CAM_FRONT_LEFT.pkl"
        scene = f"scene-{sceneNumber}-CAM_FRONT_LEFT"
        cursor.load(file_regex=VIDEO_PATH + video_name, format="VIDEO", table_name='ObjectDetectionVideos').df()

        # Add camera configs
        result = database.execute(f"SELECT cameraId, ROW_NUMBER() OVER (Order by frameNum) AS RowNumber, cameraTranslation, cameraRotation, cameraIntrinsic, egoHeading, filename FROM Cameras WHERE cameraId = '{scene}'")
        with open(os.path.join(VIDEO_PATH, camera_name), 'rb') as f:
            result = pickle.load(f)['frames']
        df = pd.DataFrame()
        for r in result:
            # cameraId, frameNum, cameraTranslation, cameraRotation, cameraIntrinsic, egoHeading, filename = r
            cameraId, frameId, frameNum, filename, cameraTranslation, cameraRotation, cameraIntrinsic, egoTranslation, egoRotation, timestamp, cameraHeading, egoHeading, location = r
            cameraTranslation = list(cameraTranslation)
            # FrameNums in Eva are zero-indexed, so we subtract one before inserting
            cursor.query(f"""INSERT INTO CameraConfigs (cameraid, framenum, cameratranslation, camerarotation, cameraintrinsic, egoheading, filename) VALUES
                                        ('{cameraId}', {frameNum - 1}, {cameraTranslation}, '{cameraRotation}', {cameraIntrinsic}, '{egoHeading}', '{filename}');""").df()


def write_times(sceneNumbers, query, time):     
    with open("eva-times.txt", 'a') as f:
        f.write(str(sceneNumbers) + " - " + query + " - " + time + "\n")
        print(str(sceneNumbers) + " - " + query + " - " + time + "\n")

def q1(cursor):
    start = time.time()
    res1 = cursor.query("""
                SELECT framenum, id, cameraid, filename, name, egoheading, cameratranslation, QE1(LocationDetection(Yolo(data), MonodepthDetection(data).depth, cameratranslation, camerarotation, cameraintrinsic), cameratranslation, egoheading).queryresult
                    FROM ObjectDetectionVideos JOIN CameraConfigs ON (id = framenum AND SameVideo(name, cameraid).issame)
    """).df()
    res1 = res1[res1["qe1.queryresult"]]    
    end = time.time()
    print("q1", format(end-start))
    return format(end-start)

def q2(cursor):
    start = time.time()
    res2 = cursor.query("""
                SELECT framenum, id, cameraid, filename, name, egoheading, cameratranslation, QE2(LocationDetection(Yolo(data), MonodepthDetection(data).depth, cameratranslation, camerarotation, cameraintrinsic), cameratranslation, egoheading).queryresult
                    FROM ObjectDetectionVideos JOIN CameraConfigs ON (id = framenum AND SameVideo(name, cameraid).issame)
    """).df()
    res2 = res2[res2["qe2.queryresult"]]
    end = time.time()
    print("q2", format(end-start))
    return format(end-start) 

def q3(cursor):
    start = time.time()
    res3 = cursor.query("""
                SELECT framenum, id, cameraid, filename, name, egoheading, cameratranslation, QE3(LocationDetection(Yolo(data), MonodepthDetection(data).depth, cameratranslation, camerarotation, cameraintrinsic), cameratranslation, egoheading).queryresult
                    FROM ObjectDetectionVideos JOIN CameraConfigs ON (id = framenum AND SameVideo(name, cameraid).issame)
    """).df()
    res3 = res3[res3["qe3.queryresult"]]
    end = time.time()
    print("q3", format(end-start))
    return format(end-start)

def q4(cursor):
    start = time.time()
    res4 = cursor.query("""
                SELECT framenum, id, cameraid, filename, name, egoheading, cameratranslation, QE4(LocationDetection(Yolo(data), MonodepthDetection(data).depth, cameratranslation, camerarotation, cameraintrinsic), cameratranslation, egoheading).queryresult
                    FROM ObjectDetectionVideos JOIN CameraConfigs ON (id = framenum AND SameVideo(name, cameraid).issame)
    """).df()
    res4= res4[res4["qe4.queryresult"]]
    end = time.time()
    print("q4", format(end-start))
    return format(end-start)


with open("eva-times.txt", 'w') as f:
        f.write("\n")

with open("scene-names.txt", 'r') as f:
    sceneNumbers = f.readlines()
    sceneNumbers = [x.strip() for x in sceneNumbers]

bsize = 10
while len(sceneNumbers) > 0:
    if len(sceneNumbers) > bsize:
        currentScenes = sceneNumbers[:bsize]
        sceneNumbers = sceneNumbers[bsize:]
    else:
        currentScenes = sceneNumbers
        sceneNumbers = []

    # currentScenes = [sceneNumbers.pop()]
    # if len(sceneNumbers) > 0:
    #     currentScenes.append(sceneNumbers.pop())

    delete_db()
    setup_udfs()
    load_data(currentScenes)
    cursor = evadb.connect().cursor()
    cursor._evadb.config.update_value("executor", "batch_mem_size", 300000)
    cursor._evadb.config.update_value("executor", "gpu_ids", [0])
    q3_time = q3(cursor)
    q4_time = q4(cursor)
    write_times(currentScenes, "q4", q4_time)

    delete_db()
    setup_udfs()
    load_data(currentScenes)
    cursor = evadb.connect().cursor()
    cursor._evadb.config.update_value("executor", "batch_mem_size", 300000)
    cursor._evadb.config.update_value("executor", "gpu_ids", [0])
    q4_time = q4(cursor)
    q1_time = q1(cursor)
    write_times(currentScenes, "q1", q1_time)

    delete_db()
    setup_udfs()
    load_data(currentScenes)
    cursor = evadb.connect().cursor()
    cursor._evadb.config.update_value("executor", "batch_mem_size", 300000)
    cursor._evadb.config.update_value("executor", "gpu_ids", [0])
    q1_time = q1(cursor)
    q2_time = q2(cursor)
    write_times(currentScenes, "q2", q2_time)

    delete_db()
    setup_udfs()
    load_data(currentScenes)
    cursor = evadb.connect().cursor()
    cursor._evadb.config.update_value("executor", "batch_mem_size", 300000)
    cursor._evadb.config.update_value("executor", "gpu_ids", [0])
    q2_time = q2(cursor)
    q3_time = q3(cursor)
    write_times(currentScenes, "q3", q3_time)


