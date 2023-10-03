import numpy as np
import pandas as pd
import torch

from ..detection_2d.ground_truth import rotate, _3d_to_2d, yolo_classes, CLASS_MAP
from ...payload import Payload
from ...types import DetectionId
from . import Detection3D, Metadatum


class GroundTruthDetection3D(Detection3D):
    def __init__(self, df_annotations: "pd.DataFrame"):
        annotations: "list[dict]" = df_annotations.to_dict("records")
        self.annotation_map: "dict[str, list[dict]]" = {}

        classes: "set[str]" = set()
        for a in annotations:
            fids: "list[str]" = a["sample_data_tokens"]
            for fid in fids:
                if fid not in self.annotation_map:
                    self.annotation_map[fid] = []
                self.annotation_map[fid].append(a)

            classes.add(a["category"])

        self.id_to_classes = [*classes]
        self.class_to_id = {c: i for i, c in enumerate(self.id_to_classes)}

    def _run(self, payload: "Payload"):
        metadata: "list[Metadatum | None]" = []
        dimension = payload.video.dimension
        for i, cc in enumerate(payload.video._camera_configs):
            fid = cc.frame_id
            assert isinstance(fid, str)
            annotations = self.annotation_map.get(fid, [])
            tensor = []
            ids = []
            for a in annotations:
                if a["category"] not in CLASS_MAP:
                    continue

                left, top, right, bottom = _3d_to_2d(
                    a["translation"],
                    a["size"],
                    a["rotation"],
                    cc.camera_translation,
                    cc.camera_rotation,
                    cc.camera_intrinsic,
                )

                left = max(0, min(left, dimension[0] - 1))
                right = max(0, min(right, dimension[0] - 1))
                top = max(0, min(top, dimension[1] - 1))
                bottom = max(0, min(bottom, dimension[1] - 1))

                bbox3d_left = a["translation"]
                bbox3d_right = a["translation"]

                bbox3d_from_camera_left = rotate(
                    (np.array(a["translation"]) - np.array(cc.camera_translation)).T,
                    cc.camera_rotation.inverse
                )
                bbox3d_from_camera_right = bbox3d_from_camera_left

                d2d = [left, top, right, bottom]
                tensor.append([
                    *d2d,
                    1,
                    CLASS_MAP[a["category"]],
                    *bbox3d_left,
                    *bbox3d_right,
                    *bbox3d_from_camera_left,
                    *bbox3d_from_camera_right
                ])
                ids.append(a["token"])

            if len(tensor) == 0:
                metadata.append(Metadatum(torch.Tensor([]), yolo_classes, []))
            else:
                metadata.append(
                    Metadatum(torch.Tensor(tensor), yolo_classes, [DetectionId(i, _id) for _id in ids])
                )

        return None, {self.classname(): metadata}
