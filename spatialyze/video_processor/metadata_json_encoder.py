import json
from typing import Any, Type

import numpy as np
import torch

from .stages.stage import Stage


class MetadataJSONEncoder(json.JSONEncoder):
    def default(self, o: "Any") -> "Any":
        subclasses = _get_all_subclasses(Stage)

        for cls in subclasses:
            encoded = cls.encode_json(o)
            if encoded is not None:
                return encoded

        if isinstance(o, torch.Tensor):
            return o.tolist()
        if isinstance(o, np.ndarray):
            return o.tolist()

        return super().default(o)


def _get_all_subclasses(cls: Type[Stage]) -> list[Type[Stage]]:
    return [cls, *sum([_get_all_subclasses(subcls) for subcls in cls.__subclasses__()], [])]
