import cv2
import numpy.typing as npt

from ..video.video import Video
from .reusable import reusable
from .stream import Stream


@reusable
class DecodeFrame(Stream[npt.NDArray]):
    def stream(self, video: Video):
        cap = cv2.VideoCapture(video.videofile)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
        cap.release()
        cv2.destroyAllWindows()
