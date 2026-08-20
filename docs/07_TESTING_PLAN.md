# 07 — TESTING PLAN

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20  

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
python -c "import rasterio, numpy, skimage, scipy, pyproj; print('Person 1 dependencies OK')"
```

### Test P1-02: End-to-End Pipeline Run
```bash
python run_pipeline.py
```

### Test P1-03: Output Verification
```bash
python -c "
import rasterio, numpy as np, os
for f in ['outputs/maps/change_magnitude.tif', 'outputs/maps/change_mask.tif', 'data/processed/spectral_delta.tif']:
    assert os.path.exists(f), f'MISSING: {f}'
    with rasterio.open(f) as src:
        d = src.read(1)
        print(f'OK: {f} | shape={src.shape} | min={float(np.nanmin(d)):.4f} | max={float(np.nanmax(d)):.4f}')
"
```

---

## 3. Person 2 — Vectorization & Feature Tests

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
```bash
python run_vectorize.py
```

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
```

---

## 4. Person 3 — ML Classification Tests

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

---

## 5. Person 4 — Dashboard & Integration Tests

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
