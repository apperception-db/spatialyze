from psycopg2._psycopg import connection as Connection

from spatialyze.database import CAMERA_COLUMNS, TRAJECTORY_COLUMNS


def export_tables(conn: Connection, data_path: str):
    # create a query to specify which values we want from the database.
    s = "SELECT * FROM "
    s_trajectory = f"SELECT {','.join([c for c, _ in TRAJECTORY_COLUMNS])} FROM Item_Trajectory"
    s_bbox = s + "General_Bbox"
    s_camera = f"SELECT {','.join([c for c, _ in CAMERA_COLUMNS])} FROM Cameras"

    # set up our database connection.
    db_cursor = conn.cursor()

    # Use the COPY function on the SQL we created above.
    SQL_trajectory_output = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(s_trajectory)
    SQL_bbox_output = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(s_bbox)
    SQL_camera_output = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(s_camera)

    # Set up a variable to store our file path and name.
    trajectory_file = data_path + "item_trajectory.csv"
    with open(trajectory_file, "w") as trajectory_output:
        db_cursor.copy_expert(SQL_trajectory_output, trajectory_output)

    bbox_file = data_path + "general_bbox.csv"
    with open(bbox_file, "w") as bbox_output:
        db_cursor.copy_expert(SQL_bbox_output, bbox_output)

    camera_file = data_path + "cameras.csv"
    with open(camera_file, "w") as camera_output:
        db_cursor.copy_expert(SQL_camera_output, camera_output)
