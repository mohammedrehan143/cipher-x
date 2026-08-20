# 10 — FINAL REPORT

> **Project:** CIPHER-X  
> **Event:** Smart India Hackathon (SIH) 2026 — Space Tech Track  
> **Team:** [Team Name]  
> **Date:** 2026-08-20  
> **Status:** In Progress (to be completed at submission)

---

## 1. Project Summary

CIPHER-X is an end-to-end satellite change detection system that uses multitemporal Sentinel-2 imagery to identify, classify, and visualize human-related land-use changes. The system ingests raw satellite bands, performs preprocessing and Change Vector Analysis (CVA), extracts GIS features per change polygon, classifies change regions using machine learning, and presents results via an interactive GIS dashboard.

---

## 2. Problem Addressed

Unauthorized land-use changes — illegal construction, deforestation, encroachment, water body degradation — are difficult to monitor at scale. Traditional field surveys are slow and costly. CIPHER-X provides an automated, near-real-time monitoring capability using freely available Sentinel-2 satellite data.

---

## 3. Technical Approach

### 3.1 Pipeline Overview

```
Sentinel-2 L2A (BEFORE + AFTER)
        v
Band extraction + reflectance scaling (Person 1)
        v
Image alignment (CRS/grid normalization) (Person 1)
        v
Cloud/shadow masking (SCL-based) (Person 1)
        v
Change Vector Analysis (CVA) (Person 1)
        v
Otsu thresholding + morphological cleanup (Person 1)
        v
Vectorization: mask -> change polygons (Person 2)
        v
Feature extraction: 16 features per polygon (Person 2)
        v
ML Classification: polygon -> change class (Person 3)
```

### 3.2 Key Technical Decisions

| Decision | Choice | Justification |
|---|---|---|
| Input data | Sentinel-2 L2A | Free, 10m resolution, pre-corrected surface reflectance |
| Change detection | CVA (Change Vector Analysis) | Multi-spectral, direction-aware, computationally efficient |
| Thresholding | Otsu (automatic) | No manual tuning required, globally optimal for bimodal distributions |
| Noise removal | Morphological opening 3x3 (before+after vectorization) | Removes salt pixels without losing genuine small changes |
| Vectorization | rasterio.features.shapes() | Built-in, returns GeoJSON directly, no external tool needed |
| Feature set | 16 features: CVA stats, NDVI delta, spectral deltas, shape features | Covers spectral change, vegetation loss, and spatial context |
| NDVI formula | (B08-B04)/(B08+B04) | Standard vegetation index; NaN-safe division |
| GeoJSON CRS | EPSG:4326 | GeoJSON spec; QGIS-compatible |
| ML handoff | Flat CSV + GeoJSON | Pandas-ready for sklearn; geometry preserved for visualization |
| ML approach | To be filled by Person 3 | - |

---

## 4. Results

> To be filled after pipeline runs on real data.

### 4.1 Change Detection Results (Person 1)

| Metric | Value |
|---|---|
| AOI coverage | - km2 |
| Valid pixels (non-cloud) | -% |
| Changed pixels detected | -% of valid |
| Otsu threshold used | - |
| Processing time (Person 1) | - minutes |

### 4.2 Vectorization & Feature Extraction Results (Person 2)

| Metric | Value |
|---|---|
| Total change polygons | - |
| Total changed area | - m2 (- ha) |
| Polygon area range | - m2 to - m2 |
| Mean CVA magnitude | - |
| Mean delta NDVI | - |
| Features exported | 16 (id, area_m2, lat, lon, cva_mean, cva_max, ndvi_before, ndvi_after, delta_ndvi, delta_b02/b03/b04/b08, bbox_width_m, bbox_height_m, compactness) |
| Processing time (Person 2) | - minutes |

### 4.3 Classification Results (Person 3)

> To be filled by Person 3.

| Class | Polygons detected | Total area |
|---|---|---|
| Construction | - | - m2 |
| Deforestation | - | - m2 |
| Water loss | - | - m2 |
| Agricultural change | - | - m2 |

