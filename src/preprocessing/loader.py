"""
Sentinel-2 Band Loader
Reads S2 L2A bands from a folder and returns numpy arrays.
"""

from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling


BAND_NAMES = {
    "B02": "Blue",
    "B03": "Green",
    "B04": "Red",
    "B08": "NIR",
    "SCL": "Scene Classification",
}

REQUIRED_BANDS = ["B02", "B03", "B04", "B08"]


def find_band_file(folder: Path, band_name: str) -> Path:
    """Find a band file in the given folder by glob pattern."""
    patterns = [f"*{band_name}*.jp2", f"*{band_name}*.tif", f"*{band_name}*.tiff"]
    for pattern in patterns:
        matches = list(folder.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(
        f"No file matching '{band_name}' found in {folder}. "
        f"Expected pattern: *{band_name}*.jp2 or *{band_name}*.tif"
    )


def load_bands(folder: Path) -> tuple:
    """
    Load Sentinel-2 bands from a folder.

    Returns:
        bands: shape (4, H, W), float32, range [0.0, 1.0]
               band order: [B02, B03, B04, B08]
        scl: shape (H, W), uint8, SCL class values (resampled to 10m)
        profile: rasterio profile dict for saving outputs
    """
    folder = Path(folder)

    band_arrays = []
    ref_profile = None

    for band in REQUIRED_BANDS:
        band_path = find_band_file(folder, band)
        with rasterio.open(band_path) as src:
            data = src.read(1).astype(np.float32) / 10000.0
            band_arrays.append(data)
            if ref_profile is None:
                ref_profile = src.profile.copy()

    bands = np.stack(band_arrays, axis=0)

    profile = ref_profile.copy()
    profile.update(
        height=bands.shape[1],
        width=bands.shape[2],
        count=4,
        dtype="float32",
    )

    # Load SCL if available
    try:
        scl_path = find_band_file(folder, "SCL")
        with rasterio.open(scl_path) as src:
            scl = src.read(1).astype(np.uint8)

            # Resample SCL to match band resolution if needed
            if scl.shape != (bands.shape[1], bands.shape[2]):
                scl_data = src.read(
                    1,
                    out_shape=(bands.shape[1], bands.shape[2]),
                    resampling=Resampling.nearest,
                )
                scl = scl_data.astype(np.uint8)
    except FileNotFoundError:
        print(f"[WARNING] SCL file not found in {folder}. Treating all pixels as valid.")
        scl = np.full((bands.shape[1], bands.shape[2]), 4, dtype=np.uint8)

    return bands, scl, profile
