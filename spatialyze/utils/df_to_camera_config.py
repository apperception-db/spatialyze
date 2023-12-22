from spatialyze.video_processor.camera_config import camera_config


def df_to_camera_config(scene_name: str, sample_data):
    all_frames = sample_data[(sample_data["scene_name"] == scene_name)].sort_values(
        by="frame_order"
    )

    return [
        camera_config(
            camera_id=scene_name + "_" + str(frame.channel),
            frame_id=str(frame.token),
            frame_num=int(frame.frame_order),
            filename=str(frame.filename),
            camera_translation=frame.camera_translation,
            camera_rotation=frame.camera_rotation,
            camera_intrinsic=frame.camera_intrinsic,
            ego_translation=frame.ego_translation,
            ego_rotation=frame.ego_rotation,
            timestamp=frame.timestamp,
            camera_heading=frame.camera_heading,
            ego_heading=frame.ego_heading,
            location=frame.location,
        )
        for frame in all_frames.itertuples(index=False)
    ]
