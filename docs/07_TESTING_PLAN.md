# 07 — TESTING PLAN

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Testing Strategy

Given the 24-hour hackathon constraint, we follow a **pragmatic testing approach**:

1. **Smoke tests** — Does it run without crashing?
2. **Output validation** — Do expected files exist with correct shapes/values?
3. **Visual inspection** — Does the change map look reasonable?

No formal pytest suite is required for MVP, but verification scripts are mandatory.

---

## 2. Person 1 — Preprocessing & CVA Tests

### Test P1-01: Environment Check
```bash
python -c "import rasterio, numpy, skimage, scipy; print('All dependencies OK')"
```
**Pass:** prints `All dependencies OK`  
**Fail:** `ModuleNotFoundError` -> run `pip install -r requirements.txt`

---

### Test P1-02: Band Loader (Synthetic Data)
```python
# Run from project root
from src.preprocessing.loader import load_bands
from pathlib import Path

# Place any valid .tif in data/sentinel/before/ for this test
bands, scl, profile = load_bands(Path("data/sentinel/before"))
assert bands.shape[0] == 4,        "Expected 4 bands (B02,B03,B04,B08)"
assert bands.dtype == "float32",   "Expected float32"
assert bands.max() <= 1.1,         "Reflectance should be ~0-1"
assert scl.ndim == 2,              "SCL should be 2D"
print("P1-02 PASS")
```

---

### Test P1-03: Alignment
```python
from src.preprocessing.align import align_images

# After alignment, shapes must match exactly
assert after_bands_aligned.shape == before_bands.shape, "Shape mismatch after alignment"
print("P1-03 PASS")
```

---

### Test P1-04: Cloud Masking
```python
from src.preprocessing.masking import scl_to_mask
import numpy as np

# Synthetic SCL: all valid (class 4 = vegetation)
scl = np.full((100, 100), 4, dtype=np.uint8)
mask = scl_to_mask(scl)
assert mask.all(), "All pixels should be valid"

# Synthetic SCL: all cloud (class 9)
scl_cloud = np.full((100, 100), 9, dtype=np.uint8)
mask_cloud = scl_to_mask(scl_cloud)
assert not mask_cloud.any(), "All pixels should be masked"
print("P1-04 PASS")
```

---

### Test P1-05: CVA Magnitude
```python
from src.cva.compute import compute_delta, compute_magnitude
import numpy as np

H, W = 50, 50
before = np.random.rand(4, H, W).astype(np.float32)
after  = before + 0.1   # simulate uniform +0.1 change
valid  = np.ones((H, W), dtype=bool)

delta = compute_delta(before, after, valid)
mag   = compute_magnitude(delta)

# Magnitude of +0.1 change in 4 bands = sqrt(4 * 0.01) = 0.2
expected = np.sqrt(4 * 0.01)
assert np.allclose(mag[valid], expected, atol=1e-4), f"Expected ~{expected:.4f}"
print("P1-05 PASS")
```

---

### Test P1-06: Threshold & Mask
```python
from src.cva.threshold import otsu_threshold, apply_threshold
import numpy as np

# Two clear populations: low noise (0.05) and high change (0.5)
low  = np.random.normal(0.05, 0.01, 1000)
high = np.random.normal(0.50, 0.01, 1000)
mag  = np.concatenate([low, high])

thresh = otsu_threshold(mag)
assert 0.1 < thresh < 0.4, f"Threshold {thresh:.3f} seems unreasonable"
print("P1-06 PASS")
```

---

### Test P1-07: End-to-End Pipeline Run
```bash
python run_pipeline.py
```

**Expected outputs (check after run):**
```bash
python -c "
import rasterio, numpy as np, os

files = [
    'outputs/maps/change_magnitude.tif',
    'outputs/maps/change_mask.tif',
    'data/processed/spectral_delta.tif',
]
for f in files:
    assert os.path.exists(f), f'MISSING: {f}'
    with rasterio.open(f) as src:
        d = src.read(1)
        print(f'OK: {f} | shape={src.shape} | min={float(np.nanmin(d)):.4f} | max={float(np.nanmax(d)):.4f}')

mask_data = rasterio.open('outputs/maps/change_mask.tif').read(1)
unique = set(mask_data.flatten().tolist())
assert unique.issubset({0,1}), f'Mask contains unexpected values: {unique}'
assert 1 in unique, 'Mask is all zeros — no changes detected!'
print('ALL P1 TESTS PASSED')
"
```

---

## 3. Person 2 — Vectorization & Feature Extraction Tests

### Test P2-01: Environment Check
```bash
python -c "import rasterio, geopandas, shapely, skimage, scipy; print('Person 2 dependencies OK')"
```
**Pass:** prints `Person 2 dependencies OK`  
**Fail:** `ModuleNotFoundError` -> run `pip install -r requirements.txt`

---

### Test P2-02: Person 1 Output Check (Prerequisite)
```bash
python -c "
import os
required = [
    'outputs/maps/change_mask.tif',
    'outputs/maps/change_magnitude.tif',
    'data/processed/spectral_delta.tif',
]
for f in required:
    assert os.path.exists(f), f'MISSING (run Person 1 pipeline first): {f}'
    print(f'OK: {f}')
print('Person 1 outputs confirmed. Person 2 can proceed.')
"
```

---

