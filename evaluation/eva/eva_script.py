import shutup;
shutup.please()
import sys
sys.path.append("/home/chanwutk/spatialyze")
import os
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
import torch
torch.cuda.empty_cache()
import evadb
import shutil
from spatialyze.database import database
import pandas as pd
import pickle

def delete_db():
    try:
        shutil.rmtree("/home/chanwutk/spatialyze/evaluation/eva/evadb_data", ignore_errors=True)
    except Exception:
        print("Dir does not exist")
    print("deleting db")

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
    cursor.query("DROP UDF IF EXISTS MonodepthDetection").df()
    cursor.query(""" 
            CREATE UDF IF NOT EXISTS MonodepthDetection
            IMPL'/home/chanwutk/spatialyze/evaluation/eva/udfs/monodepth_detection.py';
    """).df()

    ### Set up Location UDF
    cursor.query("DROP UDF IF EXISTS LocationDetection").df()
    cursor.query(""" 
            CREATE UDF IF NOT EXISTS LocationDetection
            IMPL'/home/chanwutk/spatialyze/evaluation/eva/udfs/location_detection.py';
    """).df()

    ### Set up Q1 Query UDF
    cursor.query("DROP UDF IF EXISTS QE1").df()
    cursor.query(""" 
            CREATE UDF IF NOT EXISTS QE1
            IMPL'/home/chanwutk/spatialyze/evaluation/eva/udfs/QE1.py';
    """).df()

    ### Set up Q2 Query UDF
    cursor.query("DROP UDF IF EXISTS QE2").df()
    cursor.query(""" 
            CREATE UDF IF NOT EXISTS QE2
            IMPL'/home/chanwutk/spatialyze/evaluation/eva/udfs/QE2.py';
    """).df()

    ### Set up Q3 Query UDF
    cursor.query("DROP UDF IF EXISTS QE3").df()
    cursor.query(""" 
            CREATE UDF IF NOT EXISTS QE3
            IMPL'/home/chanwutk/spatialyze/evaluation/eva/udfs/QE3.py';
    """).df()

    ### Set up Q4 Query UDF
    cursor.query("DROP UDF IF EXISTS QE4").df()
    cursor.query(""" 
            CREATE UDF IF NOT EXISTS QE4
            IMPL'/home/chanwutk/spatialyze/evaluation/eva/udfs/QE4.py';
    """).df()

    ### Set up SameVideo UDF
    cursor.query("DROP UDF IF EXISTS SameVideo").df()
    cursor.query(""" 
            CREATE UDF IF NOT EXISTS SameVideo
            IMPL'/home/chanwutk/spatialyze/evaluation/eva/udfs/same_video.py';
    """).df()

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
        video_path = "/home/chanwutk/data/processed/videos/"
        cursor.load(file_regex=video_path + video_name, format="VIDEO", table_name='ObjectDetectionVideos').df()

        # Add camera configs
        result = database.execute(f"SELECT cameraId, ROW_NUMBER() OVER (Order by frameNum) AS RowNumber, cameraTranslation, cameraRotation, cameraIntrinsic, egoHeading, filename FROM Cameras WHERE cameraId = '{scene}'")
        with open(os.path.join(video_path, camera_name), 'rb') as f:
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


