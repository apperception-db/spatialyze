from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

import numpy as np
import numpy.typing as npt
import shapely.errors
import torch
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Polygon

from spatialyze.video_processor.types import DetectionId
from spatialyze.video_processor.video import Video
from spatialyze.video_processor.stream.data_types import Detection2D, Skip
from spatialyze.video_processor.stream.stream import Stream

FILE = Path(__file__).resolve()
SPATIALYZE = FILE.parent.parent.parent.parent
WEIGHTS = SPATIALYZE / "weights"
REID_WEIGHTS = WEIGHTS / "osnet_x0_25_msmt17.pt"
# EMPTY_DETECTION = torch.Tensor(0, 6)
EMPTY_DETECTION = np.empty((0, 6))


@dataclass
class TrackingResult:
    detection_id: DetectionId
    object_id: int
    confidence: float | np.float32
    bbox: torch.Tensor | npt.NDArray
    object_type: str
    next: "TrackingResult | None" = field(default=None, compare=False, repr=False)
    prev: "TrackingResult | None" = field(default=None, compare=False, repr=False)


class Detection(NamedTuple):
    did: DetectionId
    det: npt.NDArray


Sequence = list[Detection]


class SORT(Stream[list[TrackingResult]]):
    def __init__(self, detections: Stream[Detection2D]):
        self.detection2ds = detections

    def _stream(self, video: Video):
        sequences: list[Sequence] = []
        activeSequences: dict[int, Sequence] = {}

        with torch.no_grad():
            for frameIdx, dlist in enumerate(self.detection2ds.stream(video)):
                if not isinstance(dlist, Skip):
                    detectionMap: list[Detection] = [
                        # Detection(did, det.detach().cpu().numpy()) for det, _, did in zip(*dlist)
                        Detection(
                            did, det if isinstance(det, np.ndarray) else det.detach().cpu().numpy()
                        )
                        for det, _, did in zip(*dlist)
                    ]

                    matches, unmatched = hungarianMatcher(activeSequences, detectionMap)
                    for seqID, detection in matches.items():
                        sequences[seqID].append(detection)

                    # new sequences for unmatched detections
                    for detID in unmatched:
                        seqID = len(sequences)
                        seq = [detectionMap[detID]]
                        activeSequences[seqID] = seq
                        sequences.append(seq)

                # remove old active sequences
                for seqID, seq in [*activeSequences.items()]:
                    lastTime = seq[-1].did.frame_idx
                    if frameIdx - lastTime < 10:
                        continue

                    yield _process_track(seq, seqID)
                    del activeSequences[seqID]
        self.end()


def _process_track(track: Sequence, tid: int):
    def tracking_result(detection: Detection):
        did, det = detection
        # return TrackingResult(did, tid, det[6], torch.from_numpy(det), "car")
        return TrackingResult(did, tid, det[6], det, "car")

    # Sort track by frame idx
    _track = map(tracking_result, track)
    _track = sorted(_track, key=lambda d: d.detection_id.frame_idx)

    # Link track
    for before, after in zip(_track[:-1], _track[1:]):
        before.next = after
        after.prev = before

    return _track


def hungarianMatcher(
    sequences: dict[int, Sequence], detections: list[Detection]
) -> tuple[dict[int, Detection], list[int]]:
    M, N = len(sequences), len(detections)
    if M == 0 or N == 0:
        return {}, list(range(N))

    sequenceList: list[Sequence] = []
    sequenceIDs: list[int] = []
    for id, seq in sequences.items():
        sequenceList.append(seq)
        sequenceIDs.append(id)

    detectionList: list[Detection] = detections
    costMatrix = np.empty((M, N))
    for i, seq in enumerate(sequenceList):
        seq_det = seq[-1].det[6:]
        seqRect = Polygon((seq_det[0:2], seq_det[3:5], seq_det[6:8], seq_det[9:11]))
        for j, det in enumerate(detectionList):
            det_det = det.det[6:]
            curRect = Polygon((det_det[0:2], det_det[3:5], det_det[6:8], det_det[9:11]))
            try:
                intersection = seqRect.intersection(curRect).area
                union = seqRect.union(curRect).area
            except shapely.errors.TopologicalError as e:
                print(e)
                print(seqRect, curRect)
                raise e
            if union == 0:
                print(seqRect, curRect)
            iou = intersection / union

            if iou > 0.99:
                cost = 0.01
            elif iou > 0.1:
                cost = 1 - iou
            else:
                cost = 10

            costMatrix[i, j] = cost
    inds: tuple[list[int], list[int]] = linear_sum_assignment(costMatrix)
    seq_ind, det_ind = inds

    matches: dict[int, Detection] = {}
    matched: set[int] = set()
    for i, j in zip(seq_ind, det_ind):
        if j < 0 or costMatrix[i, j] > 0.9:
            continue
        matches[sequenceIDs[i]] = detectionList[j]
        matched.add(j)

    return matches, list(set(range(N)) - matched)