### Test P2-03: Vectorization Unit Test
```python
from src.vectorization.polygonize import load_and_clean_mask, polygonize_mask
from pathlib import Path

mask, profile = load_and_clean_mask(Path("outputs/maps/change_mask.tif"))
assert mask.ndim == 2,                "Mask should be 2D"
assert set(mask.flatten().tolist()).issubset({0,1}), "Mask should only contain 0 and 1"

gdf = polygonize_mask(mask, profile, min_area_m2=1000.0)
assert len(gdf) >= 1,                "At least one polygon expected"
assert "area_m2" in gdf.columns,     "area_m2 column missing"
assert "latitude" in gdf.columns,    "latitude column missing"
assert "longitude" in gdf.columns,   "longitude column missing"
assert gdf["area_m2"].min() >= 1000, "Polygons smaller than min_area_m2 were not filtered"
assert gdf["latitude"].between(-90, 90).all(),   "Latitude out of WGS84 range"
assert gdf["longitude"].between(-180, 180).all(), "Longitude out of WGS84 range"
print(f"P2-03 PASS — {len(gdf)} polygons generated")
```

---

### Test P2-04: NDVI Unit Test
```python
from src.features.ndvi import compute_ndvi
from pathlib import Path
import rasterio, numpy as np

with rasterio.open("outputs/maps/change_mask.tif") as src:
    profile_ref = src.profile

ndvi = compute_ndvi(Path("data/sentinel/before"), profile_ref)
assert ndvi.ndim == 2,                  "NDVI should be 2D"
assert ndvi.dtype == np.float32,        "NDVI should be float32"
assert np.nanmin(ndvi) >= -1.0,         "NDVI min below -1"
assert np.nanmax(ndvi) <= 1.0,          "NDVI max above 1"
print(f"P2-04 PASS — NDVI range: [{float(np.nanmin(ndvi)):.3f}, {float(np.nanmax(ndvi)):.3f}]")
```

---

### Test P2-05: Feature Extraction Column Check
```python
from src.features.extractor import extract_features
# (run after vectorization and NDVI steps)

required_cols = [
    "id", "area_m2", "latitude", "longitude",
    "cva_mean", "cva_max",
    "ndvi_before", "ndvi_after", "delta_ndvi",
    "delta_b02", "delta_b03", "delta_b04", "delta_b08",
    "bbox_width_m", "bbox_height_m", "compactness"
]
for col in required_cols:
    assert col in gdf.columns, f"Missing column: {col}"
assert (gdf["area_m2"] > 0).all(), "All area_m2 should be positive"
assert (gdf["compactness"].between(0, 1)).all(), "Compactness should be 0-1"
print(f"P2-05 PASS — All {len(required_cols)} columns present")
```

---

### Test P2-06: End-to-End Person 2 Pipeline Run
```bash
python run_vectorize.py
```

**Expected console output (abbreviated):**
```
[1/6] Checking Person 1 outputs exist...
[2/6] Loading and vectorizing change mask...
[3/6] Computing NDVI (before)...
[4/6] Computing NDVI (after)...
[5/6] Extracting polygon features...
[6/6] Saving outputs...
Done.
```

**Verify outputs:**
```bash
python -c "
import geopandas as gpd, pandas as pd, os

# Check GeoJSON
assert os.path.exists('outputs/polygons/change_results.geojson'), 'GeoJSON missing'
gdf = gpd.read_file('outputs/polygons/change_results.geojson')
print(f'GeoJSON: {len(gdf)} polygons, {len(gdf.columns)} columns')
print(f'Columns: {list(gdf.columns)}')
assert gdf.crs.to_epsg() == 4326, 'GeoJSON CRS must be EPSG:4326'

# Check CSV
assert os.path.exists('outputs/predictions/change_features.csv'), 'CSV missing'
df = pd.read_csv('outputs/predictions/change_features.csv')
print(f'CSV: {len(df)} rows, {len(df.columns)} columns')
assert len(df) == len(gdf), 'CSV and GeoJSON row count must match'

print('ALL P2 TESTS PASSED')
"
```

---

## 4. Visual Inspection Checklist

- [ ] Open `outputs/maps/change_magnitude.tif` in QGIS
- [ ] Verify bright areas correspond to areas of visible change
- [ ] Open `outputs/maps/change_mask.tif` in QGIS (binary 0/1)
- [ ] Change regions look spatially coherent (not random noise)
- [ ] Open `outputs/polygons/change_results.geojson` in QGIS
- [ ] Polygons overlay correctly on the raster
- [ ] Attribute table shows numeric values for all feature columns
- [ ] Overlay on Google Maps / OpenStreetMap basemap for sanity check

---

## 5. Known Acceptable Failures (MVP)

| Scenario | Acceptable? | Mitigation |
|---|---|---|
| SCL band missing | Yes - skip masking, log warning | Document clearly |
| All pixels masked by cloud | No - pipeline should raise error | User selects better date |
| Change mask is all-zero | Investigate threshold - may need manual override | Log Otsu threshold value |
| CRS mismatch between S2 scenes | Handled automatically by align.py | Verify same tile |
| B04/B08 raw bands not found | Yes - NDVI = NaN, pipeline continues | Log warning; all other features still work |
| Zero polygons after area filter | No - lower MIN_AREA_M2 or check mask | Use `--min-area 100` to test |
