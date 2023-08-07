from __future__ import annotations

import datetime
import inspect
import uuid
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from spatialyze.data_types import Camera, FetchCameraTuple
from spatialyze.database import database
from spatialyze.utils import transformation

if TYPE_CHECKING:
    import pandas as pd

    from ..data_types import Trajectory
    from ..predicate import PredicateNode


camera_nodes: Dict[str, "Camera"] = {}


class World:
    _parent: Optional[World]
    _name: str
    _fn: Tuple[Optional[Callable]]
    _kwargs: dict[str, Any]
    _done: bool
    _world_id: str
    _timestamp: datetime.datetime
    _materialized: bool

    def __init__(
        self,
        world_id: str,
        timestamp: datetime.datetime,
        name: Optional[str] = None,
        parent: Optional[World] = None,
        fn: Optional[Union[str, Callable]] = None,
        kwargs: Optional[dict[str, Any]] = None,
        done: bool = False,
        materialized: bool = False,
    ):
        self._parent = parent
        self._name = "" if name is None else name
        self._fn = (fn if fn is None else (getattr(database, fn) if isinstance(fn, str) else fn),)
        self._kwargs = {} if kwargs is None else kwargs
        self._done = done  # update node
        self._world_id = world_id
        self._timestamp = timestamp
        self._materialized = materialized

    def add_camera(self, camera: "Camera"):
        node1 = self._insert_camera(camera=camera)
        node2 = node1._retrieve_camera(camera_id=camera.id)
        return node2

    def recognize(self, camera: "Camera", annotation: "pd.DataFrame"):
        node1 = self._insert_bbox_traj(camera=camera, annotation=annotation)
        node2 = node1._retrieve_bbox(camera_id=camera.id)
        node3 = node2._retrieve_traj(camera_id=camera.id)
        return node3

    def filter(self, predicate: "PredicateNode") -> World:
        return derive_world(
            self,
            database.filter,
            predicate=predicate,
        )

    def exclude(self, other: World) -> World:
        return derive_world(self, database.exclude, world=other)

    def union(self, other: World) -> World:
        return derive_world(self, database.union, world=other)

    def intersect(self, other: World) -> World:
        return derive_world(self, database.intersect, world=other)

    def sym_diff(self, other: World) -> World:
        return self.union(other).exclude(self.intersect(other))

    def __lshift__(self, camera: "Camera | tuple[Camera, pd.DataFrame]"):
        """add a camera or add a camera and recognize"""
        if isinstance(camera, Camera):
            return self.add_camera(camera)
        c, a, *_ = camera
        return self.add_camera(c).recognize(c, a)

    def __sub__(self, other: World) -> World:
        return self.exclude(other)

    def __or__(self, other: World) -> World:
        return self.union(other)

    def __and__(self, other: World) -> World:
        return self.intersect(other)

    def __xor__(self, other: World) -> World:
        return self.sym_diff(other)

    def road_direction(self, x: float, y: float, default_dir: float):
        return database.road_direction(x, y, default_dir)

    def road_coords(self, x: float, y: float):
        return database.road_coords(x, y)

    def get_traj_key(self):
        return derive_world(
            self,
            database.get_traj_key,
        )._execute_from_root()

    def get_id_time_camId_filename(self, num_joined_tables: int):
        result = derive_world(
            self,
            database.get_id_time_camId_filename,
            num_joined_tables=num_joined_tables,
        )._execute_from_root()
        result = sorted(result, key=lambda x: x[num_joined_tables])
        return result

    def _insert_camera(self, camera: "Camera"):
        return derive_world(
            self,
            database.insert_cam,
            camera=camera,
        )

    def _retrieve_camera(self, camera_id: str):
        return derive_world(
            self,
            database.retrieve_cam,
            camera_id=camera_id,
        )

    def _insert_bbox_traj(self, camera: "Camera", annotation: "pd.DataFrame"):
        return derive_world(
            self,
            database.insert_bbox_traj,
            camera=camera,
            annotation=annotation,
        )

    def _retrieve_bbox(self, camera_id: str):
        return derive_world(self, database.retrieve_bbox, camera_id=camera_id)

    def _retrieve_traj(self, camera_id: str):
        return derive_world(self, database.retrieve_traj, camera_id=camera_id)

    def _execute_from_root(self) -> Any:
        nodes: list[World] = []
        curr: Optional[World] = self
        res = None
        query = "SELECT * FROM item_general_trajectory"

        # collect all the nodes til the root
        while curr:
            nodes.append(curr)
            curr = curr._parent

        # execute the nodes from the root
        for node in nodes[::-1]:
            # root
            if node.fn is None:
                continue

            if node.fn == database.insert_cam or node.fn == database.insert_bbox_traj:
                # print("execute:", node.fn.__name__)
                if not node.done:
                    node._execute()
                    node._done = True
            # treat update method differently
            else:
                # print("execute:", node.fn.__name__)
                # print(query)
                query = node._execute(query=query, **node.kwargs)
        # print("done execute node")

        res = query
        # if isinstance(query, list):
        #     print("Result length:", len(query))
        return res

    def _execute(self, **kwargs):
        fn = self._fn[0]
        if fn is None:
            raise Exception("A world without a function should not be executed")

        fn_spec = inspect.getfullargspec(fn)
        if "world_id" in fn_spec.args or fn_spec.varkw is not None:
            return fn(**{"world_id": self._world_id, **self._kwargs, **kwargs})
        return fn(**{**self._kwargs, **kwargs})

    def _print_lineage(self):
        curr = self
        while curr:
            print(curr)
            curr = curr._parent

    def __str__(self):
        return f"fn={self._fn[0]}\nkwargs={self._kwargs}\ndone={self._done}\nworld_id={self._world_id}\n"

    @property
    def world_id(self):
        return self._world_id

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self._name

    @property
    def fn(self):
        return self._fn[0]

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def done(self):
        return self._done

    @property
    def materialized(self):
        return self._materialized


