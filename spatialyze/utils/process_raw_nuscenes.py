import json
import math
import os
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
from pyquaternion import Quaternion
from tqdm import tqdm

from ..data_types.camera_key import CameraKey
from ..data_types.nuscenes_annotation import NuscenesAnnotation
from ..data_types.nuscenes_camera import NuscenesCamera


def process_raw_nuscenes(dir: "str"):
    """Ingest NuScenes dataset into database."""
    df_sample_data, df_sample_annotation = _process_raw_nuscenes(dir)
    sample_data = df_sample_data.to_dict("records")
    sample_annotations = df_sample_annotation.to_dict("records")

    sample_annotations_partitioned = _partition_camera(sample_annotations, sample_data)

    camera_map: "dict[CameraKey, list[NuscenesCamera]]" = {}
    print("Indexing Cameras by Camera Id")
    for cc in tqdm(sample_data, total=len(sample_data)):
        key = CameraKey(scene=cc["scene_name"], channel=cc["channel"])
        if key not in camera_map:
            camera_map[key] = []
        camera_map[key].append(NuscenesCamera(**{str(k): v for k, v in cc.items()}))

    for v in camera_map.values():
        v.sort(key=lambda x: x.timestamp)

    annotations_map: "dict[CameraKey, list[NuscenesAnnotation]]" = {
        k: [] for k in camera_map.keys()
    }
    print("Indexing Annotations by Camera Id")
    for a in tqdm(sample_annotations_partitioned, total=len(sample_annotations_partitioned)):
        sd_tokens = a["sample_data_tokens"]
        channels = a["channels"]
        assert len(sd_tokens) == len(channels), (sd_tokens, channels)
        for sdt, c in zip(sd_tokens, channels):
            key = CameraKey(scene=a["scene_name"], channel=c)
            annotations_map[key].append(
                NuscenesAnnotation(
                    sample_data_token=sdt,
                    channel=c,
                    **a,
                )
            )

    return annotations_map, camera_map


def unique(data: "list[dict]", key: str = "token"):
    return {d[key] for d in data}


def normalize_angle(angle: "float | int") -> float:
    while angle > math.pi:
        angle -= math.tau
    while angle < -math.pi:
        angle += math.tau
    assert -math.pi <= angle <= math.pi
    return angle


def index(data: "list[dict]", key: str = "token") -> "dict[Any, dict]":
    return {d[key]: d for d in data}


def get_heading_from_north(rotation: "Quaternion"):
    yaw = rotation.yaw_pitch_roll[0]
    return normalize_angle(yaw - (math.pi / 2))


def get_camera_rotation(
    camera_rotation: "list[float]", ego_rotation: "list[float]"
) -> "npt.NDArray":
    return (Quaternion(ego_rotation) * Quaternion(camera_rotation)).q


def get_camera_position(
    camera_translation: "list[float]",
    ego_translation: "list[float]",
    ego_rotation: "list[float]",
) -> "npt.NDArray":
    rotated_offset = Quaternion(ego_rotation).rotate(np.array(camera_translation))
    return np.array(ego_translation) + rotated_offset


def get_heading(rotation: "Quaternion"):
    yaw = rotation.yaw_pitch_roll[0]
    return normalize_angle(yaw)


ROT = Quaternion(axis=[1, 0, 0], angle=np.pi / 2)


def get_camera_heading(rotation: "Quaternion"):
    rot = ROT.rotate(rotation)
    assert isinstance(rot, Quaternion)
    return -get_heading(rot) + math.pi / 2


