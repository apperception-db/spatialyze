from typing import NamedTuple


class CameraKey(NamedTuple):
    scene: "str"
    channel: "str"
    
    def __str__(self):
        return f"{self.scene}:{self.channel}"