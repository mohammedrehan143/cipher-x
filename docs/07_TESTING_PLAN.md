# 07 — TESTING PLAN

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20 (updated: tests reflect BUG-01 fix in compute_magnitude)

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
python -c "import rasterio, numpy, skimage, scipy, pyproj; print('All dependencies OK')"
```
**Pass:** prints `All dependencies OK`  
**Fail:** `ModuleNotFoundError` → run `pip install -r requirements.txt`

---

### Test P1-02: Band Loader
```python
from src.preprocessing.loader import load_bands
from pathlib import Path

bands, scl, profile = load_bands(Path("data/sentinel/before"))
assert bands.shape[0] == 4,        "Expected 4 bands (B02,B03,B04,B08)"
assert bands.dtype == "float32",   "Expected float32"
assert bands.max() <= 1.1,         "Reflectance should be ~0–1"
assert scl.ndim == 2,              "SCL should be 2D"
print("P1-02 PASS")
```

---

### Test P1-03: Alignment
```python
from src.preprocessing.align import align_images

aligned_after_bands, aligned_after_scl = align_images(
    before_bands, before_scl, before_profile,
    after_bands, after_scl, after_profile
)
assert aligned_after_bands.shape == before_bands.shape, "Band shape mismatch after alignment"
assert aligned_after_scl.shape == before_scl.shape, "SCL shape mismatch after alignment"
print("P1-03 PASS")
```

---

### Test P1-04: Cloud Masking
```python
from src.preprocessing.masking import scl_to_mask
import numpy as np

# All vegetation (class 4) → all valid
scl = np.full((100, 100), 4, dtype=np.uint8)
mask = scl_to_mask(scl)
assert mask.all(), "All pixels should be valid"

# All high cloud (class 9) → all masked
scl_cloud = np.full((100, 100), 9, dtype=np.uint8)
mask_cloud = scl_to_mask(scl_cloud)
assert not mask_cloud.any(), "All pixels should be masked"
print("P1-04 PASS")
```

---

### Test P1-05: CVA Magnitude — NaN Propagation (BUG-01 fix verification)
```python
from src.cva.compute import compute_delta, compute_magnitude
import numpy as np

H, W = 50, 50
before = np.random.rand(4, H, W).astype(np.float32)
after  = before + 0.1   # uniform +0.1 change in all bands
valid  = np.ones((H, W), dtype=bool)

# Mask a region to all-NaN
valid[10:20, 10:20] = False
before[:, ~valid] = np.nan
after[:, ~valid]  = np.nan

delta = compute_delta(before, after, valid)
mag   = compute_magnitude(delta)

# BUG-01 fix: masked region must be NaN, not 0
masked_region = mag[10:20, 10:20]
assert np.all(np.isnan(masked_region)), \
    f"BUG-01: masked pixels should be NaN, got: {masked_region[0,0]}"

# Valid pixels: magnitude of +0.1 change in 4 bands = sqrt(4 * 0.01) = 0.2
valid_region = mag[valid]
expected = np.sqrt(4 * 0.01)
assert np.allclose(valid_region, expected, atol=1e-4), \
    f"Expected magnitude ~{expected:.4f}, got {valid_region.mean():.4f}"

print("P1-05 PASS (BUG-01 fix verified)")
```

---

### Test P1-06: Otsu Threshold on Bimodal Distribution
```python
from src.cva.threshold import otsu_threshold, apply_threshold
import numpy as np

low  = np.random.normal(0.05, 0.01, 1000).astype(np.float32)
high = np.random.normal(0.50, 0.01, 1000).astype(np.float32)
mag  = np.concatenate([low, high])

thresh = otsu_threshold(mag)
assert 0.1 < thresh < 0.4, f"Threshold {thresh:.3f} out of expected range"
print(f"P1-06 PASS — Otsu threshold: {thresh:.4f}")
```

---

### Test P1-07: End-to-End Pipeline Run
```bash
python run_pipeline.py
```

**Verify outputs after run:**
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
        print(f'OK  {f}')
        print(f'    shape={src.shape}, crs={src.crs}')
        print(f'    min={float(np.nanmin(d)):.4f}, max={float(np.nanmax(d)):.4f}')

mask_data = rasterio.open('outputs/maps/change_mask.tif').read(1)
unique_vals = set(mask_data.flatten().tolist())
assert unique_vals.issubset({0, 1}), f'Unexpected mask values: {unique_vals}'
assert 1 in unique_vals, 'Mask is all zeros — no changes detected'
print('ALL P1 TESTS PASSED')
"
```

---

## 3. Person 2 — Vectorization & Feature Tests

### Test P2-01: Vectorization
```python
from src.vectorization.polygonize import load_and_clean_mask, polygonize_mask

mask, profile = load_and_clean_mask("outputs/maps/change_mask.tif")
gdf = polygonize_mask(mask, profile, min_area_m2=500.0)

assert len(gdf) >= 1, "Expected at least 1 change polygon"
assert "area_m2" in gdf.columns
assert "latitude" in gdf.columns
assert gdf.crs.to_epsg() == 4326, "Output CRS should be EPSG:4326"
print(f"P2-01 PASS — {len(gdf)} polygons found")
```

---

### Test P2-02: Feature Extraction
```bash
python run_vectorize.py
```

```python
import pandas as pd
df = pd.read_csv("outputs/predictions/change_features.csv")
expected_cols = ["id","area_m2","latitude","longitude","cva_mean","cva_max",
                 "ndvi_before","ndvi_after","delta_ndvi",
                 "delta_b02","delta_b03","delta_b04","delta_b08",
                 "bbox_width_m","bbox_height_m","compactness"]
for col in expected_cols:
    assert col in df.columns, f"Missing column: {col}"
print(f"P2-02 PASS — {len(df)} rows, {len(df.columns)} features")
```

---

### Test P2-03: ML Classifier (placeholder — to be built)
> Person 2 to add tests once `src/models/classifier.py` is built.
- Expected: `outputs/predictions/classified.geojson` exists
- Expected: each feature has a `class_label` attribute with valid class string

### Test P2-04: Dashboard
```bash
streamlit run app/main.py
```
**Pass:** Opens at `http://localhost:8501` without errors.  
**Fail:** Check `app/main.py` exists and all imports resolve.

---

## 4. Visual Inspection Checklist

- [ ] Open `outputs/maps/change_magnitude.tif` in QGIS — bright areas = high change
- [ ] Open `outputs/maps/change_mask.tif` in QGIS — binary patches look spatially coherent
- [ ] Overlay on Google Maps / OSM basemap for sanity check
- [ ] Cloud-masked areas in QGIS show NoData (transparent), NOT black zeros

> **Note:** The last check verifies the BUG-01 fix — before the fix, cloud-masked pixels showed as 0.0 (black), not NoData (transparent).

---

## 5. Known Acceptable Failures (MVP)

| Scenario | Acceptable? | Mitigation |
|---|---|---|
| SCL band missing | Yes — skip masking, log warning | Document clearly |
| All pixels masked by cloud | No — pipeline exits with code 1 | User selects clearer date |
| Change mask is all-zero | Investigate — may need manual threshold | Log Otsu value, try lower threshold |
| CRS mismatch between S2 scenes | Handled by `align.py` | Recommend same tile for MVPn |
| `pyproj` not installed | Fixed — now in `requirements.txt` (BUG-02) | Run `pip install -r requirements.txt` |
