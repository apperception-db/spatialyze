import logging
import time
from typing import Callable, List, Tuple

import postgis
import shapely
import shapely.geometry
import shapely.wkb
import torch
from bitarray import bitarray
from psycopg2 import sql

from spatialyze.database import database

from ...camera_config import CameraConfig
from ...payload import Payload
from ...types import DetectionId
from ...video import Video
from ..detection_2d.detection_2d import Detection2D
from ..detection_2d.detection_2d import Metadatum as D2DMetadatum
from ..detection_3d import Detection3D
from ..in_view.in_view import get_views
from ..stage import Stage
from .detection_estimation import (
    DetectionInfo,
    SamplePlan,
    construct_all_detection_info,
    generate_sample_plan,
    obj_detection,
)
from .utils import get_ego_avg_speed, trajectory_3d

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


DetectionEstimationMetadatum = List[DetectionInfo]


class DetectionEstimation(Stage[DetectionEstimationMetadatum]):
    def __init__(self, predicate: "Callable[[DetectionInfo], bool]" = lambda _: True):
        self.predicates = [predicate]
        self._benchmark = []
        super(DetectionEstimation, self).__init__()

    def add_filter(self, predicate: "Callable[[DetectionInfo], bool]"):
        self.predicates.append(predicate)

    def _run(self, payload: "Payload"):
        start_time = time.time()
        if Detection2D.get(payload) is None:
            raise Exception()

        keep = bitarray(len(payload.video))
        keep[:] = 1

        ego_trajectory = [trajectory_3d(v.ego_translation, v.timestamp) for v in payload.video]
        ego_speed = get_ego_avg_speed(ego_trajectory)
        logger.info(f"ego_speed: {ego_speed}")
        if ego_speed < 2:
            return keep, {DetectionEstimation.classname(): [[]] * len(keep)}

        ego_views = get_ego_views(payload.video)
        ego_views = [shapely.wkb.loads(view.to_ewkb(), hex=True) for view in ego_views]

        skipped_frame_num = []
        next_frame_num = 0
        action_type_counts = {}
        total_detection_time = []
        total_sample_plan_time = []
        dets = Detection3D.get(payload)
        assert dets is not None, [*payload.metadata.keys()]
        metadata: "list[DetectionEstimationMetadatum]" = []
        # investigation_frame_nums = []
        current_fps = payload.video.fps
        for i in Stage.tqdm(range(len(payload.video) - 1)):
            current_ego_config = payload.video[i]

            if i != next_frame_num:
                skipped_frame_num.append(i)
                metadata.append([])
                continue

            next_frame_num = i + 1

            det, _, dids = dets[i]
            if new_car(dets, i, i + 5) <= i + 1:
                # will not map segment if cannot skip in the first place
                metadata.append([])
                continue

            start_detection_time = time.time()
            logger.info(f"current frame num {i}")
            all_detection_info, times = construct_estimated_all_detection_info(
                det, dids, current_ego_config, ego_trajectory
            )
            total_detection_time.append(
                (time.time() - start_detection_time, len(det), len(all_detection_info), times)
            )

            all_detection_info_pruned, det = prune_detection(
                all_detection_info, det, self.predicates
            )

            if len(det) == 0 or len(all_detection_info_pruned) == 0:
                # skipped_frame_num.append(i)
                metadata.append([])
                continue

            start_generate_sample_plan = time.time()
            next_sample_plan, _ = generate_sample_plan_once(
                payload.video, next_frame_num, ego_views, all_detection_info_pruned, fps=current_fps
            )
            total_sample_plan_time.append(time.time() - start_generate_sample_plan)
            next_frame_num = next_sample_plan.get_next_frame_num()
            next_frame_num = new_car(dets, i, next_frame_num)
            logger.info(f"founded next_frame_num {next_frame_num}")
            metadata.append(all_detection_info)

            next_action_type = next_sample_plan.get_action_type()
            if next_action_type not in action_type_counts:
                action_type_counts[next_action_type] = 0
            action_type_counts[next_action_type] += 1

        # TODO: ignore the last frame ->
        metadata.append([])
        # skipped_frame_num.append(len(payload.video) - 1)

        #     times.append([t2 - t1 for t1, t2 in zip(t[:-1], t[1:])])
        # logger.info(np.array(times).sum(axis=0))
        logger.info(f"sorted_ego_config_length {len(payload.video)}")
        logger.info(f"number of skipped {len(skipped_frame_num)}")
        logger.info(action_type_counts)
        total_run_time = time.time() - start_time
        logger.info(f"total_run_time {total_run_time}")
        logger.info(f"total_detection_time {sum(t for t, *_ in total_detection_time)}")
        logger.info(f"total_generate_sample_plan_time {sum(total_sample_plan_time)}")

        self._benchmark.append(
            {
                "name": payload.video.videofile,
                "skipped_frames": skipped_frame_num,
                "actions": action_type_counts,
                "runtime": total_run_time,
                "detection": total_detection_time,
                "sample_plan": total_sample_plan_time,
            }
        )

        for f in skipped_frame_num:
            keep[f] = 0

        return keep, {DetectionEstimation.classname(): metadata}


