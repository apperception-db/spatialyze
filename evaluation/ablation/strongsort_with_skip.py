import copy
from pathlib import Path
from typing import Literal

import numpy.typing as npt
import torch

from spatialyze.video_processor.modules.yolo_tracker.trackers.multi_tracker_zoo import StrongSORT, create_tracker
from spatialyze.video_processor.modules.yolo_tracker.yolov5.utils.torch_utils import select_device
from spatialyze.video_processor.payload import Payload
from spatialyze.video_processor.types import DetectionId
from spatialyze.video_processor.stages.decode_frame.decode_frame import DecodeFrame
from spatialyze.video_processor.stages.detection_2d.detection_2d import Detection2D, Metadatum
from spatialyze.video_processor.stages.stage import Stage

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
reid_weights = WEIGHTS / "osnet_x0_25_msmt17.pt"


Method = Literal["increment-ages", "update-empty"]


class StrongSORTWithSkip(Stage["list[tuple[int, DetectionId, DetectionId | None]]"]):
    def __init__(self, method: "Method" = "increment-ages", skip: "int" = 32):
        self.method: "Method" = method
        self.skip: "int" = skip

    def _run(self, payload: "Payload"):
        dets = Detection2D.get(payload)
        assert dets is not None

        imgs = DecodeFrame.get(payload)
        assert imgs is not None

        class_map = dets[0].class_map
        assert class_map is not None
        vehicle_cids = set(
            i
            for i, d in enumerate(class_map)
            if d in ["car", "bus", "truck", "motorcycle", "bicycle", "person"]
        )
        device = select_device("")
        strongsort = create_tracker("strongsort", reid_weights, device, False)
        assert isinstance(strongsort, StrongSORT)
        assert hasattr(strongsort, "tracker")
        assert hasattr(strongsort.tracker, "camera_update")

        skippable: "list[list[tuple[int, DetectionId, DetectionId | None, bool]]]" = [
            [] for _ in range(len(payload.video))
        ]
        prev_frame = None
        with torch.no_grad():
            if hasattr(strongsort, "model") and hasattr(strongsort.model, "warmup"):
                strongsort.model.warmup()

            strongsort_copies: "list[StrongSORT]" = []
            assert len(dets) == len(imgs)
            for didx, ((det, names, dids), im0s) in StrongSORTWithSkip.tqdm(
                enumerate(zip(dets, imgs)), total=len(dets), desc="ground truth"
            ):
                prev_frame = process_one_frame(
                    strongsort, Metadatum(det, names, dids), im0s, prev_frame
                )
                strongsort_copies.append(copy.deepcopy(strongsort))

            all_tracks = strongsort.tracker.tracks + strongsort.tracker.deleted_tracks
            mem: "dict[tuple[int, int], dict[int, list[DetectionId]]]" = {}
            for tidx, track in enumerate(all_tracks):
                # Looking at the track with `tracking_id`
                track_id = track.track_id
                assert isinstance(track_id, int), type(track_id)
                # print("track", track_id, len(strongsort.tracker.tracks), len(strongsort.tracker.deleted_tracks), len(all_tracks))

                # Only consider vehicles because these are the only types of objects that
                # Detection Estimation cares about.
                classes = track.class_ids
                vehicles = [c for c in classes if int(c) in vehicle_cids]
                if len(vehicles) / len(classes) < 0.7:
                    continue

                if len(track.detection_ids) <= 2:
                    continue

                threshold: "list[tuple[DetectionId, DetectionId | None, bool]]" = []
                # For every starting point (except the last one)
                dids: "list[DetectionId]" = sorted(track.detection_ids, key=by_frameidx)
                for didx, did in StrongSORTWithSkip.tqdm(
                    enumerate(dids[:-1]), total=len(dids) - 1, desc=f"{tidx + 1}/{len(all_tracks)}"
                ):
                    fid = did.frame_idx
                    # Choose the copy of StrongSORT that has visit up to did.frame_idx
                    ss = strongsort_copies[fid]

                    can_skip_to = None
                    skip_failed = False
                    for _did in dids[didx + 1 :]:
                        if _did.frame_idx - did.frame_idx > self.skip:
                            break

                        # Configm that did is the latest detection on the track of interest.
                        _all_tracks = ss.tracker.tracks + ss.tracker.deleted_tracks
                        for _track in _all_tracks:
                            if _track.track_id == track_id:
                                assert did == _track.detection_ids[-1], (did, _track.detection_ids)

                        # Confirm that the target detection id (_did) is not already in any of the existing tracks
                        for track in ss.tracker.tracks + ss.tracker.deleted_tracks:
                            assert all(id for id in track.detection_ids if id != _did)

                        # Check if we can skip up to the frame before _did and still does not lose track
                        if test_skip(ss, dets, imgs, track_id, did, _did, self.method, mem):
                            can_skip_to = _did
                        else:
                            skip_failed = True
                            break

                    if can_skip_to is not None:
                        threshold.append((did, can_skip_to, skip_failed))
                    else:
                        threshold.append((did, None, skip_failed))

                for did_from, did_to, skip_failed in threshold:
                    fid = did_from.frame_idx
                    skippable[fid].append((track_id, did_from, did_to, skip_failed))

        return None, {self.classname(): skippable}


