import datetime
from dataclasses import dataclass, field
from typing import Literal

from ...types import DetectionId, Float2, Float3, Float22

"""
Action:
    trajectory so far
    next timestamp to sample
    next frame to sample and it's frame num
    Heuristic to sample
"""

ActionType = Literal["ego_exit_segment", "car_exit_segment", "exit_view", "meet_up"]

EGO_EXIT_SEGMENT: "ActionType" = "ego_exit_segment"
CAR_EXIT_SEGMENT: "ActionType" = "car_exit_segment"
EXIT_VIEW: "ActionType" = "exit_view"
MEET_UP: "ActionType" = "meet_up"
OBJ_BASED_ACTION: "list[ActionType]" = [CAR_EXIT_SEGMENT, EXIT_VIEW, MEET_UP]


@dataclass
class Action:
    start_time: "datetime.datetime"
    finish_time: "datetime.datetime | None"
    start_loc: "Float2 | Float3"  # TODO: should either be Float2 or Float3
    end_loc: "Float2 | Float3 | None"  # TODO: should either be Float2 or Float3
    action_type: "ActionType"
    target_obj_id: "DetectionId | None" = None
    target_obj_bbox: "Float22 | None" = None
    invalid: bool = field(init=False)
    estimated_time: "datetime.timedelta" = field(init=False)

    def __post_init__(self):
        if self.finish_time is None or self.end_loc is None:
            self.invalid = True
            return

        self.invalid = self.finish_time < self.start_time
        self.estimated_time = self.finish_time - self.start_time
        if self.action_type and self.action_type in OBJ_BASED_ACTION:
            assert self.target_obj_id is not None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"""action type: {self.action_type},
        start time: {self.start_time},
        finish time: {self.finish_time},
        start loc: {self.start_loc},
        end loc: {self.end_loc}
        estimated time: {self.estimated_time}"""
