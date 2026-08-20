# 05 — MODULE RESPONSIBILITIES

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20 (updated: removed erroneous Person 3 references — BUG-05 fix)

---

## 1. Team Structure

| Person | Role | Focus Area |
|---|---|---|
<<<<<<< HEAD
| Person 1 | Satellite Data Engineer | Sentinel-2 preprocessing + CVA change detection |
| Person 2 | ML & GIS Engineer | Vectorization + Feature extraction + ML classifier + Streamlit dashboard |

> **Note:** This is a 2-person team. There is no Person 3. The ML classifier is Person 2's responsibility.
=======
| **Person 1** | Satellite Data Engineer | Sentinel-2 Ingestion, Preprocessing & CVA |
| **Person 2** | GIS & Feature Engineer | Mask Vectorization, NDVI, Feature Extraction & Table Generation |
| **Person 3** | ML Engineer | Label Creation, Random Forest Classifier & Inference |
| **Person 4** | Frontend & GIS Visualizer | Streamlit Interactive GIS Dashboard & Analytics |
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

---

## 2. Person 1 — Sentinel-2 Preprocessing & CVA

### Owned Modules

<<<<<<< HEAD
| Module | File | Status |
|---|---|---|
| Band Loader | `src/preprocessing/loader.py` | ✅ Complete |
| Image Alignment | `src/preprocessing/align.py` | ✅ Complete (BUG-04 fixed) |
| Cloud Masking | `src/preprocessing/masking.py` | ✅ Complete |
| CVA Computation | `src/cva/compute.py` | ✅ Complete (BUG-01 fixed) |
| Thresholding | `src/cva/threshold.py` | ✅ Complete |
| Pipeline Runner | `run_pipeline.py` | ✅ Complete (BUG-06 fixed) |
=======
| Module | File | Status | Description |
|---|---|---|---|
| Band Loader | `src/preprocessing/loader.py` | ✅ Done | `find_band_file`, `load_bands` |
| Image Alignment | `src/preprocessing/align.py` | ✅ Done | `align_to_reference`, `align_images` |
| Cloud Masking | `src/preprocessing/masking.py` | ✅ Done | `scl_to_mask`, `combine_masks`, `apply_mask` |
| CVA Computation | `src/cva/compute.py` | ✅ Done | `compute_delta`, `compute_magnitude`, `save_raster` |
| Thresholding | `src/cva/threshold.py` | ✅ Done | `otsu_threshold`, `apply_threshold`, `clean_mask`, `save_change_mask` |
| Pipeline Runner | `run_pipeline.py` | ✅ Done | CLI orchestrator for Person 1 |
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

### Deliverables to Person 2

| File | Description |
|---|---|
| `outputs/maps/change_mask.tif` | Binary change mask (uint8, 0=no change, 1=change) |
| `outputs/maps/change_magnitude.tif` | Continuous CVA magnitude (float32, NaN where cloud-masked) |
| `data/processed/spectral_delta.tif` | 4-band spectral delta (float32): [ΔB02, ΔB03, ΔB04, ΔB08] |

<<<<<<< HEAD
### Guaranteed Interface

- All outputs share the same CRS and transform as the input Sentinel-2 data.
- Cloud-masked pixels are **NaN** in float rasters and **0** in the mask raster.
- Band order in `spectral_delta.tif`: Band 1=ΔB02, Band 2=ΔB03, Band 3=ΔB04, Band 4=ΔB08.
- Pipeline is triggered by: `python run_pipeline.py`

### NOT in Person 1's scope

- Vectorization of change mask to polygons
- Feature extraction from polygons
- ML classification
- Streamlit dashboard
- GeoJSON output

=======
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
---

## 3. Person 2 — Vectorization, Features, ML Classifier & Dashboard

### Owned Modules

<<<<<<< HEAD
| Module | File | Status |
|---|---|---|
| Vectorization | `src/vectorization/polygonize.py` | ✅ Complete |
| NDVI Computation | `src/features/ndvi.py` | ✅ Complete |
| Feature Extraction | `src/features/extractor.py` | ✅ Complete (16 features) |
| Vectorize Runner | `run_vectorize.py` | ✅ Complete |
| **ML Classifier** | `src/models/classifier.py` | ❌ **Not yet built — Person 2's task** |
| **Dashboard** | `app/main.py` | ❌ **Not yet built — Person 2's task** |

### Inputs from Person 1

Person 2 reads these files (guaranteed to exist after `python run_pipeline.py`):

| File | How to use |
|---|---|
| `outputs/maps/change_mask.tif` | `rasterio.open()` → vectorize with `rasterio.features.shapes()` |
| `outputs/maps/change_magnitude.tif` | Mean magnitude per polygon attribute |
| `data/processed/spectral_delta.tif` | 4-band per-polygon spectral features |

### Reading Person 1 Outputs (Sample Code)

```python
import rasterio
import numpy as np

# Read change mask
with rasterio.open("outputs/maps/change_mask.tif") as src:
    mask = src.read(1)           # shape (H, W), uint8, values 0 or 1
    transform = src.transform
    crs = src.crs

# Read spectral delta for features
with rasterio.open("data/processed/spectral_delta.tif") as src:
    delta = src.read()           # shape (4, H, W)
    # Band 1=ΔB02, Band 2=ΔB03, Band 3=ΔB04, Band 4=ΔB08
```

### Person 2 Deliverables

| File | Description |
|---|---|
| `outputs/polygons/change_results.geojson` | Change polygons with 16 feature attributes |
| `outputs/predictions/change_features.csv` | Flat feature table (16 columns) for ML input |
| `outputs/predictions/classified.geojson` | Classified polygons with `class_label` attribute |
| `app/main.py` | Streamlit dashboard entry point |

