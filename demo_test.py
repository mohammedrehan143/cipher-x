"""
Demo / Smoke Test
Generates synthetic Sentinel-2 band files, runs the full pipeline,
and verifies all outputs are valid.

Usage:
    python demo_test.py
"""

import shutil
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

# ---------- CONFIG ----------
H, W = 200, 200
CRS = CRS.from_epsg(32643)  # UTM zone 43N (India)
BOUND = (77.0, 8.0, 77.1, 8.1)  # fake AOI near Bangalore
transform = from_bounds(*BOUND, W, H)

BEFORE_DIR = Path("data/sentinel/before")
AFTER_DIR = Path("data/sentinel/after")


def make_profile(dtype="float32", count=1):
    return {
        "driver": "GTiff",
        "dtype": dtype,
        "width": W,
        "height": H,
        "count": count,
        "crs": CRS,
        "transform": transform,
        "compress": "deflate",
    }


def save_band(path, data, dtype="float32"):
    p = make_profile(dtype)
    p["count"] = 1
    with rasterio.open(path, "w", **p) as dst:
        dst.write(data.astype(dtype), 1)


def generate_before():
    """Generate realistic-looking BEFORE scene."""
    print("[DEMO] Generating BEFORE scene...")
    BEFORE_DIR.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    base = np.random.rand(H, W).astype(np.float32) * 0.3 + 0.1

    for band, factor in [("B02", 1.0), ("B03", 1.2), ("B04", 0.8), ("B08", 1.5)]:
        noise = np.random.rand(H, W).astype(np.float32) * 0.02
        data = (base * factor + noise) * 10000  # store as DN (0-10000)
        data = np.clip(data, 0, 10000)
        save_band(BEFORE_DIR / f"T43PFP_20240115_{band}_10m.tif", data, "uint16")

    # SCL: mostly vegetation (4) with some clouds (9)
    scl = np.full((H, W), 4, dtype=np.uint8)
    scl[50:70, 50:70] = 9   # cloud patch
    scl[150:160, 150:170] = 3  # cloud shadow
    save_band(BEFORE_DIR / f"T43PFP_20240115_SCL_20m.tif", scl, "uint8")

    print(f"       Saved 5 files to {BEFORE_DIR}/")


def generate_after():
    """Generate AFTER scene with simulated changes."""
    print("[DEMO] Generating AFTER scene with changes...")
    AFTER_DIR.mkdir(parents=True, exist_ok=True)

    np.random.seed(99)
    base = np.random.rand(H, W).astype(np.float32) * 0.3 + 0.1

    # Simulate strong changes in specific regions
    # 1. Construction area (big reflectance jump)
    base[80:120, 80:120] += 0.5
    # 2. Deforestation (big reflectance drop)
    base[30:60, 130:170] -= 0.4

    for band, factor in [("B02", 1.0), ("B03", 1.2), ("B04", 0.8), ("B08", 1.5)]:
        noise = np.random.rand(H, W).astype(np.float32) * 0.02
        data = (base * factor + noise) * 10000
        data = np.clip(data, 0, 10000)
        save_band(AFTER_DIR / f"T43PFP_20240601_{band}_10m.tif", data, "uint16")

    # SCL: mostly clear with one small cloud
    scl = np.full((H, W), 4, dtype=np.uint8)
    scl[10:20, 10:20] = 9  # small cloud
    save_band(AFTER_DIR / f"T43PFP_20240601_SCL_20m.tif", scl, "uint8")

    print(f"       Saved 5 files to {AFTER_DIR}/")


def run_pipeline():
    """Run the full pipeline."""
    print("\n[DEMO] Running pipeline...")
    import subprocess
    result = subprocess.run(
        ["python", "run_pipeline.py"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode


def verify_outputs():
    """Check all expected outputs exist and are valid."""
    print("[DEMO] Verifying outputs...")
    expected = [
        "outputs/maps/change_magnitude.tif",
        "outputs/maps/change_mask.tif",
        "data/processed/spectral_delta.tif",
    ]

    all_ok = True
    for f in expected:
        path = Path(f)
        if not path.exists():
            print(f"  FAIL: {f} — missing!")
            all_ok = False
            continue

        with rasterio.open(f) as src:
            d = src.read(1)
            print(
                f"  OK: {f} | shape={src.shape} | crs={src.crs} | "
                f"dtype={src.dtypes[0]} | min={float(np.nanmin(d)):.4f} | "
                f"max={float(np.nanmax(d)):.4f}"
            )

    # Check change_mask values are only 0 or 1
    with rasterio.open("outputs/maps/change_mask.tif") as src:
        mask = src.read(1)
        unique = set(np.unique(mask).tolist())
        if not unique.issubset({0, 1}):
            print(f"  FAIL: Mask has unexpected values: {unique}")
            all_ok = False
        elif unique == {0}:
            print("  WARN: Mask is all zeros — no changes detected")
        else:
            pct = mask.sum() / mask.size * 100
            print(f"  OK: Change mask has both 0 and 1 ({pct:.2f}% changed)")

    # Check spectral_delta has 4 bands
    with rasterio.open("data/processed/spectral_delta.tif") as src:
        if src.count != 4:
            print(f"  FAIL: spectral_delta has {src.count} bands, expected 4")
            all_ok = False
        else:
            print("  OK: spectral_delta has 4 bands [dB02, dB03, dB04, dB08]")

    return all_ok


def cleanup():
    """Remove generated test data."""
    print("\n[DEMO] Cleaning up test data...")
    for d in [BEFORE_DIR, AFTER_DIR]:
        if d.exists():
            shutil.rmtree(d)
    for f in [
        "outputs/maps/change_magnitude.tif",
        "outputs/maps/change_mask.tif",
        "data/processed/spectral_delta.tif",
    ]:
        p = Path(f)
        if p.exists():
            p.unlink()
    print("       Done.")


def main():
    print("=" * 60)
    print("CIPHER-X — Demo / Smoke Test")
    print("=" * 60)

    generate_before()
    generate_after()

    rc = run_pipeline()
    if rc != 0:
        print(f"\n[DEMO] FAIL: Pipeline exited with code {rc}")
        return

    ok = verify_outputs()

    print("\n" + "=" * 60)
    if ok:
        print("DEMO RESULT: ALL CHECKS PASSED")
    else:
        print("DEMO RESULT: SOME CHECKS FAILED — see above")
    print("=" * 60)

    cleanup()


if __name__ == "__main__":
    main()
