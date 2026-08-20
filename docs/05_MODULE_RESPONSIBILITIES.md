# 05 — MODULE RESPONSIBILITIES

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Team Structure

| Person | Role | Focus Area |
|---|---|---|
| Person 1 | Satellite Data Engineer | Preprocessing + CVA |
| Person 2 | GIS & Feature Engineer | Vectorization + Feature Extraction + ML Handoff |
| Person 3 | ML Engineer | Classification model (uses Person 2 outputs) |

---

## 2. Person 1 — Sentinel-2 Preprocessing & CVA

### Owned Modules

| Module | File | Status |
|---|---|---|
<<<<<<< HEAD
| Band Loader | `src/preprocessing/loader.py` | Pending |
| Image Alignment | `src/preprocessing/align.py` | Pending |
| Cloud Masking | `src/preprocessing/masking.py` | Pending |
| CVA Computation | `src/cva/compute.py` | Pending |
| Thresholding | `src/cva/threshold.py` | Pending |
| Pipeline Runner | `run_pipeline.py` | Pending |
=======
| Band Loader | `src/preprocessing/loader.py` | ✅ Done | find_band_file, load_bands |
| Image Alignment | `src/preprocessing/align.py` | ✅ Done | align_to_reference, align_images |
| Cloud Masking | `src/preprocessing/masking.py` | ✅ Done | scl_to_mask, combine_masks, apply_mask |
| CVA Computation | `src/cva/compute.py` | ✅ Done | compute_delta, compute_magnitude, save_raster |
| Thresholding | `src/cva/threshold.py` | ✅ Done | otsu_threshold, apply_threshold, clean_mask, save_change_mask |
| Pipeline Runner | `run_pipeline.py` | ✅ Done | CLI with --before/--after args |
>>>>>>> dc0c2e197200a48fe04f4aa26094afe39dca638a

### Deliverables to Person 2

| File | Description |
|---|---|
| `outputs/maps/change_mask.tif` | Binary change mask (uint8, 0/1) |
| `outputs/maps/change_magnitude.tif` | Continuous magnitude (float32) |
| `data/processed/spectral_delta.tif` | 4-band spectral delta (float32) |

### Guaranteed Interface

- All outputs share the same CRS and transform as the input Sentinel-2 data.
- Cloud-masked pixels are NaN in float rasters and 0 in the mask raster.
- Band order in `spectral_delta.tif`: [dB02, dB03, dB04, dB08].
- Pipeline is triggered by: `python run_pipeline.py`

### NOT in Person 1's scope

- Vectorization of change mask to polygons
- Feature extraction from polygons
- ML classification
- Streamlit dashboard
- GeoJSON output

---

## 3. Person 2 — Vectorization & Feature Extraction

### Owned Modules

| Module | File | Status |
|---|---|---|
| Change Mask Vectorization | `src/vectorization/polygonize.py` | Pending |
| NDVI Calculator | `src/features/ndvi.py` | Pending |
| Feature Extractor | `src/features/extractor.py` | Pending |
| Person 2 Runner | `run_vectorize.py` | Pending |

### Inputs from Person 1

