# 03 — DATA DESIGN

> **Project:** CIPHER-X  
> **Note:** This project has no traditional relational database. All data is file-based (raster, vector, tabular).  
> **Last Updated:** 2026-08-20 (Unified 4-Person Architecture)

---

## 1. Overview

CIPHER-X uses a **file-based data model** instead of a database. All intermediate and final data are stored as GeoTIFF rasters, GeoJSON vector files, CSV tabular datasets, and serialized model binaries on the local filesystem.

---

## 2. Input Data Specification

### 2.1 Sentinel-2 L2A Band Files

**Location:** `data/sentinel/before/` and `data/sentinel/after/`

| Field | Value |
|---|---|
| Source | ESA Copernicus Sentinel-2 L2A |
| Format | .jp2 (JPEG2000) or .tif (GeoTIFF) |
| Projection | UTM (tile-dependent, e.g. EPSG:32643) |
| Resolution | 10m (B02/B03/B04/B08), 20m (SCL) |
| Data type | uint16 (DN), range 0-10000 for reflectance |
| No-data value | 0 |

**Bands used:**

| Band ID | Name | Wavelength | Resolution |
|---|---|---|---|
| B02 | Blue | 490 nm | 10m |
| B03 | Green | 560 nm | 10m |
| B04 | Red | 665 nm | 10m |
| B08 | NIR | 842 nm | 10m |
| SCL | Scene Classification | - | 20m |

**SCL Class Reference:**

| Value | Class |
|---|---|
| 0 | No data |
| 1 | Saturated / Defective |
| 2 | Dark Area Pixels |
| 3 | Cloud Shadows |
| 4 | Vegetation |
| 5 | Bare Soils |
| 6 | Water |
| 7 | Unclassified |
| 8 | Cloud Medium Probability |
| 9 | Cloud High Probability |
| 10 | Thin Cirrus |
| 11 | Snow or Ice |

### 2.2 Area of Interest (AOI)

**Location:** `data/aoi/aoi.geojson` (optional)

| Field | Value |
|---|---|
| Format | GeoJSON |
| CRS | EPSG:4326 (WGS84 lat/lon) |
| Geometry | Single Polygon or MultiPolygon |
| Usage | Optional clip boundary for large scenes |

---

## 3. Intermediate Data (data/processed/ & data/labels/)

### 3.1 spectral_delta.tif (Person 1 -> Person 2)

| Property | Value |
|---|---|
| Path | `data/processed/spectral_delta.tif` |
| Format | GeoTIFF |
| Bands | 4 |
| Band order | Band 1=dB02, Band 2=dB03, Band 3=dB04, Band 4=dB08 |
| Dtype | float32 |
| Range | ~-1.0 to +1.0 (reflectance difference) |
| NoData | NaN (cloud-masked pixels) |
| CRS | Matches input Sentinel-2 CRS |
| Producer | Person 1 - compute.py |

### 3.2 prototype_labels.csv (Person 3 Training Dataset)

| Property | Value |
|---|---|
| Path | `data/labels/prototype_labels.csv` |
| Format | CSV |
| Rows | Labelled change polygons |
| Columns | 16 feature columns + `label` (int 0-4), `label_name` (str), `label_source` (str: 'auto_rule'/'manual') |
| Producer | Person 3 - labeller.py |

---

## 4. Output Data Specification

### 4.1 change_magnitude.tif (Person 1)

| Property | Value |
|---|---|
| Path | `outputs/maps/change_magnitude.tif` |
| Format | GeoTIFF |
| Bands | 1 |
| Dtype | float32 |
| Range | 0.0 to ~1.4 (magnitude of reflectance change) |
| NoData | NaN |
| CRS | Matches input Sentinel-2 CRS |
| Producer | Person 1 - compute.py |

### 4.2 change_mask.tif (Person 1)

| Property | Value |
|---|---|
| Path | `outputs/maps/change_mask.tif` |
| Format | GeoTIFF |
| Bands | 1 |
| Dtype | uint8 |
| Values | 0 = no change, 1 = change |
| NoData | 0 (masked pixels treated as no-change) |
| CRS | Matches input Sentinel-2 CRS |
| Producer | Person 1 - threshold.py |

### 4.3 change_results.geojson (Person 2)

| Property | Value |
|---|---|
| Path | `outputs/polygons/change_results.geojson` |
| Format | GeoJSON |
| CRS | EPSG:4326 (WGS84 - required by GeoJSON spec) |
| Geometry | Polygon / MultiPolygon |
| Producer | Person 2 - polygonize.py + extractor.py |

**Attributes (all polygons):**

