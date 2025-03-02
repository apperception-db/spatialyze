import os
import random

import pandas as pd
from spatialyze.data_types.query_result import QueryResult

from spatialyze.database import (
    BBOX_COLUMNS,
    CAMERA_COLUMNS,
    TRAJECTORY_COLUMNS,
    Database,
    database,
    columns,
)


random.seed(1234)


def get_results(path: str = "./data/scenic/test-results"):
    results: list[QueryResult] = []
    for file in os.listdir(path):
        if not file.endswith(".py"):
            continue
        with open(os.path.join(path, file), "r") as f:
            _results = f.readlines()
        results.extend(eval("\n".join(_results[1:])))
    assert all(isinstance(result, QueryResult) for result in results)

    results_set = set(results)

    scenes: dict[str, list[QueryResult]] = {}
    for result in results_set:
        if result.camera_id not in scenes:
            scenes[result.camera_id] = []
        scenes[result.camera_id].append(result)

    frame_range: dict[str, tuple[int, int]] = {
        scene: (min(result.frame_number for result in results),
                max(result.frame_number for result in results))
        for scene, results in scenes.items()
    }

    _items: list[str] = []
    for result in results_set:
        _items.extend(result.item_ids)
    items = set(_items)

    return scenes, frame_range, items


def import_tables(database: "Database", data_path: str):
    # scenes, frame_range, items = get_results()

    # Import CSV
    data_Cameras = pd.read_csv(os.path.join(data_path, "cameras.csv"))
    df_Cameras = pd.DataFrame(data_Cameras)
    # df_Cameras = df_Cameras[df_Cameras.apply(lambda x: (x['cameraid'] in frame_range and frame_range[x['cameraid']][0] - 10 < x['framenum'] and x['framenum'] < frame_range[x['cameraid']][1] + 10) or random.random() < 0.1, axis=1)]

    # data_Item_Trajectory = pd.read_csv(
    #     os.path.join(data_path, "item_trajectory.csv")
    # )
    # df_Item_Trajectory = pd.DataFrame(data_Item_Trajectory)
    # df_Item_Trajectory.drop(columns=["color", "largestbbox", "translations"], inplace=True)
    # df_Item_Trajectory = df_Item_Trajectory[df_Item_Trajectory.apply(lambda x: x['itemid'] in items or random.random() < 0.07, axis=1)]

    # data_General_Bbox = pd.read_csv(os.path.join(data_path, "general_bbox.csv"))
    # df_General_Bbox = pd.DataFrame(data_General_Bbox)

    database.reset(False)

    for _, row in df_Cameras.iterrows():
        values = tuple(row.values)
        _insert_into_camera(database, values, False)

    # for _, row in df_Item_Trajectory.iterrows():
    #     values = tuple(row.values)
    #     _insert_into_item_trajectory(database, values, False)

    # for _, row in df_General_Bbox.iterrows():
    #     database._insert_into_general_bbox(row, False)

    with open('./data/scenic/database/item_trajectory.csv', 'r') as f:
        database.cursor.copy_expert("copy item_trajectory from stdin DELIMITER ',' CSV header", f)

    database._commit()


def _name(column: "tuple[str, str]") -> str:
    return column[0]


def place_holder(num: int):
    return ",".join(["%s"] * num)


def _insert_into_camera(database: "Database", value: tuple, commit=True):
    cursor = database.connection.cursor()
    cursor.execute(
        f"INSERT INTO Camera ({columns(_name, CAMERA_COLUMNS)}) VALUES ({place_holder(len(CAMERA_COLUMNS))})",
        tuple(value),
    )
    database._commit(commit)
    cursor.close()


# def _insert_into_item_trajectory(database: "Database", value: tuple, commit=True):
#     cursor = database.connection.cursor()
#     cursor.execute(
#         f"INSERT INTO Item_Trajectory ({columns(_name, TRAJECTORY_COLUMNS)}) VALUES ({place_holder(len(TRAJECTORY_COLUMNS))})",
#         tuple(value),
#     )
#     database._commit(commit)
#     cursor.close()


def _insert_into_general_bbox(database: "Database", value: tuple, commit=True):
    database.cursor.execute(
        f"INSERT INTO General_Bbox ({columns(_name, BBOX_COLUMNS)}) VALUES ({place_holder(len(BBOX_COLUMNS))})",
        tuple(value),
    )
    database._commit(commit)


if __name__ == "__main__":
    import_tables(database, './data/scenic/database')
