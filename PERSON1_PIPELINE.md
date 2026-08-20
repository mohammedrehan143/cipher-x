# CIPHER-X - PERSON 1: Sentinel-2 Preprocessing & CVA Pipeline

> **Owner:** Person 1
> **Scope:** Sentinel-2 data ingestion to Preprocessing to CVA to Change Magnitude to Binary Change Mask
> **NOT in scope:** ML classification, Streamlit dashboard, vectorization
> **Last updated:** 2026-08-20 (all bugs fixed)

---

## Repository Audit (as of 2026-08-20)

### What already existed before this session

| Path | Type | Notes |
|---|---|---|
| src/__init__.py | File | Empty init |
| src/preprocessing/__init__.py | File | Empty init |
| src/preprocessing/README.md | File | Stub only |
| src/cva/__init__.py | File | Empty init |
| src/cva/README.md | File | Stub only |
| data/README.md | File | Generic description |
| outputs/.gitkeep | File | Placeholder |
| requirements.txt | File | numpy, pandas, scikit-learn, matplotlib, opencv-python, rasterio, geopandas, streamlit |

### Folders created in this session

| Path | Purpose |
|---|---|
| data/sentinel/before/ | Drop BEFORE S2 band files here |
| data/sentinel/after/ | Drop AFTER S2 band files here |
| data/aoi/ | Optional AOI GeoJSON |
| data/processed/ | Intermediate aligned/masked rasters |
| outputs/maps/ | Final change_magnitude.tif + change_mask.tif |
| outputs/polygons/ | For Person 2 |
| outputs/predictions/ | For Person 2 |

### Files Created

| Path | Purpose |
|---|---|
| src/preprocessing/loader.py | Read S2 bands from folder |
| src/preprocessing/align.py | CRS/grid alignment (BUG-04 fixed) |
| src/preprocessing/masking.py | SCL cloud/shadow masking |
| src/cva/compute.py | CVA delta + magnitude (BUG-01 fixed) |
| src/cva/threshold.py | Otsu thresholding + morphological cleanup |
| run_pipeline.py | Top-level pipeline runner (BUG-06 fixed) |

### Files Updated

| Path | Change |
|---|---|
| requirements.txt | Added: scikit-image, scipy, shapely, pyproj (BUG-02 fix) |
| .gitignore | Added: .env entries (BUG-03 fix) |

---

## Data Input Convention

Drop Sentinel-2 L2A band files into data/sentinel/before/ and data/sentinel/after/

| Band | Filename pattern | Resolution |
|---|---|---|
| B02 (Blue) | *B02*.jp2 or *B02*.tif | 10m |
| B03 (Green) | *B03*.jp2 or *B03*.tif | 10m |
| B04 (Red) | *B04*.jp2 or *B04*.tif | 10m |
| B08 (NIR) | *B08*.jp2 or *B08*.tif | 10m |
| SCL | *SCL*.jp2 or *SCL*.tif | 20m (resampled) |

---

## Bug Fixes Applied

### BUG-01 Fixed - compute.py line 39
np.nansum returns 0 (not NaN) for all-masked pixels.
Fix: np.all(np.isnan(delta_array), axis=0) used to re-apply NaN after nansum.

### BUG-04 Fixed - align.py lines 83-88
SCL was passed with count=4 profile (reflectance band count).
Fix: dedicated scl_profile with count=1, dtype=uint8 created before reproject call.

### BUG-06 Fixed - run_pipeline.py line 97
No shape assertion before masked array indexing.
Fix: assert clean_change.shape == combined_valid.shape with clear error message.

---

## Expected Outputs

| File | Format | Description |
|---|---|---|
| outputs/maps/change_magnitude.tif | GeoTIFF float32 | CVA magnitude (NaN where cloud-masked) |
| outputs/maps/change_mask.tif | GeoTIFF uint8 | Binary: 0=no change, 1=change |
| data/processed/spectral_delta.tif | GeoTIFF float32 4-band | Band order: dB02, dB03, dB04, dB08 |

---

## How to Run

```
python run_pipeline.py
python run_pipeline.py --before data/sentinel/before --after data/sentinel/after
```

---

## Progress Tracker

| Phase | Description | Status | Notes |
|---|---|---|---|
| Audit | Repository inspection | Done | 2026-08-20 |
| Plan | This document | Done | 2026-08-20 |
| Phase 0 | Environment + folder setup | Done | requirements.txt updated; folders created |
| Phase 1 | loader.py | Done | |
| Phase 2 | align.py | Done | BUG-04 fixed: SCL profile count corrected |
| Phase 3 | masking.py | Done | |
| Phase 4 | compute.py | Done | BUG-01 fixed: NaN propagation corrected |
| Phase 5 | threshold.py | Done | |
| Phase 6 | run_pipeline.py | Done | BUG-06 fixed: shape assertion added |
| Phase 7 | Verification | Pending | Awaiting real Sentinel-2 data |

---

## Update Log

| Date | Update |
|---|---|
| 2026-08-20 T11:36 | Repository audit completed. Plan created. |
| 2026-08-20 T11:46 | All folders created. docs/ written. |
| 2026-08-20 T13:27 | Analysis: 6 bugs found, documented. |
| 2026-08-20 T13:45 | All 6 bugs fixed in code. Docs updated. |
