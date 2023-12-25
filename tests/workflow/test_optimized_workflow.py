import pytest
import json
import pickle
import os

from spatialyze.world import _execute
from common import ResultsEncoder, build_filter_world, compare_objects, compare_trackings, compare_objects2, VIDEO_DIR


OUTPUT_DIR = './data/pipeline/test-results'


@pytest.mark.parametrize("alt_tracker, detect_only, suffix", [
    (True, False, '-alt'),
    (False, False, ''),
    (True, True, '-det'),
])
def test_optimized_workflow(alt_tracker: bool, detect_only: bool, suffix: str):
    world = build_filter_world(pkl=True, alt_tracker=alt_tracker, track=not detect_only)
    objects, trackings = _execute(world)
    for t in trackings.values(): t.sort()
    for o in objects.values(): o.sort()

    with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-trackings{suffix}.json'), 'w') as f:
        json.dump(trackings, f, indent=1, cls=ResultsEncoder)
    # with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-trackings{suffix}.pkl'), 'wb') as f:
    #     pickle.dump(trackings, f)
    
    with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-trackings{suffix}.pkl'), 'rb') as f:
        trackings_groundtruth = pickle.load(f)
    compare_trackings(trackings, trackings_groundtruth)
    
    with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-objects{suffix}.json'), 'w') as f:
        json.dump(objects, f, indent=1, cls=ResultsEncoder)
    # with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-objects{suffix}.pkl'), 'wb') as f:
    #     pickle.dump(objects, f)
    
    with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-objects{suffix}.pkl'), 'rb') as f:
        objects_groundtruth = pickle.load(f)
    compare_objects(objects, objects_groundtruth)

    world._objects, world._trackings = objects, trackings
    objects2 = world.getObjects()
    objects2.sort(key=lambda x: (x.id, x.type, x.camera_id, x.frame_ids, x.track, x.bboxes))

    with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-objects2{suffix}.json'), 'w') as f:
        json.dump(objects2, f, indent=1, cls=ResultsEncoder)
    # with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-objects2{suffix}.pkl'), 'wb') as f:
    #     pickle.dump(objects2, f)
    
    with open(os.path.join(OUTPUT_DIR, f'optimized-workflow-objects2{suffix}.pkl'), 'rb') as f:
        objects2_groundtruth = pickle.load(f)
    compare_objects2(objects2, objects2_groundtruth)
    
    files = os.listdir(VIDEO_DIR)
    files = (f for f in files if f.startswith('boston-seaport'))
    files = (f[len('boston-seaport-scene-'):] for f in files)
    files = (f[:len('xxxx')] for f in files)
    files = set(files)
    # files = ['0655', '0757']
    out_folder = os.path.join('./outputs', 'workflow' + suffix)
    for f in files:
        path = os.path.join(out_folder, f'scene-{f}-CAM_FRONT-result.mp4')
        if os.path.exists(path):
            os.remove(path)
    world.saveVideos(out_folder, addBoundingBoxes=True)
    for f in files:
        path = os.path.join(out_folder, f'scene-{f}-CAM_FRONT-result.mp4')
        assert os.path.exists(path)

