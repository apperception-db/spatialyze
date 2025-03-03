import duckdb

from spatialyze.database import CAMERA_COLUMNS, TRAJECTORY_COLUMNS


def export_tables(conn: duckdb.DuckDBPyConnection, data_path: str):
    # create a query to specify which values we want from the database.
    s = "SELECT * FROM "
    s_trajectory = f"SELECT {','.join([c for c, _ in TRAJECTORY_COLUMNS])} FROM Item_Trajectory"
    s_bbox = s + "General_Bbox"
    s_camera = f"SELECT {','.join([c for c, _ in CAMERA_COLUMNS])} FROM Camera"

    with conn.cursor() as db_cursor:
        trajectory_file = data_path + "item_trajectory.csv"
        db_cursor.execute(f"COPY ({s_trajectory}) TO '{trajectory_file}' (HEADER true, DELIMITER ',')")

        bbox_file = data_path + "general_bbox.csv"
        db_cursor.execute(f"COPY ({s_bbox}) TO '{bbox_file}' (HEADER true, DELIMITER ',')")

        camera_file = data_path + "cameras.csv"
        db_cursor.execute(f"COPY ({s_camera}) TO '{camera_file}' (HEADER true, DELIMITER ',')")
