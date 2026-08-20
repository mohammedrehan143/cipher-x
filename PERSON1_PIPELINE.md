# CIPHER-X — PERSON 1: Sentinel-2 Preprocessing & CVA Pipeline

> **Owner:** Person 1  
> **Scope:** Sentinel-2 data ingestion → Preprocessing → CVA → Change Magnitude → Binary Change Mask  
> **NOT in scope:** ML classification, Streamlit dashboard, vectorization  
> **Last updated:** 2026-08-20  
> **Status:** ✅ All phases implemented

---

## 📋 Repository Audit (as of 2026-08-20)

### What already existed before this session

| Path | Type | Notes |
|---|---|---|
| `src/__init__.py` | File | Empty init |
| `src/preprocessing/__init__.py` | File | Empty init |
| `src/preprocessing/README.md` | File | Stub only |
| `src/cva/__init__.py` | File | Empty init |
| `src/cva/README.md` | File | Stub only |
| `data/README.md` | File | Generic description |
| `outputs/.gitkeep` | File | Placeholder |
| `requirements.txt` | File | numpy, pandas, scikit-learn, matplotlib, opencv-python, rasterio, geopandas, streamlit |
| `app/README.md` | File | Stub |
| `app/__init__.py` | File | Empty |

### Folders created in this session

| Path | Purpose |
|---|---|
| `data/sentinel/before/` | Drop BEFORE S2 band files here |
| `data/sentinel/after/` | Drop AFTER S2 band files here |
| `data/aoi/` | Optional AOI GeoJSON |
| `data/processed/` | Intermediate aligned/masked rasters |
| `outputs/maps/` | Final change_magnitude.tif + change_mask.tif |
| `outputs/polygons/` | For Person 2 |
| `outputs/predictions/` | For Person 2/3 |

### Files CREATED in implementation phases

| Path | Purpose | Phase |
|---|---|---|
| `src/preprocessing/loader.py` | Read S2 bands from folder | Phase 1 |
| `src/preprocessing/align.py` | CRS/grid alignment | Phase 2 |
| `src/preprocessing/masking.py` | SCL cloud/shadow masking | Phase 3 |
| `src/cva/compute.py` | CVA delta + magnitude | Phase 4 |
| `src/cva/threshold.py` | Otsu thresholding + morphological cleanup | Phase 5 |
| `run_pipeline.py` | Top-level pipeline runner | Phase 6 |

### Files UPDATED

| Path | Change | Phase |
|---|---|---|
| `requirements.txt` | Added: scikit-image, scipy | Phase 0 |
| `src/__init__.py` | Added package docstring | Phase 7 |
| `src/preprocessing/__init__.py` | Added exports for all public functions | Phase 7 |
| `src/cva/__init__.py` | Added exports for all public functions | Phase 7 |

---

## 🗂️ Final File Layout After Implementation

```
cipher-x/
├── src/
│   ├── __init__.py                  ✅ Updated
│   ├── preprocessing/
│   │   ├── __init__.py              ✅ Updated (exports)
│   │   ├── loader.py                ✅ Phase 1 — read S2 bands
│   │   ├── align.py                 ✅ Phase 2 — align before/after
│   │   └── masking.py               ✅ Phase 3 — SCL cloud mask
│   │   └── README.md                ✅ Updated
│   └── cva/
│       ├── __init__.py              ✅ Updated (exports)
│       ├── compute.py               ✅ Phase 4 — CVA delta + magnitude
│       ├── threshold.py             ✅ Phase 5 — Otsu + morphological cleanup
│       └── README.md                ✅ Updated
├── data/
│   ├── sentinel/
│   │   ├── before/                  ✅ Created
│   │   └── after/                   ✅ Created
│   ├── aoi/                         ✅ Created
│   └── processed/                   ✅ Created
├── outputs/
│   ├── maps/                        ✅ Created
│   ├── polygons/                    ✅ Created
│   └── predictions/                 ✅ Created
├── run_pipeline.py                  ✅ Phase 6 — orchestrator
└── requirements.txt                 ✅ Phase 0 — updated
```

---

## 📦 Data Input Convention

### Expected file naming

Sentinel-2 L2A band files inside `data/sentinel/before/` and `data/sentinel/after/`:

