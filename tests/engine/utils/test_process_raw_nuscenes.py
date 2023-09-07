import pickle

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
        assert annotation == annotation_groundtruth, (annotation, annotation_groundtruth)
    
    for key in cameras:
        camera = cameras[key]
        camera_groundtruth = cameras_groundtruth[key]
        assert len(camera) == len(camera_groundtruth), (len(camera), len(camera_groundtruth))
        for a, a_groundtruth in zip(camera, camera_groundtruth):
            assert a[:6] == a_groundtruth[:6], (a[:6], a_groundtruth[:6])
            assert a[8:] == a_groundtruth[8:], (a[8:], a_groundtruth[8:])
            assert np.allclose(a.camera_translation, a_groundtruth.camera_translation), (a.camera_translation, a_groundtruth.camera_translation)
            assert np.allclose(a.camera_rotation, a_groundtruth.camera_rotation), (a.camera_rotation, a_groundtruth.camera_rotation)
