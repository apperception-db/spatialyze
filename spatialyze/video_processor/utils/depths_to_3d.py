from math import sqrt

import numpy as np
import numpy.typing as npt
from numpy import newaxis as na


def depths_to_3ds_naive(depths: npt.NDArray, intrinsic: npt.NDArray) -> npt.NDArray:
    n, lenx, leny = depths.shape
    [[fx, _, x0], [_, fy, y0], [_, _, s]] = intrinsic
    out = np.empty((n, lenx, leny, 3))
    for i in range(n):
        for x in range(lenx):
            for y in range(leny):
                unit_x: float = (s * x - x0) / fx
                unit_y: float = (s * y - y0) / fy

                Z = depths[i, x, y] / sqrt(1 + (unit_x**2) + (unit_y**2))
                X = unit_x * Z
                Y = unit_y * Z
                out[i, x, y, :] = np.array([X, Y, Z])
    return out


def depths_to_3ds(
    depths: npt.NDArray, intrinsic: npt.NDArray, true_depth: bool = False
) -> npt.NDArray:
    """
    Parameters:
    depths: (N x X x Y) depth maps
    intrinsic: (3 x 3) camera intrinsic
    true_depth: True if depths is the z-axis distance from the camera. False if depths is the distance from the camera.

    Returns:
    d3 location of each pixel (N x X x Y x 3)
    """
    n, lenx, leny = depths.shape

    # N x X x Y x 1
    xs = np.repeat(np.repeat(np.arange(lenx)[na, :, na, na], n, axis=0), leny, axis=2)
    # N x X x Y x 1
    ys = np.repeat(np.repeat(np.arange(leny)[na, na, :, na], n, axis=0), lenx, axis=1)
    # N x X x Y x 1
    zs = depths[:, :, :, na]

    # N x X x Y x 3
    _depths = np.concatenate([xs * zs, ys * zs, zs], axis=3)

    # N x X x Y x 3 x 1
    res = (np.linalg.inv(intrinsic) * intrinsic[2, 2]) @ _depths[:, :, :, :, na]
    # N x X x Y x 3
    res = res[:, :, :, :, 0]
    if true_depth:
        return res

    # N x X x Y
    X = res[:, :, :, 0]
    # N x X x Y
    Y = res[:, :, :, 1]
    # N x X x Y
    Z = res[:, :, :, 2]

    # N x X x Y
    scale = np.sqrt(1 + (X / Z) ** 2 + (Y / Z) ** 2)
    return res / scale[:, :, :, na]


# if __name__ == "__main__":
#     np.random.seed(10)
#     depths = np.random.rand(20, 1000, 700)
#     intrinsic = np.array([[1000, 0, 800], [0, 1000, 400], [0, 0, 1]])

#     start = time.time()
#     d_numpy = depths_to_3ds(depths, intrinsic)
#     numpy_time = time.time() - start
#     print(numpy_time)

#     start = time.time()
#     d_naive = depths_to_3ds_naive(depths, intrinsic)
#     naive_time = time.time() - start
#     print(naive_time)

#     print(np.allclose(d_naive, d_numpy))
