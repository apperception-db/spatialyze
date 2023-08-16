from typing import NamedTuple


class QueryResult(NamedTuple):
    frame_number: "int"
    camera_id: "str"
    filename: "str"
    item_ids: "list[str]"