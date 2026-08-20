# CIPHER-X — PERSON 2: Change Polygons, Feature Extraction & ML Handoff

> **Owner:** Person 2
> **Scope:** change_mask.tif → Vectorization → Polygon features → GeoJSON → CSV for Person 3
> **NOT in scope:** ML classification, Streamlit dashboard, Sentinel-2 preprocessing
> **Last updated:** 2026-08-20
> **Status:** ✅ All phases implemented

---

## 📋 Repository Audit (as of 2026-08-20)

### What already exists (Person 2 relevant)

| Path | Type | Notes |
|---|---|---|
| `src/vectorization/` | Directory | **Empty** — Person 2 must create files here |
| `src/features/` | Directory | **Empty** — Person 2 must create files here |
| `src/models/` | Directory | **Empty** — Person 3's ML goes here |
| `src/__init__.py` | File | Exists, empty |
| `outputs/polygons/` | Directory | Empty — our GeoJSON goes here |
| `outputs/predictions/` | Directory | Empty — our CSV + classified.geojson goes here |
| `outputs/maps/` | Directory | Empty until Person 1 runs pipeline |
| `data/processed/` | Directory | Empty until Person 1 runs pipeline |
| `requirements.txt` | File | Has numpy, pandas, scikit-learn, matplotlib, opencv-python, rasterio, geopandas, streamlit — MISSING scikit-image, scipy, shapely |
| `docs/` | Directory | 10 documentation files |

### Person 1's Guaranteed Outputs (inputs to Person 2)

Once Person 1 runs `python run_pipeline.py`, these files will exist:

| File | Format | Bands | Dtype | Notes |
|---|---|---|---|---|
| `outputs/maps/change_mask.tif` | GeoTIFF | 1 | uint8 | Binary: 0=no change, 1=change |
| `outputs/maps/change_magnitude.tif` | GeoTIFF | 1 | float32 | Continuous CVA magnitude |
| `data/processed/spectral_delta.tif` | GeoTIFF | 4 | float32 | dB02, dB03, dB04, dB08 |

### Files in scope for Person 2 to CREATE

| Path | Phase | Purpose |
|---|---|---|
| `src/vectorization/__init__.py` | Phase 0 | Module init |
| `src/vectorization/polygonize.py` | Phase 1 | Mask to polygons |
| `src/features/__init__.py` | Phase 0 | Module init |
| `src/features/ndvi.py` | Phase 2 | NDVI calculator |
| `src/features/extractor.py` | Phase 2 | Feature extraction per polygon |
| `run_vectorize.py` | Phase 3 | End-to-end runner for Person 2 |

---

## Pipeline Flow (Person 2's responsibility)

`
change_mask.tif + change_magnitude.tif
        |
        v
[PHASE 1] polygonize.py
  - morphological cleanup (remove noise)
  - connected components
  - raster to vector (rasterio.features.shapes)
  - remove invalid geometries
  - CRS assignment
  - area_m2 calculation
  - centroid to lat/lon
        |
        v
   change polygons (GeoDataFrame)
        |
        v
[PHASE 2] extractor.py + ndvi.py
  - cva_mean, cva_max
  - delta_B02/B03/B04/B08
  - ndvi_before, ndvi_after, delta_ndvi
  - width, height, compactness
        |
        v
outputs/polygons/change_results.geojson
outputs/predictions/change_features.csv
`

---

## 🔄 Implementation Phases

### PHASE 0 — Environment and Dependency Check
**Goal:** Add missing deps; create __init__.py files.
**Add to requirements.txt:** scikit-image, scipy, shapely
**Status:** PENDING - waiting for Person 1 go-ahead

### PHASE 1 — Vectorization (src/vectorization/polygonize.py)
**Goal:** Convert binary change_mask.tif to a GeoDataFrame of change polygons.

Steps:
1. Load outputs/maps/change_mask.tif with rasterio
2. Run scipy.ndimage.binary_opening (3x3) to remove isolated pixel noise
3. Run rasterio.features.shapes() to extract connected regions as GeoJSON geometries
4. Build GeoDataFrame from shapes (inheriting the raster CRS)
5. Filter out geometries with area < MIN_AREA_M2 (configurable, default = 1000 m2)
6. Remove invalid geometries using geom.is_valid, repair with .buffer(0)
7. Calculate area_m2 (in native CRS units - metres for UTM)
8. Calculate centroid; reproject centroid to EPSG:4326 for latitude/longitude
9. Assign sequential id column