def _process_raw_nuscenes(dir: "str"):
    """Process raw NuScenes dataset."""
    with open(os.path.join(dir, "calibrated_sensor.json")) as f:
        calibrated_sensor_json = json.load(f)
    with open(os.path.join(dir, "category.json")) as f:
        category_json = json.load(f)
    with open(os.path.join(dir, "sample.json")) as f:
        sample_json = json.load(f)
    with open(os.path.join(dir, "sample_data.json")) as f:
        sample_data_json = json.load(f)
    with open(os.path.join(dir, "sample_annotation.json")) as f:
        sample_annotation_json = json.load(f)
    with open(os.path.join(dir, "instance.json")) as f:
        instance_json = json.load(f)
    with open(os.path.join(dir, "scene.json")) as f:
        scene_json = json.load(f)
    with open(os.path.join(dir, "ego_pose.json")) as f:
        ego_pose_json = json.load(f)
    with open(os.path.join(dir, "sensor.json")) as f:
        sensor_json = json.load(f)
    with open(os.path.join(dir, "log.json")) as f:
        log_json = json.load(f)
    print("Loaded json files")

    sample_data_filter = [s for s in sample_data_json if s["fileformat"] == "jpg"]

    sample_tokens = unique(sample_data_filter, "sample_token")
    sample_filter = [
        {
            "sample_token": s["token"],
            "scene_token": s["scene_token"],
            "sample_timestamp": s["timestamp"],
        }
        for s in sample_json
        if s["token"] in sample_tokens
    ]
    # len(sample_filter)

    calibrated_sensor_tokens = unique(sample_data_filter, "calibrated_sensor_token")
    calibrated_sensor_filter = [
        {
            "calibrated_sensor_token": c["token"],
            "camera_translation": c["translation"],
            "camera_rotation": c["rotation"],
            "camera_intrinsic": c["camera_intrinsic"],
            "sensor_token": c["sensor_token"],
        }
        for c in calibrated_sensor_json
        if c["token"] in calibrated_sensor_tokens
    ]
    # len(calibrated_sensor_filter)

    sensor_tokens = unique(calibrated_sensor_filter, "sensor_token")
    sensor_filter = [
        {"sensor_token": s["token"], "channel": s["channel"], "modality": s["modality"]}
        for s in sensor_json
        if s["token"] in sensor_tokens
    ]

    ego_pose_tokens = unique(sample_data_filter, "ego_pose_token")
    ego_pose_filter = [
        {
            "ego_pose_token": e["token"],
            "ego_translation": e["translation"],
            "ego_rotation": e["rotation"],
        }
        for e in ego_pose_json
        if e["token"] in ego_pose_tokens
    ]
    # len(ego_pose_filter)

    scene_tokens = unique(sample_filter, "scene_token")
    scene_filter = [
        {
            "scene_token": s["token"],
            "scene_name": s["name"],
            "log_token": s["log_token"],
        }
        for s in scene_json
        if s["token"] in scene_tokens
    ]
    # len(scene_filter)

    log_tokens = unique(scene_filter, "log_token")
    log_filter = [
        {
            "log_token": lg["token"],
            "location": lg["location"],
        }
        for lg in log_json
        if lg["token"] in log_tokens
    ]
    # len(log_filter)

    log_map = index(log_filter, "log_token")
    sample_map = index(sample_filter, "sample_token")
    calibrated_sensor_map = index(calibrated_sensor_filter, "calibrated_sensor_token")
    ego_pose_map = index(ego_pose_filter, "ego_pose_token")
    scene_map = index(scene_filter, "scene_token")
    sensor_map = index(sensor_filter, "sensor_token")

    def s_map(s):
        sample = sample_map[s["sample_token"]]
        calibrated_sensor = calibrated_sensor_map[s["calibrated_sensor_token"]]
        ego_pose = ego_pose_map[s["ego_pose_token"]]
        scene = scene_map[sample["scene_token"]]
        sensor = sensor_map[calibrated_sensor["sensor_token"]]
        assert sensor["modality"] == "camera"

        log = log_map[scene["log_token"]]

        ego_heading = get_heading_from_north(Quaternion(ego_pose["ego_rotation"]))
        camera_heading = get_camera_heading(Quaternion(calibrated_sensor["camera_rotation"]))
        ret = {
            **s,
            **sample,
            **calibrated_sensor,
            **ego_pose,
            **scene,
            **sensor,
            **log,
            "ego_heading": ego_heading * 180 / math.pi,
            "camera_heading": normalize_angle(camera_heading + ego_heading) * 180 / math.pi,
            "camera_translation": get_camera_position(
                calibrated_sensor["camera_translation"],
                ego_pose["ego_translation"],
                ego_pose["ego_rotation"],
            ),
            "camera_rotation": get_camera_rotation(
                calibrated_sensor["camera_rotation"],
                ego_pose["ego_rotation"],
            ),
        }
        del ret["ego_pose_token"]
        del ret["calibrated_sensor_token"]
        del ret["log_token"]
        del ret["fileformat"]
        del ret["height"]
        del ret["width"]
        del ret["prev"]
        del ret["next"]
        del ret["scene_token"]
        del ret["sensor_token"]
        del ret["modality"]
        return ret

    print("Processing sample data")
    sample_data_res = [*tqdm(map(s_map, sample_data_filter), total=len(sample_data_filter))]

    # len(sample_data_res)

    sample_annotation_filter = [
        sa for sa in sample_annotation_json if sa["sample_token"] in sample_tokens
    ]
    # len(sample_annotation_filter)

    instance_tokens = unique(sample_annotation_filter, "instance_token")
    instance_filter = [
        {"instance_token": i["token"], "category_token": i["category_token"]}
        for i in instance_json
        if i["token"] in instance_tokens
    ]
    # len(instance_filter)

    category_tokens = unique(instance_filter, "category_token")
    category_filter = [
        {"category_token": c["token"], "category": c["name"]}
        for c in category_json
        if c["token"] in category_tokens
    ]
    # len(category_filter)

    instance_map = index(instance_filter, "instance_token")
    category_map = index(category_filter, "category_token")

    def sa_map(sa):
        instance = instance_map[sa["instance_token"]]
        sample = sample_map[sa["sample_token"]]
        scene = scene_map[sample["scene_token"]]
        log = log_map[scene["log_token"]]
        ret = {
            **sa,
            **instance,
            **category_map[instance["category_token"]],
            "heading": (get_heading_from_north(Quaternion(sa["rotation"]))) * 180 / math.pi,
            "location": log["location"],
            "scene_name": scene["scene_name"],
        }

        del ret["visibility_token"]
        del ret["attribute_tokens"]
        del ret["prev"]
        del ret["next"]
        del ret["num_lidar_pts"]
        del ret["num_radar_pts"]
        del ret["category_token"]

        return ret

    print("Processing sample annotation")
    sample_annotation_res = [
        *tqdm(map(sa_map, sample_annotation_filter), total=len(sample_annotation_filter))
    ]
    # len(sample_annotation_res)

    df_sample_data = pd.DataFrame(sample_data_res)
    df_sample_annotation = pd.DataFrame(sample_annotation_res)

    df_sample_data_keyframe = (
        df_sample_data[df_sample_data["is_key_frame"]][["token", "sample_token"]]
        .groupby("sample_token")
        .agg(list)
        .reset_index()
        .rename(columns={"token": "sample_data_tokens"})
    )

    df_sample_annotation = (
        df_sample_annotation.set_index("sample_token")
        .join(
            df_sample_data_keyframe.set_index("sample_token"),
            on="sample_token",
        )
        .reset_index()
    )

    df_sample_data["frame_order"] = (
        df_sample_data.groupby("scene_name")["timestamp"].rank(method="first").astype(int)
    )

    return df_sample_data, df_sample_annotation


