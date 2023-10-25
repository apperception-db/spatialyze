import logging
import time
from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

import shapely
import shapely.wkb

from ..stages.detection_estimation import (
    construct_estimated_all_detection_info,
    generate_sample_plan_once,
    get_ego_avg_speed,
    get_ego_views,
    trajectory_3d,
)
from ..video import Video
from .data_types import Detection3D, Skip, skip
from .stream import Stream

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


class ExitFrameSampler(Stream[bool]):
    def __init__(self, detections: Stream[Detection3D]):
        self.detections = detections

    def _stream(self, video: Video):
        start_time = time.time()

        ego_trajectory = [trajectory_3d(v.ego_translation, v.timestamp) for v in video]
        ego_speed = get_ego_avg_speed(ego_trajectory)
        logger.info(f"ego_speed: {ego_speed}")
        if ego_speed < 2:
            return self.detections.stream(video)

        ego_views = get_ego_views(video)
        # ego_views = [shapely.wkb.loads(view.to_ewkb(), hex=True) for view in ego_views]

        skipped_frame_num = []
        next_frame_num = 0
        action_type_counts = {}
        total_detection_time = []
        total_sample_plan_time = []
        current_fps = video.fps

        detections = FutureIterator(self.detections.stream(video))
        for i, (config, detection) in enumerate(zip(video, detections)):
            if i == len(video) - 1:
                yield True
                continue

            if i != next_frame_num or isinstance(detection, Skip):
                yield False
                continue

            next_frame_num = i + 1

            det, _, dids = detection
            if new_car(detections, min(5, len(video) - i - 1)) <= 1:
                # do not map segment if cannot skip in the first place
                yield True
                continue

            start_detection_time = time.time()
            logger.info(f"current frame num {i}")
            all_detection_info, times = construct_estimated_all_detection_info(
                det, dids, config, ego_trajectory
            )
            total_detection_time.append(
                (time.time() - start_detection_time, len(det), len(all_detection_info), times)
            )

            # all_detection_info_pruned, det = prune_detection(
            #     all_detection_info, det, self.predicates
            # )
            all_detection_info_pruned = all_detection_info

            if len(det) == 0 or len(all_detection_info_pruned) == 0:
                yield True
                continue

            start_generate_sample_plan = time.time()
            next_sample_plan, _ = generate_sample_plan_once(
                video, next_frame_num, ego_views, all_detection_info_pruned, fps=current_fps
            )
            total_sample_plan_time.append(time.time() - start_generate_sample_plan)
            next_frame_num = next_sample_plan.get_next_frame_num()
            next_frame_num = i + new_car(detections, min(next_frame_num, len(video) - 1) - i)
            logger.info(f"founded next_frame_num {next_frame_num}")
            yield True

            next_action_type = next_sample_plan.get_action_type()
            if next_action_type not in action_type_counts:
                action_type_counts[next_action_type] = 0
            action_type_counts[next_action_type] += 1

        #     times.append([t2 - t1 for t1, t2 in zip(t[:-1], t[1:])])
        # logger.info(np.array(times).sum(axis=0))
        logger.info(f"sorted_ego_config_length {len(video)}")
        logger.info(f"number of skipped {len(skipped_frame_num)}")
        logger.info(action_type_counts)
        total_run_time = time.time() - start_time
        logger.info(f"total_run_time {total_run_time}")
        logger.info(f"total_detection_time {sum(t for t, *_ in total_detection_time)}")
        logger.info(f"total_generate_sample_plan_time {sum(total_sample_plan_time)}")

        # self._benchmark.append(
        #     {
        #         "name": video.videofile,
        #         "skipped_frames": skipped_frame_num,
        #         "actions": action_type_counts,
        #         "runtime": total_run_time,
        #         "detection": total_detection_time,
        #         "sample_plan": total_sample_plan_time,
        #     }
        # )


T = TypeVar("T")


class FutureIterator(Generic[T], Iterator[T]):
    def __init__(self, it: Iterable[T]):
        self.it = iter(it)
        self.idx = -1
        self.mem: list[T | None] = []

    def __next__(self):
        if self.idx >= 0:
            self.mem[self.idx] = None
        self.idx += 1
        while len(self.mem) <= self.idx:
            self.mem.append(next(self.it))
        return self.mem[self.idx]

    def __getitem__(self, item: int):
        try:
            while len(self.mem) <= self.idx + item:
                self.mem.append(next(self.it))
            return self.mem[self.idx + item]
        except StopIteration:
            if item == 0:
                raise StopIteration
            return None


def new_car(detections: FutureIterator[Detection3D | Skip], nxt: int):
    detection = detections[0]
    assert detection is not None
    assert not isinstance(detection, Skip)
    len_det = len(detection[0])
    for i in range(1, nxt + 1):
        det = detections[i]
        assert not isinstance(det, Skip)
        if det is None:
            return i - 1
        future_det = det[0]
        if len(future_det) > len_det:
            return i
    return nxt
