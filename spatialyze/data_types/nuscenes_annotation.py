from typing import NamedTuple


class NuscenesAnnotation(NamedTuple):
    sample_token: "str"
    token: "str"
    instance_token: "str"
    translation: "list[float]"
    size: "list[float]"
    rotation: "list[float]"
    category: "str"
    heading: "float"
    location: "str"
    scene_name: "str"
    sample_data_token: "str"
    channel: "str"
    sample_data_tokens: "list[str]"
    out_of_view_sample_data_tokens: "list[str]"
    channels: "list[str]"
