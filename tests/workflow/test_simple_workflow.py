import pickle
import json
import os
import numpy as np

from spatialyze.video_processor.cache import disable_cache
from spatialyze.video_processor.metadata_json_encoder import MetadataJSONEncoder
from spatialyze.video_processor.stages.tracking_3d.tracking_3d import Tracking3DResult
from spatialyze.world import _execute

from common import build_filter_world


OUTPUT_DIR = './data/pipeline/test-results'
disable_cache()


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
        for idx, (tp, tg) in enumerate(zip(tps, tgs)):
            assert len(tp) == len(tg), (idx, len(tp), len(tg))
            for oid, g in tg.items():
                assert oid in tp, (oid, tp.keys())
                p = tp[oid]
                assert isinstance(g, Tracking3DResult), (g, type(g))
                assert p.frame_idx == g.frame_idx, (p.frame_idx, g.frame_idx)
                assert tuple(p.detection_id) == tuple(g.detection_id), (p.detection_id, g.detection_id)
                assert p.object_id == g.object_id, (p.object_id, g.object_id)
                assert np.allclose(np.array(p.point_from_camera), np.array(g.point_from_camera)), (p.point_from_camera, g.point_from_camera)
                assert np.allclose(np.array(p.point), np.array(g.point)), (p.point, g.point)
                assert p.bbox_left == g.bbox_left, (p.bbox_left, g.bbox_left)
                assert p.bbox_top == g.bbox_top, (p.bbox_top, g.bbox_top)
                assert p.bbox_w == g.bbox_w, (p.bbox_w, g.bbox_w)
                assert p.bbox_h == g.bbox_h, (p.bbox_h, g.bbox_h)
                assert p.object_type == g.object_type, (p.object_type, g.object_type)
                assert p.timestamp == g.timestamp, (p.timestamp, g.timestamp)
    
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
