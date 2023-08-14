import datetime

from ..stages.segment_trajectory.construct_segment_trajectory import InvalidSegmentPoint
from ..types import Float3
from .get_tracks import TrackPoint


def format_trajectory(video_name: "str", obj_id: "int", track: "list[TrackPoint]"):
    timestamps: "list[datetime.datetime]" = []
    pairs: "list[Float3]" = []
    itemHeadings: "list[float | None]" = []
    translations: "list[Float3]" = []
    camera_id = None
    object_type = None
    # road_types: "list[str]" = []
    # roadpolygons: "list[list[Float2]]" = []
    ### TODO (fge): remove investigation code
    info_found = []
    # if obj_id in investigation_ids:
    #     print(f"obj_id, {obj_id}:", [e[1].filename for e in track])
    for tracking_result_3d, ego_info, segment_mapping in track:
        if ego_info:
            if (
                ego_info.filename is not None
                and "sweeps/CAM_FRONT/n008-2018-08-30-15-16-55-0400__CAM_FRONT__1535657125362404.jpg"
                in ego_info.filename
            ):
                info_found.append(
                    [
                        obj_id,
                        tracking_result_3d.bbox_left,
                        tracking_result_3d.bbox_top,
                        tracking_result_3d.bbox_w,
                        tracking_result_3d.bbox_h,
                    ]
                )
            camera_id = ego_info.camera_id
            object_type = tracking_result_3d.object_type
            timestamps.append(ego_info.timestamp)
            pairs.append(tracking_result_3d.point)
            itemHeadings.append(None if segment_mapping is None or isinstance(segment_mapping, InvalidSegmentPoint) or segment_mapping.segment_type == "intersection" else segment_mapping.segment_heading)
            translations.append(ego_info.ego_translation)
            # road_types.append(segment_mapping.road_polygon_info.road_type if base else detection_info.road_type)
            # roadpolygons.append(None if base else detection_info.road_polygon_info.polygon)
    if len(timestamps) == 0 or camera_id is None or object_type is None:
        return None
    # if obj_id in investigation_ids:
    #     print(f"pairs for obj {obj_id}:", [(e[0], e[1]) for e in pairs])
    #     print(f"itemHeadings for obj {obj_id}:", itemHeadings)

    return (
        video_name + "_obj_" + str(obj_id),
        camera_id,
        object_type,
        timestamps,
        pairs,
        itemHeadings,
        translations,
    ), info_found