def new_car(dets: "list[D2DMetadatum]", cur: "int", nxt: "int"):
    len_det = len(dets[cur][0])
    for j in range(cur + 1, min(nxt + 1, len(dets))):
        future_det = dets[j][0]
        if len(future_det) > len_det:
            return j
    return nxt


def objects_count_change(dets: "list[D2DMetadatum]", cur: "int", nxt: "int"):
    det, _, _ = dets[cur]
    for j in range(cur + 1, min(nxt + 1, len(dets))):
        future_det, _, _ = dets[j]
        if len(future_det) > len(det):
            return j
        elif len(future_det) < len(det):
            return max(j - 1, cur + 1)
    return nxt


def get_ego_views(video: "Video") -> "list[postgis.Polygon]":
    indices, view_areas = get_views(video, distance=100, skip=False)
    views_raw = database.execute(
        sql.SQL(
            """
    SELECT index, ST_ConvexHull(points)
    FROM UNNEST (
        {view_areas},
        {indices}::int[]
    ) AS ViewArea(points, index)
    """
        ).format(
            view_areas=sql.Literal(view_areas),
            indices=sql.Literal(indices),
        )
    )

    idxs_set = set(idx for idx, _ in views_raw)
    idxs_all = set(range(len(video)))
    assert idxs_set == idxs_all, (idxs_set.difference(idxs_all), idxs_all.difference(idxs_set))
    return [v for _, v in sorted(views_raw)]


def prune_detection(
    detection_info: "list[DetectionInfo]",
    det: "torch.Tensor",
    predicates: "List[Callable[[DetectionInfo], bool]]",
):
    # TODO (fge): this is a hack before fixing the mapping between det and detection_info
    return detection_info, det
    if len(detection_info) == 0:
        return detection_info, det
    pruned_detection_info: "list[DetectionInfo]" = []
    pruned_det: "list[torch.Tensor]" = []
    for d, di in zip(det, detection_info):
        if all([predicate(di) for predicate in predicates]):
            pruned_detection_info.append(di)
            pruned_det.append(d)
    logger.info("length before pruning", len(det))
    logger.info("length after pruning", len(pruned_det))
    return pruned_detection_info, pruned_det


def generate_sample_plan_once(
    video: "Video",
    next_frame_num: "int",
    ego_views: "list[shapely.geometry.Polygon]",
    all_detection_info: "list[DetectionInfo] | None" = None,
    fps: "int" = 13,
) -> "Tuple[SamplePlan, None]":
    assert all_detection_info is not None
    next_sample_plan = generate_sample_plan(
        video, next_frame_num, all_detection_info, ego_views, 50, fps=fps
    )
    return next_sample_plan, None


def construct_estimated_all_detection_info(
    detections: "torch.Tensor",
    detection_ids: "list[DetectionId]",
    ego_config: "CameraConfig",
    ego_trajectory: "list[trajectory_3d]",
) -> "list[DetectionInfo]":
    _times = time.time()
    all_detections = []
    for det, did in zip(detections, detection_ids):
        bbox = det[:4]
        # conf = det[4]
        # obj_cls = det[5]
        # bbox3d_from_camera = det[12:18]
        bbox3d = det[6:12]
        x, y, x2, y2 = list(map(int, bbox))
        w = x2 - x
        h = y2 - y
        car_loc2d = (x + w // 2, y + h // 2)
        car_bbox2d = ((x, y), (x2, y2))
        left3d, right3d = bbox3d[:3], bbox3d[3:]
        car_loc3d = tuple(map(float, (left3d + right3d) / 2))
        assert len(car_loc3d) == 3
        car_bbox3d = (tuple(map(float, left3d)), tuple(map(float, right3d)))
        all_detections.append(obj_detection(did, car_loc3d, car_loc2d, car_bbox3d, car_bbox2d))
    all_detection_info, times = construct_all_detection_info(
        ego_config, ego_trajectory, all_detections
    )
    return all_detection_info, [_times] + times
