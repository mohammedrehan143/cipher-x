"""
Image Alignment Module
Ensures BEFORE and AFTER arrays are on the exact same grid using rasterio.warp.reproject.
"""

import numpy as np
import rasterio
from rasterio.warp import reproject, calculate_default_transform
from rasterio.enums import Resampling


def align_to_reference(
    src_array: np.ndarray,
    src_profile: dict,
    ref_profile: dict,
    resampling: str = "bilinear",
) -> np.ndarray:
    """
    Reproject src_array to match ref_profile's CRS, transform, and shape.

    Args:
        src_array: (bands, H, W) source array
        src_profile: rasterio profile of source
        ref_profile: rasterio profile of reference (target grid)
        resampling: 'bilinear' for continuous bands, 'nearest' for SCL

    Returns:
        Reprojected array matching reference grid
    """
    resampling_method = (
        Resampling.nearest if resampling == "nearest" else Resampling.bilinear
    )

    dst_height = ref_profile["height"]
    dst_width = ref_profile["width"]
    dst_crs = ref_profile["crs"]
    dst_transform = ref_profile["transform"]

    dst_array = np.empty(
        (src_array.shape[0], dst_height, dst_width), dtype=src_array.dtype
    )

    for i in range(src_array.shape[0]):
        reproject(
            source=src_array[i],
            destination=dst_array[i],
            src_transform=src_profile["transform"],
            src_crs=src_profile["crs"],
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=resampling_method,
        )

    return dst_array


def align_images(
    before_bands: np.ndarray,
    before_scl: np.ndarray,
    before_profile: dict,
    after_bands: np.ndarray,
    after_scl: np.ndarray,
    after_profile: dict,
) -> tuple:
    """
    Align AFTER images to BEFORE grid. BEFORE is used as the reference.

    Returns:
        (aligned_after_bands, aligned_after_scl)
    """
    if (
        before_profile["crs"] == after_profile["crs"]
        and before_profile["transform"] == after_profile["transform"]
        and before_bands.shape == after_bands.shape
    ):
        print("[3/6] Images already aligned — skipping reprojection.")
        return after_bands, after_scl

    print("[3/6] Aligning AFTER image to BEFORE grid...")
    aligned_bands = align_to_reference(
        after_bands, after_profile, before_profile, resampling="bilinear"
    )
    aligned_scl = align_to_reference(
        after_scl.reshape(1, *after_scl.shape),
        after_profile,
        before_profile,
        resampling="nearest",
    ).squeeze()

    return aligned_bands, aligned_scl