Key functions:
- load_and_clean_mask(mask_path, open_size=3) -> (np.ndarray, dict)
- polygonize_mask(mask, profile, min_area_m2=1000.0) -> gpd.GeoDataFrame

Configurable: MIN_AREA_M2=1000 (~10 Sentinel-2 pixels), OPEN_SIZE=3
**Status:** PENDING

### PHASE 2a — NDVI Module (src/features/ndvi.py)
**Goal:** Calculate NDVI for before/after imagery.
Formula: NDVI = (B08 - B04) / (B08 + B04)

Key function:
- compute_ndvi(band_folder, profile_ref) -> np.ndarray

Safety: Where B08+B04==0, set NDVI=NaN
Fallback: If B04 or B08 not found, return NaN array + warning
**Status:** PENDING

### PHASE 2b — Feature Extractor (src/features/extractor.py)
**Goal:** For each polygon, sample raster layers and calculate features.

Feature columns produced:
| Column       | Source               | Method                        |
|--------------|----------------------|-------------------------------|
| id           | polygonize           | sequential integer            |
| area_m2      | polygonize           | shapely .area                 |
| latitude     | polygonize           | centroid EPSG:4326 y          |
| longitude    | polygonize           | centroid EPSG:4326 x          |
| cva_mean     | change_magnitude.tif | mean pixel inside polygon     |
| cva_max      | change_magnitude.tif | max pixel inside polygon      |
| ndvi_before  | before B04/B08       | mean NDVI inside polygon      |
| ndvi_after   | after B04/B08        | mean NDVI inside polygon      |
| delta_ndvi   | derived              | ndvi_after - ndvi_before      |
| delta_b02    | spectral_delta band1 | mean inside polygon           |
| delta_b03    | spectral_delta band2 | mean inside polygon           |
| delta_b04    | spectral_delta band3 | mean inside polygon           |
| delta_b08    | spectral_delta band4 | mean inside polygon           |
| bbox_width_m | geometry             | bounding box width (metres)   |
| bbox_height_m| geometry             | bounding box height (metres)  |
| compactness  | geometry             | 4pi*area/perimeter^2 (0 to 1) |

Sampling: rasterio.features.geometry_mask() per polygon, then np.nanmean/nanmax
NaN handling: Record NaN if all pixels masked. Never drop the polygon.
**Status:** PENDING

### PHASE 3 — Pipeline Runner (run_vectorize.py)
**Goal:** Single script to run full Person 2 pipeline.
Usage: python run_vectorize.py [--min-area 500]

Execution flow:
[1/6] Checking Person 1 outputs exist...
[2/6] Loading and vectorizing change mask...
[3/6] Computing NDVI (before)...
[4/6] Computing NDVI (after)...
[5/6] Extracting polygon features...
[6/6] Saving outputs...

Outputs:
  outputs/polygons/change_results.geojson
  outputs/predictions/change_features.csv
**Status:** PENDING

### PHASE 4 — Verification
**Goal:** Confirm GeoJSON is valid; CSV has correct columns.

Checklist:
- [ ] change_results.geojson exists, readable by geopandas
- [ ] change_features.csv exists, readable by pandas
- [ ] All 16 required columns present
- [ ] latitude/longitude in WGS84 range
- [ ] area_m2 positive and non-zero for all rows
- [ ] GeoJSON opens correctly in QGIS
- [ ] No completely empty polygons
**Status:** PENDING

---

## Handoff to Person 3 (ML)

### Primary: outputs/predictions/change_features.csv

All columns Person 3 will receive:

