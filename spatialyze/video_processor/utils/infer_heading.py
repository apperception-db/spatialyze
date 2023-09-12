import math

from ..types import Float3


def infer_heading(
    curItemHeading: "float | None", prevPoint: "Float3 | None", current_point: "Float3"
):
    if curItemHeading is not None:
        return math.degrees(curItemHeading)
    if prevPoint is None:
        return None
    x1, y1, z1 = prevPoint
    x2, y2, z2 = current_point
    # 0 is north (y-axis) and counter clockwise
    return math.degrees(math.atan2(y2 - y1, x2 - x1)) - 90
