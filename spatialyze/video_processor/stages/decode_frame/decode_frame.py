from typing import TYPE_CHECKING

import cv2
import numpy as np
import numpy.typing as npt

from ..stage import Stage

if TYPE_CHECKING:
    from ...payload import Payload


class DecodeFrame(Stage[np.ndarray]):
    def _run(self, payload: "Payload"):
        metadata: "list[npt.NDArray]" = []

        video = cv2.VideoCapture(payload.video.videofile)
        n_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        for _ in DecodeFrame.tqdm(range(n_frames)):
            assert video.isOpened()
            frame = video.read()[1]
            metadata.append(frame)
        assert len(metadata) == len(payload.video)
        assert not video.read()[0]
        video.release()
        cv2.destroyAllWindows()

        return None, {self.classname(): metadata}
