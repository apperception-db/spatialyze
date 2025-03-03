import datetime
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Callable, NamedTuple

import duckdb
import shapely.geometry

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
    from .predicate import PredicateNode

CAMERA_TABLE = "Camera"
TRAJECTORY_TABLE = "Item_Trajectory"
DETECTION_TABLE = "Item_Detection"
BBOX_TABLE = "General_Bbox"
METADATA_TABLE = "Spatialyze_Metadata"
TABLES = (
    DETECTION_TABLE,
    TRAJECTORY_TABLE,
    BBOX_TABLE,
    CAMERA_TABLE,
    METADATA_TABLE,
)

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

DETECTION_COLUMNS: list[tuple[str, str]] = [
    ("itemId", "TEXT"),
    ("cameraId", "TEXT"),
    ("objectType", "TEXT"),
    ("frameNum", "Int"),
    ("translation", "geometry"),
    ("timestamp", "timestamptz"),
    ("itemHeading", "Float"),
]

TRAJECTORY_COLUMNS: list[tuple[str, str]] = [
    ("itemId", "TEXT"),
    ("cameraId", "TEXT"),
    ("objectType", "TEXT"),
    ("frameNum", "Int"),
    ("translation", "geometry"),
    ("itemHeading", "Float"),
]

BBOX_COLUMNS: "list[tuple[str, str]]" = [
    ("itemId", "TEXT"),
    ("cameraId", "TEXT"),
    ("trajBbox", "stbox"),
    ("timestamp", "timestamptz"),
]

METADATA_COLUMNS: "list[tuple[str, str]]" = [
    ("fps", "Int"),
]


def columns(fn: "Callable[[tuple[str, str]], str]", columns: "list[tuple[str, str]]") -> str:
    return ",".join(map(fn, columns))


def _schema(column: "tuple[str, str]") -> str:
    return " ".join(column)