def by_frameidx(d: "DetectionId"):
    return d.frame_idx


def test_skip(
    ss: "StrongSORT",
    dets: "list[Metadatum]",
    imgs: "list[npt.NDArray]",
    track_id: "int",
    start_did: "DetectionId",
    target_did: "DetectionId",
    method: "Method",
    mem: "dict[tuple[int, int], dict[int, list[DetectionId]]]",
) -> "bool":
    key = start_did.frame_idx, target_did.frame_idx

    if key not in mem:
        mem[key] = _skip(ss, dets, imgs, start_did, target_did, method)

    return target_did in mem[key].get(track_id, [])


def _skip(
    ss: "StrongSORT",
    dets: "list[Metadatum]",
    imgs: "list[npt.NDArray]",
    start_did: "DetectionId",
    target_did: "DetectionId",
    method: "Method",
) -> "dict[int, list[DetectionId]]":
    start_fid = start_did.frame_idx
    target_fid = target_did.frame_idx

    ss = copy.deepcopy(ss)

    # Confirm that the target detection_id is not already in any of the existing tracks
    # assert target_detection_id not in detections[idx].detection_ids
    for track in ss.tracker.tracks + ss.tracker.deleted_tracks:
        assert all(id for id in track.detection_ids if id != target_did)

    # Skip to the desired frame
    prev_frame = imgs[start_fid]
    for _idx in range(start_fid + 1, target_fid):
        curr_frame = imgs[_idx].copy()
        if prev_frame is not None and curr_frame is not None:
            ss.tracker.camera_update(prev_frame, curr_frame, cache=True)
        if method == "increment-ages":
            ss.increment_ages()
        else:
            ss.update(torch.Tensor(0, 6), [], curr_frame)
        prev_frame = curr_frame

    # Run StrongSORT on the desired frame
    curr_frame = imgs[target_fid].copy()
    if prev_frame is not None and curr_frame is not None:
        ss.tracker.camera_update(prev_frame, curr_frame, cache=True)

    ds = dets[target_fid]
    ss.update(ds.detections.cpu(), ds.detection_ids, curr_frame)

    all_tracks = ss.tracker.tracks + ss.tracker.deleted_tracks
    return {t.track_id: t.detection_ids for t in all_tracks}


def process_one_frame(
    ss: "StrongSORT",
    detection: "Metadatum",
    im0s: "npt.NDArray",
    prev_frame: "npt.NDArray | None",
) -> "npt.NDArray":
    det, _, dids = detection
    im0 = im0s.copy()
    curr_frame = im0

    if prev_frame is not None and curr_frame is not None:
        ss.tracker.camera_update(prev_frame, curr_frame, cache=True)

    ss.update(det.cpu(), dids, im0)
    return curr_frame
