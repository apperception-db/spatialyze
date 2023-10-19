import time

import numpy as np

from spatialyze.video_processor.utils.depths_to_3d import depths_to_3ds, depths_to_3ds_naive


def test_depths_to_3d():
    np.random.seed(10)
    depths = np.random.rand(20, 1000, 700)
    intrinsic = np.array([[1000, 0, 800], [0, 1000, 400], [0, 0, 1]])

    start = time.time()
    d_numpy = depths_to_3ds(depths, intrinsic)
    numpy_time = time.time() - start

    start = time.time()
    d_naive = depths_to_3ds_naive(depths, intrinsic)
    naive_time = time.time() - start

    assert numpy_time < naive_time, (numpy_time, naive_time)

    assert np.allclose(d_naive, d_numpy), (d_naive, d_numpy)
