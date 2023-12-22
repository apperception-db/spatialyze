import pickle
import json
import os
import numpy as np

from spatialyze.video_processor.metadata_json_encoder import MetadataJSONEncoder
from spatialyze.video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult
from spatialyze.video_processor.stream.strongsort import TrackingResult
from spatialyze.world import _execute

from common import build_filter_world


OUTPUT_DIR = './data/pipeline/test-results'


def trackid(track: list[TrackingResult]):
    return track[0].object_id


def frameidx(track: TrackingResult):
    return track.detection_id.frame_idx


def test_simple_workflow():
    world = build_filter_world()
    objects, trackings = _execute(world, optimization=False)

    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.json'), 'w') as f:
    #     json.dump(trackings, f, indent=1, cls=MetadataJSONEncoder)
    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.pkl'), 'wb') as f:
    #     pickle.dump(trackings, f)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.pkl'), 'rb') as f:
        trackings_groundtruth = pickle.load(f)
    
    for filename, tgs in trackings_groundtruth.items():
        assert filename in trackings, (filename, trackings.keys())
        tps = trackings[filename]
        assert len(tps) == len(tgs), (len(tps), len(tgs))
        for idx, (tp, tg) in enumerate(zip(sorted(tps, key=trackid), sorted(tgs, key=trackid))):
            assert len(tp) == len(tg), (idx, len(tp), len(tg))
            for p, g in zip(sorted(tp, key=frameidx), sorted(tg, key=frameidx)):
                assert isinstance(p, TrackingResult), (p, type(p))
                assert isinstance(g, TrackingResult), (g, type(g))
                assert tuple(p.detection_id) == tuple(g.detection_id), (p.detection_id, g.detection_id)
                assert p.object_id == g.object_id, (p.object_id, g.object_id)
                assert p.object_type == g.object_type, (p.object_type, g.object_type)
                assert p.timestamp == g.timestamp, (p.timestamp, g.timestamp)
                assert np.allclose([p.confidence], [g.confidence], atol=0.001, rtol=0), (p.confidence, g.confidence)
                assert np.allclose(p.bbox.detach().cpu().numpy(), g.bbox.detach().cpu().numpy(), atol=0.001, rtol=0), (p.bbox, g.bbox)
    
    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.json'), 'w') as f:
    #     json.dump(objects, f, indent=1)
    # with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.pkl'), 'wb') as f:
    #     pickle.dump(objects, f)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.pkl'), 'rb') as f:
        objects_groundtruth = pickle.load(f)
    
    assert len(objects) == len(objects_groundtruth), (len(objects), len(objects_groundtruth))
    for filename, ogs in objects_groundtruth.items():
        assert filename in objects, (filename, objects.keys())
        ops = objects[filename]
        assert len(ops) == len(ogs), (len(ops), len(ogs))
        for p, og in zip(sorted(ops), sorted(ogs)):
            assert tuple(p) == tuple(og), (p, og)
