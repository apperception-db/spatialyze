from evadb.udfs.abstract.abstract_udf import AbstractUDF
from evadb.udfs.decorators.decorators import forward, setup
import numpy as np
import pandas as pd
import torch
import math
from pyquaternion import Quaternion
from spatialyze.video_processor.stages.decode_frame.decode_frame import DecodeFrame
from spatialyze.video_processor.stages.stage import Stage
from evadb.udfs.abstract.abstract_udf import AbstractUDF
from evadb.udfs.decorators.decorators import forward, setup
from evadb.udfs.decorators.io_descriptors.data_types import PandasDataframe
from evadb.catalog.catalog_type import NdArrayType, ColumnType
from evadb.udfs.gpu_compatible import GPUCompatible
from nuscenes.nuscenes import NuScenes
from nuscenes.map_expansion.map_api import NuScenesMap
from nuscenes.map_expansion import arcline_path_utils
from nuscenes.map_expansion.bitmap import BitMap
from pathlib import Path
EVA = Path(__file__).parent.parent

class QE3(AbstractUDF):
    @setup(cacheable=True, udf_type="Query", batchable=True)
    def setup(self):
        self.nusc_map = NuScenesMap(dataroot=str(EVA), map_name='boston-seaport')
    
    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["locations"],
                column_types=[NdArrayType.ANYTYPE],
                column_shapes=[(None,)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["queryresult"],
                column_types=[NdArrayType.ANYTYPE],
                column_shapes=[(None)],
            )
        ],
    )
    def forward(self, df):
        objClasses = ["car", "truck"]
        def _forward(row):
            locations, egoTranslation, egoHeading = [np.array(x) for x in row.iloc]
            for object in locations:
                x, y, z, objClass, conf = object
                loc = np.array([float(x) for x in (x, y, z)])

                if objClass not in objClasses:
                   continue
                
                distance = np.linalg.norm(egoTranslation - loc)

                if distance < 10 and is_contained_lane(self.nusc_map, loc):
                   return True
            return False

        ret = pd.DataFrame()
        ret["queryresult"] = df.apply(_forward, axis=1)
        return ret


    def name(self):
        return "QE3"

def is_contained_lane(nusc_map, position):
  x, y, z = position
  lane_segment_token = nusc_map.layers_on_point(x, y)['lane']
  if lane_segment_token != '':
    return True
  else:
    return False