| Band | Filename pattern | Resolution |
|---|---|---|
| B02 (Blue) | `*B02*.jp2` or `*B02*.tif` | 10m |
| B03 (Green) | `*B03*.jp2` or `*B03*.tif` | 10m |
| B04 (Red) | `*B04*.jp2` or `*B04*.tif` | 10m |
| B08 (NIR) | `*B08*.jp2` or `*B08*.tif` | 10m |
| SCL | `*SCL*.jp2` or `*SCL*.tif` | 20m (resampled to 10m) |

Glob patterns match standard ESA Sentinel-2 SAFE product naming automatically.

### How to get Sentinel-2 data (free)

1. **Copernicus Browser**: https://browser.dataspace.copernicus.eu/
   - Register free → search your AOI → download L2A product
   - Pick two dates: one BEFORE event, one AFTER event
   - Same tile code (e.g., T43PFP) strongly recommended for MVP
2. **Google Earth Engine** (if access available): export B02/B03/B04/B08/SCL as GeoTIFF
3. **Sentinel Hub EO Browser**: https://apps.sentinel-hub.com/eo-browser/

---

## 🔄 Implementation Phases — All Complete

---

### PHASE 0 — Environment & Folder Setup ✅

**Goal:** Confirm all Python deps install cleanly; confirm folders exist.

**Tasks completed:**
- [x] Updated `requirements.txt`: added `scikit-image`, `scipy`
- [x] Created all data/ and outputs/ directories
- [x] Verified folder structure

**requirements.txt now contains:**
```
numpy, pandas, scikit-learn, scikit-image, scipy, matplotlib, opencv-python, rasterio, geopandas, streamlit
```

---

### PHASE 1 — Band Loader (`src/preprocessing/loader.py`) ✅

**Goal:** Read a Sentinel-2 folder and return numpy arrays ready for processing.

**Functions implemented:**

```python
find_band_file(folder: Path, band_name: str) -> Path
    # Globs for *B02*.jp2, *B02*.tif, *B02*.tiff in folder
    # Returns path; raises FileNotFoundError if missing

load_bands(folder: Path) -> tuple[np.ndarray, np.ndarray, dict]
    # Returns:
    #   bands  — shape (4, H, W), float32, range [0.0, 1.0]
    #             band order: [B02, B03, B04, B08]
    #   scl    — shape (H, W), uint8, SCL class values
    #             resampled to match band resolution
    #   profile — rasterio profile dict for saving outputs
```

**Reflectance scaling:**
- S2 L2A stores DN as integer (0–10000)
- Divide by 10000 to get surface reflectance [0.0–1.0]
- SCL is NOT divided (class values 0–11)

**Inputs:** `data/sentinel/before/` or `data/sentinel/after/`  
**Outputs:** numpy arrays + rasterio profile dict

---

### PHASE 2 — Image Alignment (`src/preprocessing/align.py`) ✅

**Goal:** Ensure BEFORE and AFTER arrays are on the exact same grid.

**Why needed:** Even same-tile images can have CRS variations or bounding-box differences across dates. CVA requires pixel-perfect overlap.

**Functions implemented:**

```python
align_to_reference(
    src_array: np.ndarray,        # (bands, H, W)
    src_profile: dict,
    ref_profile: dict,
    resampling: str = 'bilinear'  # 'nearest' for SCL
) -> np.ndarray
    # Reprojects src_array to match ref_profile's CRS + transform + shape

align_images(
    before_bands, before_scl, before_profile,
    after_bands,  after_scl,  after_profile
) -> tuple[np.ndarray, np.ndarray]
    # Returns (aligned_after_bands, aligned_after_scl)
    # BEFORE is used as reference grid
    # Skips reprojection if already aligned
```

**Resampling:**
- Bands → bilinear (smooth continuous values)
- SCL → nearest neighbour (preserve class integer values)

**Inputs:** numpy arrays + rasterio profile dicts  
**Outputs:** aligned AFTER arrays matching BEFORE grid exactly

---

### PHASE 3 — Cloud/Shadow Masking (`src/preprocessing/masking.py`) ✅

**Goal:** Build a validity mask from SCL — invalid pixels excluded from CVA.

**SCL classes masked as invalid:**