Person 2 reads these files (guaranteed to exist after Person 1's pipeline runs):

| File | How to use |
|---|---|
| `outputs/maps/change_mask.tif` | Vectorize with `rasterio.features.shapes()` |
| `outputs/maps/change_magnitude.tif` | Sample per-polygon: `cva_mean`, `cva_max` |
| `data/processed/spectral_delta.tif` | Sample per-polygon: `delta_b02`, `delta_b03`, `delta_b04`, `delta_b08` |
| `data/sentinel/before/` | Read B04 + B08 for NDVI before |
| `data/sentinel/after/` | Read B04 + B08 for NDVI after |

### Implementation Plan (PERSON2_PIPELINE.md)

Full phased implementation plan is documented in `PERSON2_PIPELINE.md` at the project root.

Summary of phases:

| Phase | Module | Goal |
|---|---|---|
| 0 | requirements.txt + inits | Add scikit-image, scipy, shapely; create __init__.py files |
| 1 | polygonize.py | Mask noise removal → connected regions → polygons → lat/lon |
| 2a | ndvi.py | Compute NDVI before and after with safe NaN handling |
| 2b | extractor.py | Sample all raster layers per polygon; compute 16 features |
| 3 | run_vectorize.py | Single-command pipeline runner |
| 4 | Verification | GeoJSON valid, CSV correct, opens in QGIS |

### Deliverables

| File | Description | Consumer |
|---|---|---|
| `outputs/polygons/change_results.geojson` | Change polygons with 16 feature attributes | QGIS, Person 3 |
| `outputs/predictions/change_features.csv` | Flat feature table (16 columns) | Person 3 - ML |

### Feature Columns (both outputs)

| Column | Type | Description |
|---|---|---|
| id | int | Unique polygon identifier |
| area_m2 | float | Polygon area in square metres |
| latitude | float | Centroid latitude (WGS84) |
| longitude | float | Centroid longitude (WGS84) |
| cva_mean | float | Mean CVA magnitude inside polygon |
| cva_max | float | Max CVA magnitude inside polygon |
| ndvi_before | float | Mean NDVI before event |
| ndvi_after | float | Mean NDVI after event |
| delta_ndvi | float | ndvi_after minus ndvi_before |
| delta_b02 | float | Mean delta Blue inside polygon |
| delta_b03 | float | Mean delta Green inside polygon |
| delta_b04 | float | Mean delta Red inside polygon |
| delta_b08 | float | Mean delta NIR inside polygon |
| bbox_width_m | float | Bounding box width in metres |
| bbox_height_m | float | Bounding box height in metres |
| compactness | float | Shape compactness (0 to 1; 1 = circle) |

### How Person 3 Reads Person 2 Output

```python
import pandas as pd

df = pd.read_csv("outputs/predictions/change_features.csv")

feature_cols = [
    "area_m2", "cva_mean", "cva_max",
    "ndvi_before", "ndvi_after", "delta_ndvi",
    "delta_b02", "delta_b03", "delta_b04", "delta_b08",
    "bbox_width_m", "bbox_height_m", "compactness"
]
X = df[feature_cols].values
# id, latitude, longitude available as metadata
```

### NOT in Person 2's scope (per 24-hour MVP plan)

- ML classification model (Person 3)
- Streamlit dashboard (out of scope per prompt)

---

## 4. Shared Conventions

| Convention | Rule |
|---|---|
| Paths | Always use `pathlib.Path`, project-relative from root |
| CRS | Never hardcode EPSG; inherit from input data |
| NoData | NaN for float rasters, 0 for uint8 mask |
| Band order | Always document band order in comments |
| Logging | Use `print` with `[step/total]` prefix for pipeline steps |
| Error handling | Raise descriptive errors; never silently continue on data missing |
| GeoJSON CRS | Always save GeoJSON in EPSG:4326 (GeoJSON spec requirement) |
| Area calculation | Always compute area in native UTM before reprojecting to WGS84 |

---

## 5. Communication Protocol

During the hackathon:
- Person 1 signals completion by: running `python run_pipeline.py` and confirming outputs exist
- Person 2 checks: `outputs/maps/change_mask.tif` and `outputs/maps/change_magnitude.tif` exist before starting
- Person 2 signals completion by: running `python run_vectorize.py` and confirming outputs exist
- Person 3 checks: `outputs/predictions/change_features.csv` exists before starting ML
- Use `PERSON1_PIPELINE.md` and `PERSON2_PIPELINE.md` progress trackers for status

---

## 6. Timeline (24-Hour Window)

| Hour | Person 1 | Person 2 | Person 3 |
|---|---|---|---|
| 0-2 | Setup + data download | Setup + read this doc | Setup |
| 2-5 | loader.py + align.py | Plan + Phase 0 | Plan ML approach |
| 5-8 | masking.py + compute.py | Phase 1: polygonize.py | Wait for P2 outputs |
| 8-10 | threshold.py + run_pipeline.py | Phase 2: ndvi.py + extractor.py | - |
| 10-13 | Verify outputs | Phase 3: run_vectorize.py | Start ML on partial data |
| 13-16 | Verify + fix bugs | Phase 4: Verify GeoJSON/CSV | ML classification |
| 16-20 | Support P2 integration | Handoff to Person 3 | Finalize model |
| 20-22 | Documentation | Update this doc | Documentation |
| 22-24 | Rehearse demo | Rehearse demo | Rehearse demo |
