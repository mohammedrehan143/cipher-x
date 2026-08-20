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
**Fail:** `ModuleNotFoundError` → run `pip install -r requirements.txt`

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
print('ALL TESTS PASSED')
"
```

---

## 3. Person 2 — Vectorization, Features, ML (Placeholder)

> To be filled in by Person 2.

### Test P2-01: Vectorization
- Input: `change_mask.tif`
- Expected: `outputs/polygons/changes.geojson` exists, valid GeoJSON, ≥ 1 feature

### Test P2-02: Feature Extraction
- Expected: each polygon has numeric feature attributes (NDVI_delta, etc.)

### Test P2-03: ML Classification
- Expected: each polygon has a `class_label` attribute with valid class string

### Test P2-04: Dashboard
- Expected: `streamlit run app/main.py` opens without errors

---

## 4. Visual Inspection Checklist

- [ ] Open `outputs/maps/change_magnitude.tif` in QGIS
- [ ] Verify bright areas correspond to areas of visible change
- [ ] Open `outputs/maps/change_mask.tif` in QGIS (binary 0/1)
- [ ] Change regions look spatially coherent (not random noise)
- [ ] Overlay on Google Maps / OpenStreetMap basemap for sanity check

---

## 5. Known Acceptable Failures (MVP)

| Scenario | Acceptable? | Mitigation |
|---|---|---|
| SCL band missing | Yes — skip masking, log warning | Document clearly |
| All pixels masked by cloud | No — pipeline should raise error | User selects better date |
| Change mask is all-zero | Investigate threshold — may need manual override | Log Otsu threshold value |
| CRS mismatch between S2 scenes | Handled automatically by align.py | Verify same tile |
