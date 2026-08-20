"""
CIPHER-X Pipeline Runner
Single script to execute the entire preprocessing + CVA pipeline end-to-end.

Usage:
    python run_pipeline.py
    python run_pipeline.py --before data/sentinel/before --after data/sentinel/after
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import rasterio

from src.preprocessing.loader import load_bands
from src.preprocessing.align import align_images
from src.preprocessing.masking import scl_to_mask, combine_masks, apply_mask
from src.cva.compute import compute_delta, compute_magnitude, save_raster
from src.cva.threshold import otsu_threshold, apply_threshold, clean_mask, save_change_mask


def main():
    parser = argparse.ArgumentParser(description="CIPHER-X Change Detection Pipeline")
    parser.add_argument(
        "--before",
        type=str,
        default="data/sentinel/before",
        help="Path to BEFORE S2 band folder",
    )
    parser.add_argument(
        "--after",
        type=str,
        default="data/sentinel/after",
        help="Path to AFTER S2 band folder",
    )
    args = parser.parse_args()

    before_folder = Path(args.before)
    after_folder = Path(args.after)

    # Create output directories
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("outputs/maps").mkdir(parents=True, exist_ok=True)

    # Step 1: Load BEFORE bands
    print("[1/6] Loading BEFORE bands...")
    before_bands, before_scl, before_profile = load_bands(before_folder)
    print(f"       Shape: {before_bands.shape}")

    # Step 2: Load AFTER bands
    print("[2/6] Loading AFTER bands...")
    after_bands, after_scl, after_profile = load_bands(after_folder)
    print(f"       Shape: {after_bands.shape}")

    # Step 3: Align images
    print("[3/6] Aligning images...")
    after_bands, after_scl = align_images(
        before_bands, before_scl, before_profile,
        after_bands, after_scl, after_profile,
    )

    # Step 4: Apply cloud masks
    print("[4/6] Applying cloud masks...")
    before_valid = scl_to_mask(before_scl)
    after_valid = scl_to_mask(after_scl)
    combined_valid = combine_masks(before_valid, after_valid)

    valid_pct = combined_valid.sum() / combined_valid.size * 100
    print(f"       Valid pixels: {valid_pct:.1f}%")

    if valid_pct < 1.0:
        print("[ERROR] Less than 1% valid pixels. Check your SCL files or pick new dates.")
        sys.exit(1)

    before_masked = apply_mask(before_bands, combined_valid)
    after_masked = apply_mask(after_bands, combined_valid)

    # Step 5: Compute CVA
    print("[5/6] Computing CVA magnitude...")
    delta = compute_delta(before_masked, after_masked, combined_valid)
    magnitude = compute_magnitude(delta)

    save_raster(delta, before_profile, "data/processed/spectral_delta.tif")
    save_raster(magnitude, before_profile, "outputs/maps/change_magnitude.tif")

    # Step 6: Generate change mask
    print("[6/6] Generating binary change mask...")
    threshold = otsu_threshold(magnitude)
    print(f"       Otsu threshold: {threshold:.6f}")

    binary_change = apply_threshold(magnitude, threshold)
    clean_change = clean_mask(binary_change, open_size=3, close_size=3)

    # Set masked pixels to 0
    clean_change[~combined_valid] = 0

    save_change_mask(clean_change, before_profile, "outputs/maps/change_mask.tif")

    # Summary statistics
    changed_count = int(clean_change.sum())
    total_valid = int(combined_valid.sum())
    change_pct = changed_count / total_valid * 100 if total_valid > 0 else 0

    print("\nDone. Outputs written to:")
    print("  outputs/maps/change_magnitude.tif")
    print("  outputs/maps/change_mask.tif")
    print("  data/processed/spectral_delta.tif")
    print("\nStatistics:")
    print(f"  Changed pixels: {changed_count} / {total_valid} ({change_pct:.2f}%)")
    print(f"  Magnitude: min={float(np.nanmin(magnitude)):.4f}, "
          f"max={float(np.nanmax(magnitude)):.4f}, "
          f"mean={float(np.nanmean(magnitude)):.4f}")
    print(f"  Otsu threshold: {threshold:.6f}")


if __name__ == "__main__":
    main()
