"""
Cloud/Shadow Masking Module
Builds validity masks from Sentinel-2 SCL band.
"""

import warnings
import numpy as np


# SCL classes to mask as INVALID (clouds, shadows, no data, etc.)
DEFAULT_MASK_CLASSES = [0, 1, 3, 8, 9, 10]


def scl_to_mask(
    scl_array: np.ndarray,
    mask_classes: list = None,
) -> np.ndarray:
    """
    Convert SCL array to boolean validity mask.

    Args:
        scl_array: (H, W) uint8 SCL values
        mask_classes: list of SCL values to mask as invalid

    Returns:
        bool array: True = VALID pixel, False = masked/invalid
    """
    if mask_classes is None:
        mask_classes = DEFAULT_MASK_CLASSES

    valid_mask = ~np.isin(scl_array, mask_classes)
    return valid_mask


def combine_masks(before_mask: np.ndarray, after_mask: np.ndarray) -> np.ndarray:
    """
    Combine before and after validity masks.
    Returns True only where BOTH images are valid.
    """
    return before_mask & after_mask


def apply_mask(bands_array: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
    """
    Apply validity mask to band array, setting invalid pixels to NaN.

    Args:
        bands_array: (bands, H, W)
        valid_mask: (H, W) bool array, True = valid

    Returns:
        Masked array with NaN where valid_mask is False
    """
    masked = bands_array.copy()
    masked[:, ~valid_mask] = np.nan
    return masked