def world2pixel(annotation, sample_data):
    ct = np.array(sample_data["camera_translation"])
    cr = Quaternion(sample_data["camera_rotation"])
    ci = np.array(sample_data["camera_intrinsic"])
    at = np.array(annotation["translation"])

    offset = at - ct  # .reshape((3, 1))
    # point_from_camera = np.dot(cr.unit.inverse.rotation_matrix, offset)
    _point_from_camera = cr.inverse.rotate(offset)
    assert isinstance(_point_from_camera, np.ndarray)
    point_from_camera = _point_from_camera.reshape((3, 1))
    if point_from_camera[2] < 0:
        return np.array([-1, -1, 0])
    assert point_from_camera.shape == (3, 1)
    point2d = np.dot(ci, point_from_camera)
    assert point2d.shape == (3, 1)

    return (point2d / point2d[2:3]).reshape((3,))


def _partition_camera(raw_annotations: "list[dict]", raw_sample_data: "list[dict]"):
    # Map from annotation token -> annotation
    annotation_map = {a["token"]: a for a in raw_annotations}
    assert len(annotation_map) == len(raw_annotations), (len(annotation_map), len(raw_annotations))

    # Map from sample data token (camera config token) -> sample data
    sample_data_map = {sd["token"]: sd for sd in raw_sample_data}
    assert len(sample_data_map) == len(raw_sample_data)

    for a in annotation_map.values():
        for sdt in a["sample_data_tokens"]:
            assert sample_data_map[sdt]["sample_token"] == a["sample_token"]

    def in_view(annotation: "dict[str, Any]"):
        def fn(sample_data_token: "str"):
            sample_data = sample_data_map[sample_data_token]
            point2d = world2pixel(annotation, sample_data)
            x, y, _ = point2d

            _, _, _z = Quaternion(sample_data["camera_rotation"]).inverse.rotate(
                np.array(annotation["translation"]) - np.array(sample_data["camera_translation"])
            )
            return (0 <= x < 1600) and (0 <= y < 900) and _z > 0

        return fn

    not_in_view = []

    def split(a):
        in_view_a = in_view(a)
        sample_data_tokens = [*filter(in_view_a, a["sample_data_tokens"])]
        channels = [sample_data_map[sdt]["channel"] for sdt in sample_data_tokens]
        # assert len(sample_data_tokens) > 0
        if len(sample_data_tokens) <= 0:
            not_in_view.append(a)
        return {
            **a,
            "sample_data_tokens": sample_data_tokens,
            "out_of_view_sample_data_tokens": [
                *filter(lambda x: not in_view_a(x), a["sample_data_tokens"])
            ],
            "channels": channels,
        }

    print("Assigning annotations to camera")
    output_annotations = [split(a) for a in tqdm(raw_annotations)]

    return output_annotations
