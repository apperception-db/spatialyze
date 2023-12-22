import os

from ..video import Video
from .stream import Stream


class ListImages(Stream[str]):
    def _stream(self, video: Video):
        directory = video.videofile
        for filename in sorted(os.listdir(directory)):
            yield os.path.join(directory, filename)
        self.end()