### 4.4 Output Files

| File | Size | Description | Producer |
|---|---|---|---|
| `outputs/maps/change_magnitude.tif` | - MB | CVA magnitude raster | Person 1 |
| `outputs/maps/change_mask.tif` | - MB | Binary change mask | Person 1 |
| `data/processed/spectral_delta.tif` | - MB | 4-band spectral delta | Person 1 |
| `outputs/polygons/change_results.geojson` | - KB | Change polygons with 16 feature attributes | Person 2 |
| `outputs/predictions/change_features.csv` | - KB | Flat feature table for ML (16 columns) | Person 2 |
| `outputs/predictions/classified.geojson` | - KB | Classified change polygons | Person 3 |

---

## 5. Challenges & Solutions

| Challenge | Solution |
|---|---|
| Sentinel-2 band alignment across dates | Used rasterio.warp.reproject to normalize CRS/grid |
| Cloud contamination | SCL-based masking excludes cloud/shadow pixels |
| Noise in binary change mask | Morphological opening + closing (3x3) applied twice: once in Person 1 threshold.py, once in Person 2 polygonize.py before vectorization |
| Invalid polygon geometries from rasterization | Repair with shapely .buffer(0); filter with .is_valid |
| NDVI division by zero | Safe division: set NaN where B08+B04==0 |
| Feature extraction from large rasters | Per-polygon mask approach with rasterio.features.geometry_mask; avoids loading full raster into memory for each polygon |
| Maintaining CRS consistency across layers | Always inherit CRS from change_mask.tif; never hardcode EPSG |
| [To be filled by Person 3 — ML challenge] | - |

---

## 6. What We Would Improve With More Time

- [ ] Time-series analysis across multiple dates
- [ ] SAR (Sentinel-1) data fusion for cloud-resistant change detection
- [ ] Deep learning segmentation model (U-Net) for change classification
- [ ] Real-time data ingestion via Sentinel Hub API
- [ ] Web deployment of the dashboard (Streamlit Cloud or Docker)
- [ ] Automated accuracy assessment with labelled ground truth
- [ ] Additional features: texture (GLCM), elevation (DEM), distance to roads

---

## 7. Innovation Highlights

1. **Fully automated 2-step pipeline** — `python run_pipeline.py` then `python run_vectorize.py`; raw data to feature-ready GeoJSON
2. **Free data, zero cost** — uses open Copernicus/ESA satellite data
3. **Generalizable** — works for any AOI with available Sentinel-2 coverage
4. **Modular design** — each module independently testable and replaceable
5. **GIS-native outputs** — all outputs compatible with QGIS and standard GIS tools
6. **ML-ready feature table** — 16 features per polygon, directly loadable into sklearn

---

## 8. Team Contributions

| Person | Contribution |
|---|---|
| Person 1 | Sentinel-2 data pipeline, preprocessing (loader, align, masking), CVA (compute, threshold), binary change mask |
| Person 2 | Vectorization (polygonize), NDVI computation, feature extraction (16 features per polygon), GeoJSON + CSV output, ML handoff |
| Person 3 | ML classification model, change category prediction, classified.geojson |

---

## 9. References

1. ESA Sentinel-2 User Guide: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi
2. Copernicus Browser: https://browser.dataspace.copernicus.eu/
3. Change Vector Analysis: Malila, W.A. (1980). Change Vector Analysis: An Approach for Detecting Forest Changes with Landsat.
4. Otsu Thresholding: Otsu, N. (1979). A threshold selection method from gray-level histograms.
5. rasterio documentation: https://rasterio.readthedocs.io/
6. scikit-image documentation: https://scikit-image.org/docs/
7. geopandas documentation: https://geopandas.org/
8. shapely documentation: https://shapely.readthedocs.io/

---

## 10. Repository

GitHub: https://github.com/mohammedrehan143/cipher-x  
Branch: `main`  
Tag: `v1.0-demo`
