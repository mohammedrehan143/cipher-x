"""
Thresholding & Change Mask Generation
Converts continuous magnitude to a binary change mask using Otsu + morphological cleanup.
"""

import numpy as np
import rasterio
import skimage.filters
import scipy.ndimage


def otsu_threshold(magnitude_array: np.ndarray) -> float:
    """
    Compute Otsu threshold from valid (non-NaN) magnitude pixels.
    """
    valid_pixels = magnitude_array[~np.isnan(magnitude_array)]
    if valid_pixels.size == 0:
        raise ValueError("No valid pixels for Otsu thresholding. All pixels are NaN.")

    threshold = skimage.filters.threshold_otsu(valid_pixels)
    return float(threshold)


def apply_threshold(magnitude_array: np.ndarray, threshold: float) -> np.ndarray:
    """
    Apply threshold to magnitude array.

    Returns:
        bool array: True where magnitude > threshold AND valid
    """
    valid = ~np.isnan(magnitude_array)
    changed = (magnitude_array > threshold) & valid
    return changed


def clean_mask(
    binary_mask: np.ndarray, open_size: int = 3, close_size: int = 3
) -> np.ndarray:
    """
    Morphological cleanup: opening then closing.
    """
    struct_open = scipy.ndimage.generate_binary_structure(2, 1)
    struct_close = scipy.ndimage.generate_binary_structure(2, 1)

    cleaned = scipy.ndimage.binary_opening(
        binary_mask, structure=struct_open, iterations=open_size
    )
    cleaned = scipy.ndimage.binary_closing(
        cleaned, structure=struct_close, iterations=close_size
    )
    return cleaned.astype(np.uint8)


def save_change_mask(
    mask: np.ndarray, profile: dict, output_path: str
) -> None:
    """
    Write binary change mask as uint8 GeoTIFF: 0=no change, 1=change.
    """
    out_profile = profile.copy()
    out_profile.update(
        driver="GTiff",
        height=mask.shape[0],
        width=mask.shape[1],
        count=1,
        dtype="uint8",
        nodata=0,
        compress="deflate",
    )

    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(mask.astype(np.uint8), 1)
