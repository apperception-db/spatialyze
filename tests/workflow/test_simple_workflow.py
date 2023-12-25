import pickle
import json
import os

from spatialyze.world import _execute
from common import build_filter_world, compare_objects, compare_trackings, ResultsEncoder


OUTPUT_DIR = './data/pipeline/test-results'


def test_simple_workflow():
    world = build_filter_world()
    objects, trackings = _execute(world, optimization=False)

    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.json'), 'w') as f:
        json.dump(trackings, f, indent=1, cls=ResultsEncoder)
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.pkl'), 'wb') as f:
        pickle.dump(trackings, f)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-trackings.pkl'), 'rb') as f:
        trackings_groundtruth = pickle.load(f)
    compare_trackings(trackings, trackings_groundtruth)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.json'), 'w') as f:
        json.dump(objects, f, indent=1, cls=ResultsEncoder)
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.pkl'), 'wb') as f:
        pickle.dump(objects, f)
    
    with open(os.path.join(OUTPUT_DIR, 'simple-workflow-objects.pkl'), 'rb') as f:
        objects_groundtruth = pickle.load(f)
    compare_objects(objects, objects_groundtruth)