def empty_world(name: str = "world") -> World:
    world_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow()
    return World(world_id, timestamp, name)


def derive_world(parent: World, fn: Any, **kwargs) -> World:
    world_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow()

    return World(
        world_id,
        timestamp,
        fn=fn,
        kwargs=kwargs,
        parent=parent,
    )


def world_to_pixel(
    camera_config: dict, world_coords: Union[np.ndarray, Tuple[float, float, float]]
):
    traj_2d = transformation(world_coords, camera_config)
    return traj_2d


def get_overlay_info(trajectory: Trajectory, camera_info: List[List["FetchCameraTuple"]]):
    """
    overlay each trajectory 3d coordinate on to the frame specified by the camera_info
    1. For each point in the trajectory, find the list of cameras that correspond to that timestamp
    2. Project the trajectory coordinates onto the intrinsics of the camera, and add it to the list of results
    3. Returns a mapping from each camera type (FRONT, BACK, etc) to the trajectory in pixel coordinates of that camera
    """
    traj_obj_3d = trajectory.coordinates
    result: Dict[str, List[Tuple[np.ndarray, int, str, float, float, List[float], dict]]] = {}
    for index, cur_camera_infos in enumerate(camera_info):
        # cur_camera_infos = camera_info[
        #     index
        # ]  # camera info of the obejct in one point of the trajectory
        centroid_3d = np.array(traj_obj_3d[index])  # one point of the trajectory in 3d
        # in order to fit into the function transformation, we develop a dictionary called camera_config
        for cur_camera_info in cur_camera_infos:
            # TODO: add type to camera_config
            camera_config: Dict[str, Any] = {}
            camera_config["egoTranslation"] = cur_camera_info[1]
            camera_config["egoRotation"] = np.array(cur_camera_info[2])
            camera_config["cameraTranslation"] = cur_camera_info[3]
            camera_config["cameraRotation"] = np.array(cur_camera_info[4])
            camera_config["cameraIntrinsic"] = np.array(cur_camera_info[5])

            traj_2d = world_to_pixel(camera_config, centroid_3d)

            framenum = cur_camera_info[6]
            filename = cur_camera_info[7]
            camera_heading = cur_camera_info[8]
            ego_heading = cur_camera_info[9]
            ego_translation = cur_camera_info[1]
            file_prefix = "_".join(filename.split("/")[:-1])

            if file_prefix not in result:
                result[file_prefix] = []
            result[file_prefix].append(
                (
                    traj_2d,
                    framenum,
                    filename,
                    camera_heading,
                    ego_heading,
                    ego_translation,
                    camera_config,
                )
            )
    return result


def trajectory_to_timestamp(trajectory):
    return [traj[0].datetimes for traj in trajectory]
