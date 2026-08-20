# 05 — MODULE RESPONSIBILITIES

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Team Structure

| Person | Role | Focus Area |
|---|---|---|
| Person 1 | Satellite Data Engineer | Preprocessing + CVA |
| Person 2 | ML & GIS Engineer | Vectorization + Features + ML + Dashboard |

---

## 2. Person 1 — Sentinel-2 Preprocessing & CVA

### Owned Modules

| Module | File | Status |
|---|---|---|
| Band Loader | `src/preprocessing/loader.py` | ✅ Done | find_band_file, load_bands |
| Image Alignment | `src/preprocessing/align.py` | ✅ Done | align_to_reference, align_images |
| Cloud Masking | `src/preprocessing/masking.py` | ✅ Done | scl_to_mask, combine_masks, apply_mask |
| CVA Computation | `src/cva/compute.py` | ✅ Done | compute_delta, compute_magnitude, save_raster |
| Thresholding | `src/cva/threshold.py` | ✅ Done | otsu_threshold, apply_threshold, clean_mask, save_change_mask |
| Pipeline Runner | `run_pipeline.py` | ✅ Done | CLI with --before/--after args |

### Deliverables to Person 2

| File | Description |
|---|---|
| `outputs/maps/change_mask.tif` | Binary change mask (uint8, 0/1) |
| `outputs/maps/change_magnitude.tif` | Continuous magnitude (float32) |
| `data/processed/spectral_delta.tif` | 4-band spectral delta (float32) |

### Guaranteed Interface

- All outputs share the same CRS and transform as the input Sentinel-2 data.
- Cloud-masked pixels are NaN in float rasters and 0 in the mask raster.
- Band order in `spectral_delta.tif`: [ΔB02, ΔB03, ΔB04, ΔB08].
- Pipeline is triggered by: `python run_pipeline.py`

### NOT in Person 1's scope

- Vectorization of change mask to polygons
- Feature extraction from polygons
- ML classification
- Streamlit dashboard
- GeoJSON output

---

## 3. Person 2 — Vectorization, Features, ML, Dashboard

> **Note:** Person 2's modules are to be filled in by Person 2. Stubs provided here.

### Owned Modules

| Module | File | Status |
|---|---|---|
| Vectorization | `src/vectorization/` | ⏳ TBD |
| Feature Extraction | `src/features/` | ⏳ TBD |
| ML Model | `src/models/` | ⏳ TBD |
| Dashboard | `app/` | ⏳ TBD |

### Inputs from Person 1

Person 2 reads these files (guaranteed to exist after Person 1's pipeline):

| File | How to use |
|---|---|
| `outputs/maps/change_mask.tif` | Read with rasterio; vectorize with rasterio.features.shapes() |
| `outputs/maps/change_magnitude.tif` | Use for polygon attribute (mean magnitude per polygon) |
| `data/processed/spectral_delta.tif` | Use per-band delta as features (4 bands) |

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
    # Band 1 = ΔB02, Band 2 = ΔB03, Band 3 = ΔB04, Band 4 = ΔB08
```

### Deliverables

| File | Description |
|---|---|
| `outputs/polygons/changes.geojson` | Change polygons with attributes |
| `outputs/predictions/classified.geojson` | Classified change polygons |
| `app/main.py` | Streamlit dashboard |

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

---

## 5. Communication Protocol

During the hackathon:
- Share intermediate files via USB / shared network folder / Google Drive if needed
- Confirm Person 1 outputs exist before Person 2 starts (run verification script)
- Check in at each phase completion
- Use `PERSON1_PIPELINE.md` progress tracker to communicate status

---

## 6. Timeline (24-Hour Window)

| Hour | Person 1 | Person 2 |
|---|---|---|
| 0–2 | Setup + data download | Setup + data download |
| 2–5 | loader.py + align.py | Plan vectorization + features |
| 5–8 | masking.py + compute.py | Implement vectorization |
| 8–10 | threshold.py + run_pipeline.py | Feature extraction |
| 10–13 | Verify + fix bugs | ML classifier |
| 13–16 | Verify outputs with Person 2 | Dashboard skeleton |
| 16–20 | Support Person 2 integration | Dashboard + integration |
| 20–22 | Documentation | Documentation |
| 22–24 | Rehearse demo | Rehearse demo |