| SCL Value | Class |
|---|---|
| 0 | No data |
| 1 | Saturated / defective |
| 3 | Cloud shadow |
| 8 | Cloud medium probability |
| 9 | Cloud high probability |
| 10 | Thin cirrus |

(Snow/ice SCL=11 kept as valid for general use; easily toggled)

**Functions implemented:**

```python
scl_to_mask(scl_array: np.ndarray,
            mask_classes: list = [0,1,3,8,9,10]) -> np.ndarray
    # Returns bool array: True = VALID pixel, False = masked

combine_masks(before_mask, after_mask) -> np.ndarray
    # True only where BOTH images are valid (logical AND)

apply_mask(bands_array: np.ndarray, valid_mask: np.ndarray) -> np.ndarray
    # Returns bands with NaN where valid_mask is False
```

**Fallback:** If SCL file not found → log a warning and treat all pixels as valid.

**Inputs:** SCL numpy arrays  
**Outputs:** boolean validity mask, NaN-masked band arrays

---

### PHASE 4 — CVA Computation (`src/cva/compute.py`) ✅

**Goal:** Compute per-pixel spectral delta and change magnitude.

**Formulas:**

```
delta[b] = after_bands[b] - before_bands[b]   for b in [B02, B03, B04, B08]

M = sqrt( delta_B02² + delta_B03² + delta_B04² + delta_B08² )
```

**Functions implemented:**

```python
compute_delta(before_bands, after_bands, valid_mask) -> np.ndarray
    # Returns shape (4, H, W), NaN where invalid

compute_magnitude(delta_array) -> np.ndarray
    # Returns shape (H, W), NaN where invalid

save_raster(array, profile, output_path)
    # Writes GeoTIFF with correct CRS + transform
    # Handles both 2D (H,W) and 3D (bands,H,W) arrays
    # Sets nodata=NaN for float, nodata=0 for int
```

**Outputs:**
- `data/processed/spectral_delta.tif` — 4-band delta (for Person 2)
- `outputs/maps/change_magnitude.tif` — 1-band magnitude

**Band order in spectral_delta.tif:**
- Band 1 = ΔB02 (Blue delta)
- Band 2 = ΔB03 (Green delta)
- Band 3 = ΔB04 (Red delta)
- Band 4 = ΔB08 (NIR delta)

---

### PHASE 5 — Thresholding & Change Mask (`src/cva/threshold.py`) ✅

**Goal:** Convert continuous magnitude to a clean binary change mask.

**Steps:**
1. Extract valid (non-NaN) magnitude pixels
2. Run `skimage.filters.threshold_otsu` on valid pixels → threshold value
3. Apply threshold → binary array (1=changed, 0=no change)
4. Morphological opening (3×3): removes small isolated "salt" noise
5. Morphological closing (3×3): fills small holes inside change regions
6. Set masked pixels (NaN in magnitude) to 0 in output

**Functions implemented:**

```python
otsu_threshold(magnitude_array) -> float
    # threshold = skimage.filters.threshold_otsu(valid_pixels)

apply_threshold(magnitude_array, threshold) -> np.ndarray
    # bool array: True where magnitude > threshold AND valid

clean_mask(binary_mask, open_size=3, close_size=3) -> np.ndarray
    # scipy.ndimage morphological open then close
    # Returns uint8 array

save_change_mask(mask, profile, output_path)
    # Writes uint8 GeoTIFF: 0=no change, 1=change
```

**Output:** `outputs/maps/change_mask.tif`

---

### PHASE 6 — Pipeline Runner (`run_pipeline.py`) ✅

**Goal:** Single script to execute the entire pipeline end-to-end.

**Usage:**
```bash
python run_pipeline.py
# or with custom paths:
python run_pipeline.py --before data/sentinel/before --after data/sentinel/after
```

**Execution flow:**
```
[1/6] Loading BEFORE bands...
[2/6] Loading AFTER bands...
[3/6] Aligning images...
[4/6] Applying cloud masks...
       Valid pixels: XX.X%
[5/6] Computing CVA magnitude...
[6/6] Generating binary change mask...
       Otsu threshold: X.XXXXXX

Done. Outputs written to:
  outputs/maps/change_magnitude.tif
  outputs/maps/change_mask.tif
  data/processed/spectral_delta.tif
Statistics:
  Changed pixels: X / Y (Z%)
  Magnitude: min=.. max=.. mean=..
  Otsu threshold: ..
```

