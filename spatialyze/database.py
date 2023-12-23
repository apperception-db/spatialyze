import datetime
from collections.abc import Mapping, Sequence
from os import environ
from typing import TYPE_CHECKING, Callable, NamedTuple

import pandas as pd
import psycopg2
import psycopg2.errors
from mobilitydb.psycopg import register as mobilitydb_register
from postgis import Point
from postgis.psycopg import register as postgis_register
from psycopg2.sql import SQL, Composable, Literal

from .data_types.camera_key import CameraKey
from .data_types.nuscenes_annotation import NuscenesAnnotation
from .data_types.nuscenes_camera import NuscenesCamera
from .data_types.query_result import QueryResult
from .predicate import (
    FindAllTablesVisitor,
    GenSqlVisitor,
    MapTablesTransformer,
    normalize,
)
from .utils.ingest_processed_nuscenes import ingest_processed_nuscenes
from .utils.ingest_road import (
    ROAD_TYPES,
    add_segment_type,
    create_tables,
    drop_tables,
    ingest_location,
)
from .video_processor.camera_config import CameraConfig
from .video_processor.types import Float33

if TYPE_CHECKING:
    from psycopg2 import connection as Connection
    from psycopg2 import cursor as Cursor

    from .predicate import PredicateNode

CAMERA_TABLE = "Cameras"
TRAJECTORY_TABLE = "Item_Trajectory"
DETECTION_TABLE = "Item_Detection"
BBOX_TABLE = "General_Bbox"
TABLES = CAMERA_TABLE, TRAJECTORY_TABLE, DETECTION_TABLE, BBOX_TABLE

CAMERA_COLUMNS: "list[tuple[str, str]]" = [
    ("cameraId", "TEXT"),
    ("frameId", "TEXT"),
    ("frameNum", "Int"),
    ("fileName", "TEXT"),
    ("cameraTranslation", "geometry"),
    ("cameraRotation", "real[4]"),
    ("cameraIntrinsic", "real[3][3]"),
    ("egoTranslation", "geometry"),
    ("egoRotation", "real[4]"),
    ("timestamp", "timestamptz"),
    ("cameraHeading", "real"),
    ("egoHeading", "real"),
]

TRAJECTORY_COLUMNS: "list[tuple[str, str]]" = [
    ("itemId", "TEXT"),
    ("cameraId", "TEXT"),
    ("objectType", "TEXT"),
    # ("roadTypes", "ttext"),
    ("translations", "tgeompoint"),  # [(x,y,z)@today, (x2, y2,z2)@tomorrow, (x2, y2,z2)@nextweek]
    ("itemHeadings", "tfloat"),
    # ("color", "TEXT"),
    # ("largestBbox", "STBOX")
    # ("roadPolygons", "tgeompoint"),
    # ("period", "period") [today, nextweek]
]

DETECTION_COLUMNS: list[tuple[str, str]] = [
    ("itemId", "TEXT"),
    ("cameraId", "TEXT"),
    ("objectType", "TEXT"),
    ("frameNum", "Int"),
    ("translation", "geompoint"),
    ("timestamp", "timestamptz"),
]

BBOX_COLUMNS: "list[tuple[str, str]]" = [
    ("itemId", "TEXT"),
    ("cameraId", "TEXT"),
    ("trajBbox", "stbox"),
    ("timestamp", "timestamptz"),
]


def columns(fn: "Callable[[tuple[str, str]], str]", columns: "list[tuple[str, str]]") -> str:
    return ",".join(map(fn, columns))


def _schema(column: "tuple[str, str]") -> str:
    return " ".join(column)


def place_holder(num: int):
    return ",".join(["%s"] * num)


