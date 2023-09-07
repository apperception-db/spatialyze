import pickle
from itertools import chain

import numpy as np

from spatialyze.utils.process_raw_nuscenes import process_raw_nuscenes

def test_process_raw_nuscenes():
    annotations, cameras = process_raw_nuscenes('./data/nuscenes/mini')

    # with open('./data/nuscenes/processed/cameras.pkl', 'wb') as f:
    #     pickle.dump(cameras, f)
    # with open('./data/nuscenes/processed/annotations.pkl', 'wb') as f:
    #     pickle.dump(annotations, f)

    with open('./data/nuscenes/processed/cameras.pkl', 'rb') as f:
        cameras_groundtruth = pickle.load(f)
    with open('./data/nuscenes/processed/annotations.pkl', 'rb') as f:
        annotations_groundtruth = pickle.load(f)
    
    assert len(cameras) == len(cameras_groundtruth), (len(cameras), len(cameras_groundtruth))
    assert len(annotations) == len(annotations_groundtruth), (len(annotations), len(annotations_groundtruth))

    for key in annotations:
        annotation = annotations[key]
        annotation_groundtruth = annotations_groundtruth[key]
        for a, a_groundtruth in zip(annotation, annotation_groundtruth):
            assert a[:3] == a_groundtruth[:3], (a[:3], a_groundtruth[:3])
            assert np.allclose([*chain(*a[3:6]), a.heading], [*chain(*a_groundtruth[3:6]), a_groundtruth.heading]), ([*chain(*a[3:6]), a.heading], [*chain(*a_groundtruth[3:6]), a_groundtruth.heading])
            assert a.category == a_groundtruth.category, (a.category, a_groundtruth.category)
            assert a[8:] == a_groundtruth[8:], (a[8:], a_groundtruth[8:])
    
    for key in cameras:
        camera = cameras[key]
        camera_groundtruth = cameras_groundtruth[key]
        assert len(camera) == len(camera_groundtruth), (len(camera), len(camera_groundtruth))
        for c, c_groundtruth in zip(camera, camera_groundtruth):
            assert c[:6] == c_groundtruth[:6], (c[:6], c_groundtruth[:6])
            assert c[11:14] == c_groundtruth[11:14], (c[11:14], c_groundtruth[11:14])
            assert np.allclose(c.camera_translation, c_groundtruth.camera_translation), (c.camera_translation, c_groundtruth.camera_translation)
            assert np.allclose(c.camera_rotation, c_groundtruth.camera_rotation), (c.camera_rotation, c_groundtruth.camera_rotation)
            assert np.allclose(c.camera_intrinsic, c_groundtruth.camera_intrinsic), (c.camera_intrinsic, c_groundtruth.camera_intrinsic)
            assert np.allclose(c.ego_translation, c_groundtruth.ego_translation), (c.ego_translation, c_groundtruth.ego_translation)
            assert np.allclose(c.ego_rotation, c_groundtruth.ego_rotation), (c.ego_rotation, c_groundtruth.ego_rotation)
            assert np.allclose((c.ego_heading, c.camera_heading), (c_groundtruth.ego_heading, c_groundtruth.camera_heading)), ((c.ego_heading, c.camera_heading), (c_groundtruth.ego_heading, c_groundtruth.camera_heading))
            assert c.frame_order == c_groundtruth.frame_order, (c.frame_order, c_groundtruth.frame_order)
