"""
NDVI Computation
Computes Normalized Difference Vegetation Index from Sentinel-2 B04 (Red) and B08 (NIR).
"""

from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling


def find_band_file(folder: Path, band_name: str) -> Path:
    """Find a band file in the given folder by glob pattern."""
    patterns = [f"*{band_name}*.jp2", f"*{band_name}*.tif", f"*{band_name}*.tiff"]
    for pattern in patterns:
        matches = list(folder.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(
        f"No file matching '{band_name}' found in {folder}."
    )


def compute_ndvi(band_folder: Path, profile_ref: dict) -> np.ndarray:
    """
    Compute NDVI from B04 (Red) and B08 (NIR) in a band folder.

    Formula: NDVI = (B08 - B04) / (B08 + B04)
    Where B08+B04 == 0, NDVI is set to NaN.

    Args:
        band_folder: path to folder containing B04 and B08 files
        profile_ref: rasterio profile to match grid shape (H, W)

    Returns:
        ndvi: (H, W) float32 array, NaN where invalid or missing
    """
    target_h = profile_ref["height"]
    target_w = profile_ref["width"]

    try:
        b04_path = find_band_file(band_folder, "B04")
    except FileNotFoundError:
        print(f"[WARNING] B04 not found in {band_folder}. NDVI set to NaN.")
        return np.full((target_h, target_w), np.nan, dtype=np.float32)

    try:
        b08_path = find_band_file(band_folder, "B08")
    except FileNotFoundError:
        print(f"[WARNING] B08 not found in {band_folder}. NDVI set to NaN.")
        return np.full((target_h, target_w), np.nan, dtype=np.float32)

    with rasterio.open(b04_path) as src:
        if src.shape != (target_h, target_w):
            b04 = src.read(
                1,
                out_shape=(target_h, target_w),
                resampling=Resampling.bilinear,
            ).astype(np.float32) / 10000.0
        else:
            b04 = src.read(1).astype(np.float32) / 10000.0

    with rasterio.open(b08_path) as src:
        if src.shape != (target_h, target_w):
            b08 = src.read(
                1,
                out_shape=(target_h, target_w),
                resampling=Resampling.bilinear,
            ).astype(np.float32) / 10000.0
        else:
            b08 = src.read(1).astype(np.float32) / 10000.0

    denominator = b08 + b04
    ndvi = np.where(denominator != 0, (b08 - b04) / denominator, np.nan)

    return ndvi.astype(np.float32)
