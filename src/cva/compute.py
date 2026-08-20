"""
Change Vector Analysis (CVA) Computation
Computes per-pixel spectral delta and change magnitude.
"""

import numpy as np
import rasterio


def compute_delta(
    before_bands: np.ndarray, after_bands: np.ndarray, valid_mask: np.ndarray
) -> np.ndarray:
    """
    Compute spectral delta between after and before bands.

    Args:
        before_bands: (4, H, W) float32
        after_bands: (4, H, W) float32
        valid_mask: (H, W) bool, True = valid

    Returns:
        delta: (4, H, W) float32, NaN where invalid
    """
    delta = after_bands.astype(np.float32) - before_bands.astype(np.float32)
    delta[:, ~valid_mask] = np.nan
    return delta


def compute_magnitude(delta_array: np.ndarray) -> np.ndarray:
    """
    Compute Euclidean magnitude across spectral bands.

    Args:
        delta_array: (4, H, W) float32

    Returns:
        magnitude: (H, W) float32, NaN where invalid
    """
    magnitude = np.sqrt(np.nansum(delta_array**2, axis=0))
    return magnitude.astype(np.float32)


def save_raster(array: np.ndarray, profile: dict, output_path: str) -> None:
    """
    Write a numpy array to a GeoTIFF with correct CRS and transform.
    """
    output_path = str(output_path)

    if array.ndim == 2:
        count = 1
        height, width = array.shape
        dtype = array.dtype
    else:
        count, height, width = array.shape
        dtype = array.dtype

    out_profile = profile.copy()
    out_profile.update(
        height=height,
        width=width,
        count=count,
        dtype=str(dtype),
        compress="deflate",
        nodata=np.nan if np.issubdtype(dtype, np.floating) else 0,
    )

    with rasterio.open(output_path, "w", **out_profile) as dst:
        if array.ndim == 2:
            dst.write(array, 1)
        else:
            dst.write(array)