class Database:
    connection: "duckdb.DuckDBPyConnection"
    cursor: "duckdb.DuckDBPyConnection"

    def __init__(self, connection: "duckdb.DuckDBPyConnection"):
        self.connection = connection
        self.connection.install_extension("spatial")
        self.connection.load_extension("spatial")
        self.cursor = self.connection.cursor()

        self.cursor.commit()
        self.connection.commit()

    def reset(self, commit=True):
        self.reset_cursor()
        self._drop_table(commit)
        self._create_camera_table(commit)
        self._create_item_trajectory_table(commit)
        self._create_item_detection_table(commit)
        # self._create_general_bbox_table(commit)
        self._create_metadata_table(commit)
        self._create_index(commit)

    def reset_cursor(self):
        self.cursor.close()
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
            "CREATE TABLE Camera ("
            f"{columns(_schema, CAMERA_COLUMNS)},"
            "PRIMARY KEY (cameraId, frameNum))"
        )
        self._commit(commit)
        cursor.close()

    # def _create_general_bbox_table(self, commit=True):
    #     cursor = self.connection.cursor()
    #     cursor.execute(
    #         "CREATE TABLE General_Bbox ("
    #         f"{columns(_schema, BBOX_COLUMNS)},"
    #         # f"FOREIGN KEY(itemId) REFERENCES {TRAJECTORY_TABLE} (itemId),"
    #         "PRIMARY KEY (itemId, timestamp))"
    #     )
    #     self._commit(commit)
    #     cursor.close()

    def _create_item_trajectory_table(self, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(
            f"CREATE TABLE {TRAJECTORY_TABLE} ("
            f"{columns(_schema, TRAJECTORY_COLUMNS)},"
            "PRIMARY KEY (itemId, frameNum), "
            "FOREIGN KEY (cameraId, frameNum) REFERENCES Camera(cameraId, frameNum))"
        )
        self._commit(commit)
        cursor.close()

    def _create_item_detection_table(self, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE TABLE Item_Detection ("
            f"{columns(_schema, DETECTION_COLUMNS)},"
            "PRIMARY KEY (itemId),"
            "FOREIGN KEY (cameraId, frameNum) REFERENCES Camera(cameraId, frameNum))"
        )
        self._commit(commit)
        cursor.close()

    def _create_metadata_table(self, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE TABLE Spatialyze_Metadata ({columns(_schema, METADATA_COLUMNS)})")
        self._commit(commit)
        cursor.close()

    def _create_index(self, commit=True):
        cursor = self.connection.cursor()
        # cursor.execute("CREATE INDEX ON Camera (cameraId);")
        cursor.execute("CREATE INDEX Camera_CameraId_frameNum_idx ON Camera (cameraId, frameNum);")
        cursor.execute("CREATE INDEX Camera_timestamp_idx ON Camera (timestamp);")

        cursor.execute("CREATE INDEX Item_Detection_cameraId_idx ON Item_Detection (cameraId);")
        cursor.execute("CREATE INDEX Item_Detection_frameNum_idx ON Item_Detection (frameNum);")
        cursor.execute(
            "CREATE INDEX Item_Detection_cameraId_frameNum_idx ON Item_Detection (cameraId, frameNum);"
        )
        cursor.execute("CREATE INDEX Item_Detection_timestamp_idx ON Item_Detection (timestamp);")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS item_detection_translation_idx "
            "ON Item_Detection "
            "USING RTREE (translation);"
        )
        cursor.execute(
            f"CREATE INDEX {TRAJECTORY_TABLE}_cameraId_idx ON {TRAJECTORY_TABLE} (cameraId);"
        )
        cursor.execute(
            f"CREATE INDEX {TRAJECTORY_TABLE}_frameNum_idx ON {TRAJECTORY_TABLE} (frameNum);"
        )
        cursor.execute(
            f"CREATE INDEX {TRAJECTORY_TABLE}_cameraId_frameNum_idx ON {TRAJECTORY_TABLE} (cameraId, frameNum);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS Item_Trajectory_translation_idx "
            f"ON {TRAJECTORY_TABLE} "
            "USING RTREE (translation);"
        )
        # cursor.execute("CREATE INDEX IF NOT EXISTS item_idx ON General_Bbox(itemId);")
        # cursor.execute(
        #     "CREATE INDEX IF NOT EXISTS traj_bbox_idx ON General_Bbox USING RTREE (trajBbox);"
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
        query: str,
        vars: tuple | list | Sequence | Mapping | map | None = None,
        many: bool = False,
    ) -> "tuple[list[tuple], duckdb.DuckDBPyConnection]":
        cursor = self.connection.cursor()
        try:
            if many:
                cursor.executemany(query, vars)
            else:
                cursor.execute(query, vars)
            return cursor.fetchall(), cursor
        except duckdb.Error as error:
            # for notice in cursor.connection.notices:
            #     print(notice)
            try:
                self.connection.rollback()
            except duckdb.TransactionException:
                pass
            cursor.close()
            raise error

    def execute(
        self,
        query: str,
        vars: tuple | list | Sequence | Mapping | map | None = None,
        many: bool = False,
    ) -> "list[tuple]":
        results, cursor = self.execute_and_cursor(query, vars, many)
        cursor.close()
        return results

    def update(
        self,
        query: str,
        commit: bool = True,
        vars: tuple | list | Sequence | Mapping | map | None = None,
        many: bool = False,
    ) -> None:
        cursor = self.connection.cursor()
        try:
            if many:
                cursor.executemany(query, vars)
            else:
                cursor.execute(query, vars)
            self._commit(commit)
        except duckdb.Error as error:
            # for notice in cursor.connection.notices:
            #     print(notice)
            try:
                self.connection.rollback()
            except duckdb.TransactionException:
                pass
            raise error
        finally:
            cursor.close()

    def insert_camera(self, camera: list[CameraConfig]):
        cursor = self.connection.cursor()
        cursor.executemany(
            "INSERT INTO Camera VALUES "
            "(?, ?, ?, ?, ST_GeomFromWKB(?), ?,"
            " ?, ST_GeomFromWKB(?), ?, ?, ?, ?)",
            map(_config, camera),
        )

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

    def predicate(self, predicate: "PredicateNode", temporal: bool = True):
        tables, _ = FindAllTablesVisitor()(predicate)
        tables = sorted(tables)
        mapping = {t: i for i, t in enumerate(tables)}
        predicate = normalize(predicate, temporal)
        predicate = MapTablesTransformer(mapping)(predicate)
        join_table = _join_table(temporal)

        t_tables = ""
        t_outputs = ""
        for i in range(len(tables)):
            t_tables += join_table(i)
            t_outputs += f",\n   t{i}.itemId"

        sql_str = (
            f"SELECT c0.frameNum, c0.cameraId, c0.filename{t_outputs}\n"
            f"FROM Camera as c0\n{t_tables}"
            f"WHERE {GenSqlVisitor()(predicate)}"
        )
        return [
            QueryResult(frame_number, camera_id, filename, tuple(item_ids))
            for frame_number, camera_id, filename, *item_ids in self.execute(sql_str)
        ]

    def sql(self, query: str) -> duckdb.DuckDBPyRelation:
        with self.connection.cursor() as cursor:
            return cursor.sql(query)


def _join_table(temporal: bool):
    if temporal:

        def join_table(i: int) -> str:
            return (
                f"JOIN {TRAJECTORY_TABLE} AS t{i} "
                f"ON  c0.frameNum = t{i}.frameNum "
                f"AND c0.cameraId = t{i}.cameraId\n"
            )

    else:

        def join_table(i: int) -> str:
            return f"JOIN Item_Detection AS t{i}" " USING (frameNum, cameraId)\n"

    return join_table


class _Config(NamedTuple):
    cameraId: str
    frameId: str
    frameNum: int
    fileName: str
    cameraTranslation: bytes  # WKB: 'POINT(x y z)'
    cameraRotation: list[float]  # [w, x, y, z]
    cameraIntrinsic: Float33
    egoTranslation: bytes  # WKB: 'POINT(x y z)'
    egoRotation: list[float]  # [w, x, y, z]
    timestamp: datetime.datetime
    cameraHeading: float
    egoHeading: float


def _config(config: CameraConfig) -> _Config:
    cc = _Config(
        cameraId=config.camera_id,
        frameId=config.frame_id,
        frameNum=config.frame_num,
        fileName=config.filename,
        cameraTranslation=shapely.geometry.Point(*config.camera_translation).wkb,
        cameraRotation=[*map(float, config.camera_rotation.q)],
        cameraIntrinsic=config.camera_intrinsic,
        egoTranslation=shapely.geometry.Point(*config.ego_translation).wkb,
        egoRotation=[*map(float, config.ego_rotation.q)],
        timestamp=config.timestamp,
        cameraHeading=config.camera_heading,
        egoHeading=config.ego_heading,
    )

    assert isinstance(cc.cameraRotation, list), cc.cameraRotation
    assert len(cc.cameraRotation) == 4, cc.cameraRotation
    assert isinstance(cc.egoRotation, list), cc.egoRotation
    assert len(cc.egoRotation) == 4, cc.egoRotation

    return cc


database = Database(duckdb.connect(":memory:"))
