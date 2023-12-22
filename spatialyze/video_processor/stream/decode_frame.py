import cv2
import numpy.typing as npt

from ..video import Video
from .stream import Stream


class DecodeFrame(Stream[npt.NDArray]):
    def _stream(self, video: Video):
        cap = cv2.VideoCapture(video.videofile)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
        cap.release()
        cv2.destroyAllWindows()
        self.end()