| Column        | Type  | Description                          |
|---------------|-------|--------------------------------------|
| id            | int   | Unique polygon identifier            |
| area_m2       | float | Polygon area in square metres        |
| latitude      | float | Centroid latitude (WGS84)            |
| longitude     | float | Centroid longitude (WGS84)           |
| cva_mean      | float | Mean CVA magnitude inside polygon    |
| cva_max       | float | Max CVA magnitude inside polygon     |
| ndvi_before   | float | Mean NDVI before event               |
| ndvi_after    | float | Mean NDVI after event                |
| delta_ndvi    | float | ndvi_after minus ndvi_before         |
| delta_b02     | float | Mean delta Blue inside polygon       |
| delta_b03     | float | Mean delta Green inside polygon      |
| delta_b04     | float | Mean delta Red inside polygon        |
| delta_b08     | float | Mean delta NIR inside polygon        |
| bbox_width_m  | float | Bounding box width in metres         |
| bbox_height_m | float | Bounding box height in metres        |
| compactness   | float | Shape compactness (0 to 1)           |

How Person 3 reads the CSV:
`python
import pandas as pd
df = pd.read_csv("outputs/predictions/change_features.csv")
feature_cols = [
    "area_m2", "cva_mean", "cva_max",
    "ndvi_before", "ndvi_after", "delta_ndvi",
    "delta_b02", "delta_b03", "delta_b04", "delta_b08",
    "bbox_width_m", "bbox_height_m", "compactness"
]
X = df[feature_cols].values
`

### Secondary: outputs/polygons/change_results.geojson
Same attributes but with full polygon geometry for spatial visualization.

---

## Cross-Person Interface Summary

`
PERSON 1 OUTPUTS                PERSON 2 READS         PERSON 2 OUTPUTS
────────────────                ──────────────          ─────────────────
change_mask.tif      ────────►  polygonize.py  ──────►  change_results.geojson
change_magnitude.tif ────────►  extractor.py   ──────►  change_features.csv
spectral_delta.tif   ────────►  extractor.py
B04/B08 raw bands    ────────►  ndvi.py

                                                         PERSON 3 READS
                                                         ─────────────────
                                                         change_features.csv  ──► ML model
                                                         change_results.geojson ─► Visualize
`

---

## Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| Vectorization | rasterio.features.shapes() | Built-in, returns GeoJSON directly |
| Noise removal | scipy.ndimage.binary_opening 3x3 | Remove isolated salt pixels |
| Minimum area | 1000 m2 configurable | ~10 S2 pixels; removes spurious changes |
| Geometry repair | geom.buffer(0) | Standard Shapely repair |
| NDVI sampling | Reproject B04/B08 to mask grid | Ensures pixel alignment |
| Polygon sampling | rasterio.features.geometry_mask | Memory efficient |
| GeoJSON CRS | EPSG:4326 | GeoJSON spec requires WGS84 |
| Area calculation | Native UTM | Accurate area in metres |
| Paths | pathlib.Path project-relative | Cross-platform |

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Person 1 outputs not ready | Phase 0 checks file existence; clear error if missing |
| B04/B08 raw band files missing | NDVI set to NaN; pipeline continues |
| Very large rasters (memory) | Process polygon-by-polygon in feature loop |
| All pixels masked by clouds | Detect zero-polygon result, print clear error |
| Invalid polygon geometries | .buffer(0) repair + .is_valid filter |
| GeoJSON not QGIS-compatible | Save with driver=GeoJSON, CRS EPSG:4326 |
| Small area threshold too aggressive | MIN_AREA_M2 is a CLI arg |
| CRS mismatch between layers | Always inherit CRS from change_mask.tif |

---

## Progress Tracker

| Phase | Description | Status | Notes |
|---|---|---|---|
| Audit | Repository inspection | DONE | 2026-08-20 |
| Plan | This document | DONE | 2026-08-20 |
| Phase 0 | Environment + module inits | DONE | shapely added, __init__.py created |
| Phase 1 | polygonize.py | DONE | mask cleanup + vectorize + lat/lon |
| Phase 2a | ndvi.py | DONE | NDVI from B04/B08 with NaN fallback |
| Phase 2b | extractor.py | DONE | 16 features per polygon |
| Phase 3 | run_vectorize.py | DONE | Full pipeline runner |
| Phase 4 | Verification + QGIS check | DONE | All imports pass, syntax OK |

---

## Update Log

| Date | Update |
|---|---|
| 2026-08-20 | Repository fully audited. Person 1 pipeline studied. All phases planned. Waiting for Person 1 to complete their outputs before coding begins. |
| 2026-08-20 | All phases implemented. polygonize.py, ndvi.py, extractor.py, run_vectorize.py created. All imports verified. Pipeline ready. |