**Safety checks:**
- Exits with error if < 1% valid pixels (all clouds)
- Creates output directories automatically

---

### PHASE 7 — Verification ✅

**Verification script (run after pipeline):**
```bash
python -c "
import rasterio, numpy as np
for f in ['outputs/maps/change_magnitude.tif',
          'outputs/maps/change_mask.tif',
          'data/processed/spectral_delta.tif']:
    with rasterio.open(f) as src:
        d = src.read(1)
        print(f'{f}: shape={src.shape}, crs={src.crs}, min={float(np.nanmin(d)):.4f}, max={float(np.nanmax(d)):.4f}')
"
```

**Checklist:**
- [x] All source files created and documented
- [x] `__init__.py` files updated with proper exports
- [x] READMEs updated for all modules
- [x] `requirements.txt` updated
- [x] All data/ and outputs/ directories created
- [x] `PERSON1_PIPELINE.md` updated with final status

---

## 📤 Handoff to Person 2

Person 2 (feature extraction + ML) consumes these files:

| File | Description | Format | Bands |
|---|---|---|---|
| `outputs/maps/change_mask.tif` | Binary change mask (0/1) | GeoTIFF uint8 | 1 |
| `outputs/maps/change_magnitude.tif` | Continuous magnitude | GeoTIFF float32 | 1 |
| `data/processed/spectral_delta.tif` | 4-band spectral delta | GeoTIFF float32 | 4 [ΔB02,ΔB03,ΔB04,ΔB08] |

**CRS:** Matches input Sentinel-2 CRS (typically EPSG:32643 or similar UTM zone)  
**NoData:** NaN (float rasters) / 0 (mask raster) for cloud-masked pixels

---

## 🛠️ Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| Reflectance scaling | DN ÷ 10000 | S2 L2A stores reflectance as integer ×10000 |
| Alignment method | rasterio.warp.reproject | Handles CRS + grid + extent in one call |
| Cloud masking | SCL band | Included in L2A, no external tool needed |
| CVA bands | B02, B03, B04, B08 | 10m res, covers visible+NIR for land change |
| Thresholding | Otsu | Automatic, no manual tuning, well-established |
| Morphological cleanup | open→close, 3×3 | Removes salt noise + fills holes |
| Output format | GeoTIFF | Universal compatibility with QGIS, rasterio, gdal |
| Path strategy | pathlib, project-relative | Works on any machine, no hardcoded paths |

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|---|---|
| No real S2 data yet | Build and test with synthetic arrays first |
| SCL file absent | Gracefully skip masking with warning |
| BEFORE/AFTER different tiles | Alignment handles it; same tile recommended |
| Memory for large rasters | Clip to AOI before processing if needed |
| All pixels cloud-masked | Detect this case, print clear error, suggest new date |
| BEFORE/AFTER scenes seasonally mismatched | Document clearly — user must pick comparable dates |

---

## 🚦 Progress Tracker

| Phase | Description | Status | Notes |
|---|---|---|---|
| Audit | Repository inspection | ✅ Done | 2026-08-20 |
| Plan | This document | ✅ Done | 2026-08-20 |
| Phase 0 | Environment + folder setup | ✅ Done | requirements.txt updated |
| Phase 1 | loader.py | ✅ Done | find_band_file, load_bands |
| Phase 2 | align.py | ✅ Done | align_to_reference, align_images |
| Phase 3 | masking.py | ✅ Done | scl_to_mask, combine_masks, apply_mask |
| Phase 4 | compute.py | ✅ Done | compute_delta, compute_magnitude, save_raster |
| Phase 5 | threshold.py | ✅ Done | otsu_threshold, apply_threshold, clean_mask, save_change_mask |
| Phase 6 | run_pipeline.py | ✅ Done | CLI with --before/--after args |
| Phase 7 | Verification | ✅ Done | All files, exports, docs updated |

---

## 🔁 Update Log

| Date | Update |
|---|---|
| 2026-08-20 | Repository fully audited. All existing files documented. Missing folders created. Implementation plan written. |
| 2026-08-20 | All 8 phases implemented. All source files created. All __init__.py exports added. All READMEs updated. Pipeline ready to run. |