| Attribute | Type | Description |
|---|---|---|
| id | int | Unique sequential polygon identifier |
| area_m2 | float | Polygon area in square metres (from native UTM CRS) |
| latitude | float | Centroid latitude in WGS84 |
| longitude | float | Centroid longitude in WGS84 |
| cva_mean | float | Mean CVA magnitude inside polygon |
| cva_max | float | Max CVA magnitude inside polygon |
| ndvi_before | float | Mean NDVI before event (NaN if bands missing) |
| ndvi_after | float | Mean NDVI after event (NaN if bands missing) |
| delta_ndvi | float | ndvi_after minus ndvi_before |
| delta_b02 | float | Mean delta Blue (B02) inside polygon |
| delta_b03 | float | Mean delta Green (B03) inside polygon |
| delta_b04 | float | Mean delta Red (B04) inside polygon |
| delta_b08 | float | Mean delta NIR (B08) inside polygon |
| bbox_width_m | float | Bounding box width in metres |
| bbox_height_m | float | Bounding box height in metres |
| compactness | float | 4*pi*area/perimeter^2 (0 to 1; 1 = perfect circle) |

### 4.4 change_features.csv (Person 2 -> Person 3 Handoff)

| Property | Value |
|---|---|
| Path | `outputs/predictions/change_features.csv` |
| Format | CSV |
| Rows | One row per change polygon |
| Columns | 16 (same attributes as change_results.geojson, without geometry) |
| Consumer | Person 3 - ML classification |

### 4.5 predictions.csv (Person 3 -> Person 4 Handoff)

| Property | Value |
|---|---|
| Path | `outputs/predictions/predictions.csv` |
| Format | CSV |
| Rows | One row per change polygon |
| Columns | `id`, `predicted_class` (0-4), `predicted_label` (str), `confidence` (float 0.0-1.0), plus pass-through features (`area_m2`, `latitude`, `longitude`, `cva_mean`, `delta_ndvi`, etc.) |
| Consumer | Person 4 - Streamlit Dashboard |

### 4.6 Trained Model Binaries (Person 3)

| File | Type | Description |
|---|---|---|
| `models/rf_classifier.joblib` | Binary (joblib) | Trained RandomForestClassifier |
| `models/rf_imputer.joblib` | Binary (joblib) | Fitted SimpleImputer for median NaN handling |
| `models/rf_metadata.json` | JSON | Feature names, class mapping, timestamp, sample counts |

### 4.7 Integrated Dashboard Data Model (Person 4)

In-memory merged GeoDataFrame joining `change_results.geojson` and `predictions.csv` on `id`:

| Property | Description |
|---|---|
| Spatial Layer | GeoJSON polygon geometry in EPSG:4326 for Folium/Leaflet rendering |
| Classification | `predicted_label`, `predicted_class`, `confidence` |
| Analytics | `area_m2`, `area_ha`, `cva_mean`, `cva_max`, `delta_ndvi`, $\Delta$ spectral bands |
| Fallback Layer | Dynamically synthesized bounding polygons if `change_results.geojson` is missing |

---

## 5. End-to-End Data Flow Summary

```
Raw S2 Bands (.jp2/.tif)
        │
        ▼ (Person 1)
loader.py ──▶ align.py ──▶ masking.py ──▶ compute.py
                                               │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
     outputs/maps/change_magnitude.tif                  data/processed/spectral_delta.tif
                    │
                    ▼ (Person 1)
               threshold.py ──▶ outputs/maps/change_mask.tif
                                               │
                                               ▼ (Person 2)
                                          polygonize.py
                                               │
                                               ▼
                                  outputs/polygons/change_results.geojson
                                               │
                                               ▼ (Person 2)
                                     extractor.py + ndvi.py
                                               │
                                               ▼
                                  outputs/predictions/change_features.csv
                                               │
                                               ▼ (Person 3)
                                  labeller.py ──▶ data/labels/prototype_labels.csv
                                               │
                                               ▼ (Person 3)
                                 classifier.py ──▶ models/rf_classifier.joblib
                                               │
                                               ▼ (Person 3)
                                run_classify.py ──▶ outputs/predictions/predictions.csv
                                                            │
                                                            ▼ (Person 4)
                                                   app/main.py (Streamlit)
```

---

## 6. File Naming Convention

```
<descriptor>_<date_optional>.<ext>

Examples:
  change_magnitude.tif          <- Person 1
  change_mask.tif               <- Person 1
  spectral_delta.tif            <- Person 1
  change_results.geojson        <- Person 2
  change_features.csv           <- Person 2
  prototype_labels.csv          <- Person 3
  predictions.csv               <- Person 3
  rf_classifier.joblib          <- Person 3
```
