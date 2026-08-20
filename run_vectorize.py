"""
CIPHER-X Vectorization & Feature Pipeline Runner
Single script to run the full Person 2 pipeline end-to-end.

Usage:
    python run_vectorize.py
    python run_vectorize.py --min-area 500
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import rasterio

from src.vectorization.polygonize import load_and_clean_mask, polygonize_mask
from src.features.ndvi import compute_ndvi
from src.features.extractor import extract_features, FEATURE_COLUMNS


# Person 1 guaranteed outputs
CHANGE_MASK = "outputs/maps/change_mask.tif"
CHANGE_MAGNITUDE = "outputs/maps/change_magnitude.tif"
SPECTRAL_DELTA = "data/processed/spectral_delta.tif"
BEFORE_FOLDER = "data/sentinel/before"
AFTER_FOLDER = "data/sentinel/after"

# Person 2 outputs
OUTPUT_GEOJSON = "outputs/polygons/change_results.geojson"
OUTPUT_CSV = "outputs/predictions/change_features.csv"


def main():
    parser = argparse.ArgumentParser(description="CIPHER-X Vectorization & Feature Pipeline")
    parser.add_argument(
        "--min-area",
        type=float,
        default=1000.0,
        help="Minimum polygon area in m² (default: 1000)",
    )
    args = parser.parse_args()

    # Create output directories
    Path("outputs/polygons").mkdir(parents=True, exist_ok=True)
    Path("outputs/predictions").mkdir(parents=True, exist_ok=True)

    # Step 1: Check Person 1 outputs exist
    print("[1/6] Checking Person 1 outputs exist...")
    missing = []
    for f in [CHANGE_MASK, CHANGE_MAGNITUDE, SPECTRAL_DELTA]:
        if not Path(f).exists():
            missing.append(f)
    if missing:
        print(f"[ERROR] Missing files: {missing}")
        print("        Run 'python run_pipeline.py' first to generate Person 1 outputs.")
        sys.exit(1)
    print("       All Person 1 outputs found.")

    # Step 2: Load and vectorize change mask
    print("[2/6] Loading and vectorizing change mask...")
    mask, mask_profile = load_and_clean_mask(CHANGE_MASK, open_size=3)
    changed_pixels = int(mask.sum())
    print(f"       Changed pixels in mask: {changed_pixels}")

    gdf = polygonize_mask(mask, mask_profile, min_area_m2=args.min_area)
    if gdf.empty:
        print("[ERROR] No change polygons found. Nothing to save.")
        sys.exit(1)

    # Step 3: Compute NDVI (before)
    print("[3/6] Computing NDVI (before)...")
    with rasterio.open(CHANGE_MAGNITUDE) as src:
        mag_profile = src.profile.copy()

    ndvi_before = compute_ndvi(Path(BEFORE_FOLDER), mag_profile)
    valid_before = int(np.sum(~np.isnan(ndvi_before)))
    print(f"       NDVI before: {valid_before} valid pixels")

    # Step 4: Compute NDVI (after)
    print("[4/6] Computing NDVI (after)...")
    ndvi_after = compute_ndvi(Path(AFTER_FOLDER), mag_profile)
    valid_after = int(np.sum(~np.isnan(ndvi_after)))
    print(f"       NDVI after: {valid_after} valid pixels")

    # Step 5: Extract features
    print("[5/6] Extracting polygon features...")
    with rasterio.open(SPECTRAL_DELTA) as src:
        delta_profile = src.profile.copy()

    df = extract_features(
        gdf,
        CHANGE_MAGNITUDE, mag_profile,
        SPECTRAL_DELTA, delta_profile,
        ndvi_before, ndvi_after,
    )
    print(f"       Features extracted for {len(df)} polygons")
    print(f"       Columns: {list(df.columns)}")

    # Step 6: Save outputs
    print("[6/6] Saving outputs...")

    # GeoJSON
    gdf_with_features = gdf.copy()
    for col in df.columns:
        if col not in gdf_with_features.columns:
            gdf_with_features[col] = df[col].values
    gdf_with_features = gdf_with_features[FEATURE_COLUMNS + ["geometry"]]
    gdf_with_features.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    print(f"       {OUTPUT_GEOJSON}")

    # CSV (no geometry)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"       {OUTPUT_CSV}")

    # Summary
    print("\nDone. Outputs written to:")
    print(f"  {OUTPUT_GEOJSON}")
    print(f"  {OUTPUT_CSV}")
    print(f"\nStatistics:")
    print(f"  Total polygons: {len(df)}")
    print(f"  Area range: {df['area_m2'].min():.0f} – {df['area_m2'].max():.0f} m²")
    print(f"  Mean CVA magnitude: {df['cva_mean'].mean():.4f}")
    print(f"  NaN features per column:")
    for col in ["ndvi_before", "ndvi_after", "delta_ndvi", "delta_b02"]:
        nan_count = df[col].isna().sum()
        print(f"    {col}: {nan_count}/{len(df)}")


if __name__ == "__main__":
    main()