class Database:
    connection: "Connection"
    cursor: "Cursor"

    def __init__(self, connection: "Connection"):
        self.connection = connection
        postgis_register(self.connection)
        mobilitydb_register(self.connection)
        self.cursor = self.connection.cursor()

    def reset(self, commit=True):
        self.reset_cursor()
        self._drop_table(commit)
        self._create_camera_table(commit)
        self._create_item_trajectory_table(commit)
        self._create_item_detection_table(commit)
        self._create_general_bbox_table(commit)
        self._create_index(commit)

    def reset_cursor(self):
        self.cursor.close()
        assert self.cursor.closed
        self.cursor = self.connection.cursor()

    def _drop_table(self, commit=True):
        cursor = self.connection.cursor()
        for table in TABLES:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        self._commit(commit)
        cursor.close()

    def _create_camera_table(self, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE TABLE Cameras ("
            f"{columns(_schema, CAMERA_COLUMNS)},"
            "PRIMARY KEY (cameraId, frameNum))"
        )
        self._commit(commit)
        cursor.close()

    def _create_general_bbox_table(self, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE TABLE General_Bbox ("
            f"{columns(_schema, BBOX_COLUMNS)},"
            "FOREIGN KEY(itemId) REFERENCES Item_Trajectory (itemId),"
            "PRIMARY KEY (itemId, timestamp))"
        )
        self._commit(commit)
        cursor.close()

    def _create_item_trajectory_table(self, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE TABLE Item_Trajectory ("
            f"{columns(_schema, TRAJECTORY_COLUMNS)},"
            "PRIMARY KEY (itemId))"
        )
        self._commit(commit)
        cursor.close()

    def _create_item_detection_table(self, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE TABLE Item_Detection ("
            f"{columns(_schema, DETECTION_COLUMNS)},"
            "PRIMARY KEY (itemId),"
            "FOREIGN KEY (cameraId, frameNum) REFERENCES Cameras(cameraId, frameNum))"
        )
        self._commit(commit)
        cursor.close()

    def _create_index(self, commit=True):
        cursor = self.connection.cursor()
        # cursor.execute("CREATE INDEX ON Cameras (cameraId);")
        cursor.execute("CREATE INDEX ON Cameras (cameraId, frameNum);")
        cursor.execute("CREATE INDEX ON Cameras (timestamp);")
        cursor.execute("CREATE INDEX ON Item_Trajectory (itemId);")
        cursor.execute("CREATE INDEX ON Item_Trajectory (cameraId);")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS trans_idx "
            "ON Item_Trajectory "
            "USING GiST(translations);"
        )
        cursor.execute("CREATE INDEX ON Item_Detection (cameraId);")
        cursor.execute("CREATE INDEX ON Item_Detection (frameNum);")
        cursor.execute("CREATE INDEX ON Item_Detection (cameraId, frameNum);")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS item_detection_translation_idx "
            "ON Item_Detection "
            "USING GiST(translation);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS item_detection_timestamp_idx "
            "ON Item_Detection "
            "USING GiST(timestamp);"
        )
        # cursor.execute("CREATE INDEX IF NOT EXISTS item_idx ON General_Bbox(itemId);")
        # cursor.execute(
        #     "CREATE INDEX IF NOT EXISTS traj_bbox_idx ON General_Bbox USING GiST(trajBbox);"
        # )
        # cursor.execute(
        #     "CREATE INDEX IF NOT EXISTS item_id_timestampx ON General_Bbox(itemId, timestamp);"
        # )
        self._commit(commit)
        cursor.close()

    def _commit(self, commit=True):
        if commit:
            self.connection.commit()

    def execute_and_cursor(
        self,
        query: str | Composable,
        vars: tuple | list | Sequence | Mapping | None = None,
    ) -> "tuple[list[tuple], Cursor]":
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, vars)
            if cursor.pgresult_ptr is not None:
                return cursor.fetchall(), cursor
            else:
                return [], cursor
        except psycopg2.errors.DatabaseError as error:
            for notice in cursor.connection.notices:
                print(notice)
            self.connection.rollback()
            cursor.close()
            raise error

    def execute(
        self,
        query: str | Composable,
        vars: tuple | list | Sequence | Mapping | None = None,
    ) -> "list[tuple]":
        results, cursor = self.execute_and_cursor(query, vars)
        cursor.close()
        return results

    def update(self, query: str | Composable, commit: bool = True) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self._commit(commit)
        except psycopg2.errors.DatabaseError as error:
            for notice in cursor.connection.notices:
                print(notice)
            self.connection.rollback()
            raise error
        finally:
            cursor.close()

    def insert_camera(self, camera: list[CameraConfig]):
        cursor = self.connection.cursor()
        insert = SQL("INSERT INTO Cameras VALUES ")
        values = SQL(",").join(map(_config, camera))
        cursor.execute(insert + values)

        # print("New camera inserted successfully.........")
        self.connection.commit()
        cursor.close()

    def load_roadnetworks(self, dir: "str", location: "str"):
        drop_tables(database)
        create_tables(database)
        ingest_location(self, dir, location)
        add_segment_type(self, ROAD_TYPES)
        self._commit()

    def load_nuscenes(
        self,
        annotations: "dict[CameraKey, list[NuscenesAnnotation]]",
        cameras: "dict[CameraKey, list[NuscenesCamera]]",
    ):
        ingest_processed_nuscenes(annotations, cameras, self)

    def predicate(self, predicate: "PredicateNode"):
        tables, camera = FindAllTablesVisitor()(predicate)
        tables = sorted(tables)
        mapping = {t: i for i, t in enumerate(tables)}
        predicate = normalize(predicate)
        predicate = MapTablesTransformer(mapping)(predicate)

        t_tables = ""
        t_outputs = ""
        for i in range(len(tables)):
            t_tables += (
                f"JOIN Item_Trajectory AS t{i} "
                f"ON  c0.timestamp <@ t{i}.translations::period "
                f"AND c0.cameraId  =  t{i}.cameraId\n"
            )
            t_outputs += f",\n   t{i}.itemId"

        sql_str = (
            f"SELECT c0.frameNum, c0.cameraId, c0.filename{t_outputs}\n"
            f"FROM Cameras as c0\n{t_tables}"
            f"WHERE {GenSqlVisitor()(predicate)}"
        )
        return [
            QueryResult(frame_number, camera_id, filename, tuple(item_ids))
            for frame_number, camera_id, filename, *item_ids in self.execute(sql_str)
        ]

    def sql(self, query: str) -> pd.DataFrame:
        results, cursor = self.execute_and_cursor(query)
        description = cursor.description
        cursor.close()
        return pd.DataFrame(results, columns=[d.name for d in description])


class _Config(NamedTuple):
    cameraId: str
    frameId: str
    frameNum: int
    fileName: str
    cameraTranslation: Point
    cameraRotation: list[float]  # [w, x, y, z]
    cameraIntrinsic: Float33
    egoTranslation: Point
    egoRotation: list[float]  # [w, x, y, z]
    timestamp: datetime.datetime
    cameraHeading: float
    egoHeading: float


def _config(config: CameraConfig) -> Composable:
    cc = _Config(
        config.camera_id,
        config.frame_id,
        config.frame_num,
        config.filename,
        Point(*config.camera_translation),
        [*map(float, config.camera_rotation.q)],
        config.camera_intrinsic,
        Point(*config.ego_translation),
        [*map(float, config.ego_rotation.q)],
        config.timestamp,
        config.camera_heading,
        config.ego_heading,
    )

    assert isinstance(cc.cameraRotation, list), cc.cameraRotation
    assert len(cc.cameraRotation) == 4, cc.cameraRotation
    assert isinstance(cc.egoRotation, list), cc.egoRotation
    assert len(cc.egoRotation) == 4, cc.egoRotation
    row = map(Literal, cc)
    return SQL("({})").format(SQL(",").join(row))


### Do we still want to keep this??? Causes problems since if user uses a different port
# will need to come in here to change
database = Database(
    psycopg2.connect(
        dbname=environ.get("AP_DB", "mobilitydb"),
        user=environ.get("AP_USER", "docker"),
        host=environ.get("AP_HOST", "localhost"),
        port=environ.get("AP_PORT", "25432"),
        password=environ.get("AP_PASSWORD", "docker"),
    )
)