### How to Run Person 2 Pipeline

```bash
# Step 1: Person 1 must run first
python run_pipeline.py

# Step 2: Vectorize and extract features
python run_vectorize.py

# Step 3: Train/run ML classifier (to be built)
python src/models/classifier.py

# Step 4: Launch dashboard
streamlit run app/main.py
```

=======
| Module | File | Status | Description |
|---|---|---|---|
| Change Mask Vectorization | `src/vectorization/polygonize.py` | ✅ Done | `load_and_clean_mask`, `polygonize_mask` |
| NDVI Calculator | `src/features/ndvi.py` | ✅ Done | `compute_ndvi` |
| Feature Extractor | `src/features/extractor.py` | ✅ Done | `extract_features` (16 attributes) |
| Person 2 Runner | `run_vectorize.py` | ✅ Done | CLI orchestrator for Person 2 |

### Deliverables to Person 3 & Person 4

| File | Description | Consumer |
|---|---|---|
| `outputs/polygons/change_results.geojson` | Change polygons with 16 attributes + geometry | Person 4 (GIS display) |
| `outputs/predictions/change_features.csv` | Flat tabular feature dataset (16 columns) | Person 3 (ML training & inference) |

---

## 4. Person 3 — ML Classification

### Owned Modules

| Module | File | Status | Description |
|---|---|---|---|
| Prototype Labeller | `src/models/labeller.py` | ⏳ Planned | Rule-based auto-labelling for prototype training set |
| Random Forest Classifier | `src/models/classifier.py` | ⏳ Planned | Data loading, median imputation, balanced RF training, evaluation |
| Classification Runner | `run_classify.py` | ⏳ Planned | End-to-end ML training & batch inference orchestrator |

### Deliverables to Person 4

| File | Description | Consumer |
|---|---|---|
| `outputs/predictions/predictions.csv` | Polygon predictions (`id`, `predicted_class`, `predicted_label`, `confidence`, features) | Person 4 (Dashboard) |
| `models/rf_classifier.joblib` | Serialized Random Forest model | App / API |
| `models/rf_imputer.joblib` | Serialized feature imputer | App / API |
| `models/rf_metadata.json` | Model metadata, feature list & class names | Documentation / App |

### Target Change Classes

1. `New Construction` (Class 0)
2. `Road Change / Expansion` (Class 1)
3. `Vegetation Clearing` (Class 2)
4. `Excavation / Mining` (Class 3)
5. `Other Human Change` (Class 4)

---

## 5. Person 4 — Streamlit GIS Dashboard (Downstream)

### Owned Modules

| Module | File | Status | Description |
|---|---|---|---|
| Dashboard App | `app/main.py` | ⏳ Pending | Streamlit application with interactive GIS map & charts |
| App Helper / Utils | `app/utils.py` | ⏳ Pending | GeoJSON loading & layer rendering utilities |

### Inputs for Person 4

Person 4 joins `outputs/polygons/change_results.geojson` with `outputs/predictions/predictions.csv` on `id`:

```python
import geopandas as gpd
import pandas as pd

# Load polygons and predictions
gdf = gpd.read_file("outputs/polygons/change_results.geojson")
preds = pd.read_csv("outputs/predictions/predictions.csv")

# Join attributes
dashboard_gdf = gdf.merge(preds[["id", "predicted_class", "predicted_label", "confidence"]], on="id")
```

>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
---

## 6. End-to-End Execution Sequence (No Clashes)

<<<<<<< HEAD
| Convention | Rule |
|---|---|
| Paths | Always use `pathlib.Path`, project-relative from root |
| CRS | Never hardcode EPSG; inherit from input data |
| NoData | NaN for float rasters, 0 for uint8 mask |
| Band order | Always document band order in comments |
| Logging | Use `print("[step/total] message")` prefix in pipeline steps |
| Error handling | Raise descriptive errors; never silently continue on missing data |
| Secrets | Never hardcode credentials; use `.env` file (never commit it) |
=======
```
Step 1: Person 1 executes:
        python run_pipeline.py
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

Step 2: Person 2 executes:
        python run_vectorize.py

Step 3: Person 3 executes:
        python run_classify.py

<<<<<<< HEAD
During the hackathon:
- Share intermediate files via USB / shared network folder / Google Drive
- **Confirm Person 1 outputs exist before Person 2 starts** — run verification:
  ```bash
  python -c "
  import os
  for f in ['outputs/maps/change_mask.tif','outputs/maps/change_magnitude.tif','data/processed/spectral_delta.tif']:
      print('OK' if os.path.exists(f) else 'MISSING', f)
  "
  ```
- Update `PERSON1_PIPELINE.md` and `PERSON2_PIPELINE.md` progress trackers as you go
- Check in at each phase completion

---

## 6. Timeline (24-Hour Window)

| Hour | Person 1 | Person 2 |
|---|---|---|
| 0–2 | Setup + data download | Setup + review plan |
| 2–5 | `loader.py` + `align.py` | Study vectorization plan |
| 5–8 | `masking.py` + `compute.py` | Implement `polygonize.py` |
| 8–10 | `threshold.py` + `run_pipeline.py` | Implement feature extraction |
| 10–13 | Verify + fix bugs | Build ML classifier |
| 13–16 | Verify outputs with Person 2 | Build Streamlit dashboard skeleton |
| 16–20 | Support Person 2 integration | Integrate map + predictions |
| 20–22 | Update docs | Update docs |
| 22–24 | Rehearse demo | Rehearse demo |
=======
Step 4: Person 4 launches dashboard:
        streamlit run app/main.py
```
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
