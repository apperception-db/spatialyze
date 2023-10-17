import cv2

from .reusable import reusable
from .stream import Stream
from ..video.video import Video
from .data_types import Frame

@reusable
class DecodeFrame(Stream[Frame]):
    def stream(self, video: Video):
        cap = cv2.VideoCapture(video.videofile)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            yield Frame(frame)
        cap.release()
        cv2.destroyAllWindows()
