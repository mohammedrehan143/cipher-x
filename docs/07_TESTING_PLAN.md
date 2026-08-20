# 07 — TESTING PLAN

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20 (updated: tests reflect BUG-01 fix in compute_magnitude)

---

## 1. Testing Strategy

Given the 24-hour hackathon constraint, we follow a **pragmatic testing approach**:

1. **Smoke tests** — Does every module run without crashing?
2. **Output validation** — Do expected files exist with correct shapes, types, and values?
3. **Cross-person interface validation** — Does each downstream person receive the exact schema guaranteed by upstream?
4. **Visual inspection** — Do maps and charts in QGIS and Streamlit look sensible?

---

## 2. Person 1 — Preprocessing & CVA Tests

### Test P1-01: Environment Check
```bash
<<<<<<< HEAD
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
=======
python -c "import rasterio, numpy, skimage, scipy; print('Person 1 dependencies OK')"
```

### Test P1-02: End-to-End Pipeline Run
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
```bash
python run_pipeline.py
```

<<<<<<< HEAD
**Verify outputs after run:**
=======
### Test P1-03: Output Verification
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
```bash
python -c "
import rasterio, numpy as np, os
for f in ['outputs/maps/change_magnitude.tif', 'outputs/maps/change_mask.tif', 'data/processed/spectral_delta.tif']:
    assert os.path.exists(f), f'MISSING: {f}'
    with rasterio.open(f) as src:
        d = src.read(1)
<<<<<<< HEAD
        print(f'OK  {f}')
        print(f'    shape={src.shape}, crs={src.crs}')
        print(f'    min={float(np.nanmin(d)):.4f}, max={float(np.nanmax(d)):.4f}')

mask_data = rasterio.open('outputs/maps/change_mask.tif').read(1)
unique_vals = set(mask_data.flatten().tolist())
assert unique_vals.issubset({0, 1}), f'Unexpected mask values: {unique_vals}'
assert 1 in unique_vals, 'Mask is all zeros — no changes detected'
print('ALL P1 TESTS PASSED')
=======
        print(f'OK: {f} | shape={src.shape} | min={float(np.nanmin(d)):.4f} | max={float(np.nanmax(d)):.4f}')
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
"
```

---

## 3. Person 2 — Vectorization & Feature Tests

<<<<<<< HEAD
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
=======
### Test P2-01: Dependencies & Prerequisite Check
```bash
python -c "
import rasterio, geopandas, shapely, skimage, scipy, os
for f in ['outputs/maps/change_mask.tif', 'outputs/maps/change_magnitude.tif', 'data/processed/spectral_delta.tif']:
    assert os.path.exists(f), f'Prerequisite missing: {f}'
print('Person 2 dependencies and prerequisites OK')
"
```

### Test P2-02: End-to-End Vectorization Run
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
```bash
python run_vectorize.py
```

<<<<<<< HEAD
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
=======
### Test P2-03: Output & Feature Column Verification
```bash
python -c "
import geopandas as gpd, pandas as pd, os
assert os.path.exists('outputs/polygons/change_results.geojson'), 'GeoJSON missing'
assert os.path.exists('outputs/predictions/change_features.csv'), 'Features CSV missing'

gdf = gpd.read_file('outputs/polygons/change_results.geojson')
df = pd.read_csv('outputs/predictions/change_features.csv')

print(f'GeoJSON polygons: {len(gdf)}, CRS: {gdf.crs}')
print(f'CSV rows: {len(df)}, columns: {len(df.columns)}')
assert len(gdf) == len(df), 'Row count mismatch'
print('Person 2 outputs verified successfully')
"
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
```
**Pass:** Opens at `http://localhost:8501` without errors.  
**Fail:** Check `app/main.py` exists and all imports resolve.

---

## 4. Person 3 — ML Classification Tests

<<<<<<< HEAD
- [ ] Open `outputs/maps/change_magnitude.tif` in QGIS — bright areas = high change
- [ ] Open `outputs/maps/change_mask.tif` in QGIS — binary patches look spatially coherent
- [ ] Overlay on Google Maps / OSM basemap for sanity check
- [ ] Cloud-masked areas in QGIS show NoData (transparent), NOT black zeros

> **Note:** The last check verifies the BUG-01 fix — before the fix, cloud-masked pixels showed as 0.0 (black), not NoData (transparent).
=======
### Test P3-01: ML Dependencies & Features Check
```bash
python -c "
import sklearn, joblib, pandas as pd, numpy as np, os
assert os.path.exists('outputs/predictions/change_features.csv'), 'Features CSV missing from Person 2'
df = pd.read_csv('outputs/predictions/change_features.csv')
print(f'Person 3 ready. Input dataset has {len(df)} samples and {len(df.columns)} columns.')
"
```

### Test P3-02: Labelling & Rule Sanity
```bash
python -c "
from src.models.labeller import auto_label
import pandas as pd
df = pd.read_csv('outputs/predictions/change_features.csv')
labelled = auto_label(df)
assert 'label' in labelled.columns and 'label_name' in labelled.columns
print('Class distribution in provisional labels:')
print(labelled['label_name'].value_counts())
"
```

### Test P3-03: Model Training & Artifact Generation
```bash
python -c "
from src.models.classifier import load_training_data, train_model, save_artifacts
from pathlib import Path
X, y, imputer, feature_names = load_training_data(Path('data/labels/prototype_labels.csv'))
clf, metrics = train_model(X, y, feature_names)
print(f'Validation Accuracy: {metrics.get(\"accuracy\", 0.0):.4f}')
save_artifacts(clf, imputer, {'features': feature_names}, Path('models'))
print('Model training and artifact test passed')
"
```

### Test P3-04: End-to-End Classification Runner
```bash
python run_classify.py
```

### Test P3-05: Prediction Output Verification (Handoff to Person 4)
```bash
python -c "
import pandas as pd, os
assert os.path.exists('outputs/predictions/predictions.csv'), 'predictions.csv missing'
df = pd.read_csv('outputs/predictions/predictions.csv')
print(f'Predictions generated: {len(df)} rows')
assert 'predicted_class' in df.columns and 'confidence' in df.columns
assert df['confidence'].between(0.0, 1.0).all(), 'Confidence outside [0, 1]'
print('Person 3 verification passed')
"
```
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

---

## 5. Person 4 — Dashboard & Integration Tests

<<<<<<< HEAD
| Scenario | Acceptable? | Mitigation |
|---|---|---|
| SCL band missing | Yes — skip masking, log warning | Document clearly |
| All pixels masked by cloud | No — pipeline exits with code 1 | User selects clearer date |
| Change mask is all-zero | Investigate — may need manual threshold | Log Otsu value, try lower threshold |
| CRS mismatch between S2 scenes | Handled by `align.py` | Recommend same tile for MVPn |
| `pyproj` not installed | Fixed — now in `requirements.txt` (BUG-02) | Run `pip install -r requirements.txt` |
=======
### Test P4-01: Data Join Test
```python
import geopandas as gpd
import pandas as pd

gdf = gpd.read_file("outputs/polygons/change_results.geojson")
preds = pd.read_csv("outputs/predictions/predictions.csv")

merged = gdf.merge(preds[["id", "predicted_class", "predicted_label", "confidence"]], on="id")
assert len(merged) == len(gdf), "Join lost rows!"
print(f"Join successful! Ready for Streamlit mapping with {len(merged)} polygons.")
```

### Test P4-02: Dashboard Launch Test
```bash
streamlit run app/main.py --server.headless true
```
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
