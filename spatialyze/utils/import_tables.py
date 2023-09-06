import os

import pandas as pd

from ..database import (
    BBOX_COLUMNS,
    CAMERA_COLUMNS,
    TRAJECTORY_COLUMNS,
    Database,
    columns,
    place_holder,
)


def import_tables(database: "Database", data_path: str):
    # Import CSV
    data_Cameras = pd.read_csv(os.path.join(data_path, "cameras.csv"))
    df_Cameras = pd.DataFrame(data_Cameras)

    data_Item_General_Trajectory = pd.read_csv(
        os.path.join(data_path, "item_general_trajectory.csv")
    )
    df_Item_General_Trajectory = pd.DataFrame(data_Item_General_Trajectory)
    df_Item_General_Trajectory.drop(columns=["color", "largestbbox"], inplace=True)

    # data_General_Bbox = pd.read_csv(os.path.join(data_path, "general_bbox.csv"))
    # df_General_Bbox = pd.DataFrame(data_General_Bbox)

    database.reset(False)

    for _, row in df_Cameras.iterrows():
        values = tuple(row.values)
        _insert_into_camera(database, values, False)

    for _, row in df_Item_General_Trajectory.iterrows():
        values = tuple(row.values)
        _insert_into_item_general_trajectory(database, values, False)

    # for _, row in df_General_Bbox.iterrows():
    #     database._insert_into_general_bbox(row, False)

    database._commit()


def _name(column: "tuple[str, str]") -> str:
    return column[0]


def _insert_into_camera(database: "Database", value: tuple, commit=True):
    cursor = database.connection.cursor()
    cursor.execute(
        f"INSERT INTO Cameras ({columns(_name, CAMERA_COLUMNS)}) VALUES ({place_holder(len(CAMERA_COLUMNS))})",
        tuple(value),
    )
    database._commit(commit)
    cursor.close()


def _insert_into_item_general_trajectory(database: "Database", value: tuple, commit=True):
    cursor = database.connection.cursor()
    cursor.execute(
        f"INSERT INTO Item_General_Trajectory ({columns(_name, TRAJECTORY_COLUMNS)}) VALUES ({place_holder(len(TRAJECTORY_COLUMNS))})",
        tuple(value),
    )
    database._commit(commit)
    cursor.close()


def _insert_into_general_bbox(database: "Database", value: tuple, commit=True):
    database.cursor.execute(
        f"INSERT INTO General_Bbox ({columns(_name, BBOX_COLUMNS)}) VALUES ({place_holder(len(BBOX_COLUMNS))})",
        tuple(value),
    )
    database._commit(commit)
