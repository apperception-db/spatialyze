import os
import pickle
import pytest

from bitarray import bitarray
import numpy as np

from spatialyze.predicate import *
from spatialyze.utils import F
from spatialyze.video_processor.camera_config import camera_config
from spatialyze.video_processor.payload import Payload

from spatialyze.video_processor.stages.detection_2d.object_type_filter import FindType, ObjectTypeFilter
from spatialyze.video_processor.stages.detection_2d.yolo_detection import YoloDetection
from spatialyze.video_processor.pipeline import Pipeline
from spatialyze.video_processor.video import Video

from common import yolo_output

OUTPUT_DIR = './data/pipeline/test-results'
VIDEO_DIR =  './data/pipeline/videos'

# Test Strategies
# - Real use case -- simple predicates from the query
# - 2 format + add true/false + add ignore_roadtype
#   - x AND ~y AND (z OR ~ w)
#   - x OR ~y OR (z AND ~ w)


o = objects[0]
o1 = objects[1]
o2 = objects[2]
c = camera
c0 = cameras[0]
gen = GenSqlVisitor()
RT = '__ROADTYPES__'

@pytest.mark.parametrize("fn, types", [
    # Propagate Boolean
    (o.type & False, set()),
    (o.type | True, set()),

    (o.type | (~(o.a & False)), set()),
    (o.type & (~(o.a | True)), set()),

    (o.type & (~((o.a | True) & True)), set()),
    (arr(o.type) | (~((o.a & False) | cast(False, 'int'))), set()),
    (arr(o.type == 'car'), {'car'}),
    (F.contains('intersection', o.type == 'car'), {'car'}),
    (o, set()),
    (camera, set()),

    # General
    (lit('car') == o.type, {'car'}),
    ((o.type == 'car') == (o1.type == 'car'), {'car'}),
    ((o.type == 'car') + (o1.type == 'car'), {'car'}),
    ((o.type == 'car') + (o1.type == 'person'), {'car', 'person'}),
])
def test_predicates(fn, types):
    _types = FindType()(fn)
    assert _types == types, (_types, types)


def test_objecttypefilter():
    assert repr(ObjectTypeFilter(types=['car', 'truck'])) == "ObjectTypeFilter(types=['car', 'truck'])"
    assert repr(ObjectTypeFilter(predicate=(o.type == 'car'))) == "ObjectTypeFilter(types=['car'])"


def test_filter():
    files = os.listdir(VIDEO_DIR)

    with open(os.path.join(VIDEO_DIR, 'frames.pkl'), 'rb') as f:
        videos = pickle.load(f)
    
    classes = ['car', 'person']
    pipeline = Pipeline()
    pipeline.add_filter(ObjectTypeFilter(types=classes))

    for name, video in videos.items():
        if video['filename'] not in files:
            continue
        
        frames = Video(
            os.path.join(VIDEO_DIR, video["filename"]),
            [camera_config(*f) for f in video["frames"]],
        )
        keep = bitarray(len(frames))
        keep.setall(0)
        keep[(len(frames) * 7) // 8:] = 1

        output = pipeline.run(Payload(frames, keep, metadata=yolo_output(name)))
        # det_result = YoloDetection.get(output)
        yolo_result = YoloDetection.get(output)
        assert yolo_result is not None
        det_result = output['Detection2D']
        assert det_result is not None

        clss = yolo_result[0][1]
        assert clss is not None

        for (det0, _, did0), (det1, _, did1) in zip(det_result, yolo_result):
            assert set(did0) <= set(did1)
            if len(det1) == 0:
                continue
            map0 = { did: det for did, det in zip(did0, det0) }
            map1 = { did: det for did, det in zip(did1, det1) }
            for idx, d0 in map0.items():
                d1 = map1[idx]
                d0 = d0.cpu().numpy()
                d1 = d1.cpu().numpy()
                assert np.allclose(d0[:4], d1[:4], atol=2)
                assert np.allclose(d0[4], d1[4], atol=0.05)
                assert np.allclose(d0[5], d1[5])
                assert clss[int(d0[5])] in classes