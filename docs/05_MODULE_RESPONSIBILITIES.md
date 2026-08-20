# 05 — MODULE RESPONSIBILITIES

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Team Structure

| Person | Role | Focus Area |
|---|---|---|
| **Person 1** | Satellite Data Engineer | Sentinel-2 Ingestion, Preprocessing & CVA |
| **Person 2** | GIS & Feature Engineer | Mask Vectorization, NDVI, Feature Extraction & Table Generation |
| **Person 3** | ML Engineer | Label Creation, Random Forest Classifier & Inference |
| **Person 4** | Frontend & GIS Visualizer | Streamlit Interactive GIS Dashboard & Analytics |

---

## 2. Person 1 — Sentinel-2 Preprocessing & CVA

### Owned Modules

| Module | File | Status | Description |
|---|---|---|---|
| Band Loader | `src/preprocessing/loader.py` | ✅ Done | `find_band_file`, `load_bands` |
| Image Alignment | `src/preprocessing/align.py` | ✅ Done | `align_to_reference`, `align_images` |
| Cloud Masking | `src/preprocessing/masking.py` | ✅ Done | `scl_to_mask`, `combine_masks`, `apply_mask` |
| CVA Computation | `src/cva/compute.py` | ✅ Done | `compute_delta`, `compute_magnitude`, `save_raster` |
| Thresholding | `src/cva/threshold.py` | ✅ Done | `otsu_threshold`, `apply_threshold`, `clean_mask`, `save_change_mask` |
| Pipeline Runner | `run_pipeline.py` | ✅ Done | CLI orchestrator for Person 1 |

### Deliverables to Person 2

| File | Description |
|---|---|
| `outputs/maps/change_mask.tif` | Binary change mask (uint8, 0/1) |
| `outputs/maps/change_magnitude.tif` | Continuous magnitude (float32) |
| `data/processed/spectral_delta.tif` | 4-band spectral delta (float32) |

---

## 3. Person 2 — Vectorization & Feature Extraction

### Owned Modules

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

---

## 6. End-to-End Execution Sequence (No Clashes)

```
Step 1: Person 1 executes:
        python run_pipeline.py

Step 2: Person 2 executes:
        python run_vectorize.py

Step 3: Person 3 executes:
        python run_classify.py

Step 4: Person 4 launches dashboard:
        streamlit run app/main.py
```
