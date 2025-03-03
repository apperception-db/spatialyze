import os
import pickle

from spatialyze.database import Database
from spatialyze.video_processor.stages.detection_2d.yolo_detection import YoloDetection, Metadatum as D2DMetadatum

OUTPUT_DIR = './data/pipeline/test-results'


class YoloOutput:
    def __init__(self):
        self.device = []
    
    def __call__(self, name: str):
        if len(self.device) == 0:
            self.device = [YoloDetection().device]
        device = self.device[0]
        with open(os.path.join(OUTPUT_DIR, f'YoloDetection--{name}.pkl'), 'rb') as f:
            d2ds = pickle.load(f)
            d2ds = [D2DMetadatum(det.to(device), clss, did) for det, clss, did in d2ds]

        return {YoloDetection.classname(): d2ds}


yolo_output = YoloOutput()