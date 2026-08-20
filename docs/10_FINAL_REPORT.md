# 10 — FINAL REPORT

> **Project:** CIPHER-X  
> **Event:** Smart India Hackathon (SIH) 2026 — Space Tech Track  
> **Team:** [Team Name]  
> **Date:** 2026-08-20  
> **Status:** 🔄 In Progress (to be completed at submission)

---

## 1. Project Summary

CIPHER-X is an end-to-end satellite change detection system that uses multitemporal Sentinel-2 imagery to identify, classify, and visualize human-related land-use changes. The system ingests raw satellite bands, performs preprocessing and Change Vector Analysis (CVA), classifies change regions using machine learning, and presents results via an interactive Streamlit GIS dashboard.

---

## 2. Problem Addressed

Unauthorized land-use changes — illegal construction, deforestation, encroachment, water body degradation — are difficult to monitor at scale. Traditional field surveys are slow and costly. CIPHER-X provides an automated, near-real-time monitoring capability using freely available Sentinel-2 satellite data.

---

## 3. Technical Approach

### 3.1 Pipeline Overview

```
Sentinel-2 L2A (BEFORE + AFTER)
        ↓
Band extraction + reflectance scaling
        ↓
Image alignment (CRS/grid normalization)
        ↓
Cloud/shadow masking (SCL-based)
        ↓
Change Vector Analysis (CVA)
        ↓
Otsu thresholding + morphological cleanup
        ↓
Vectorization → GeoJSON polygons
        ↓
Feature extraction (spectral, index-based)
        ↓
ML Classification (Random Forest / similar)
        ↓
Streamlit Dashboard (interactive map)
```

### 3.2 Key Technical Decisions

| Decision | Choice | Justification |
|---|---|---|
| Input data | Sentinel-2 L2A | Free, 10m resolution, pre-corrected surface reflectance |
| Change detection | CVA (Change Vector Analysis) | Multi-spectral, direction-aware, computationally efficient |
| Thresholding | Otsu (automatic) | No manual tuning required, globally optimal for bimodal distributions |
| ML approach | [To be filled by Person 2] | — |
| Dashboard | Streamlit | Fast to develop, Python-native, handles spatial data display |

---

## 4. Results

> **To be filled after pipeline runs on real data.**

### 4.1 Change Detection Results

| Metric | Value |
|---|---|
| AOI coverage | — km² |
| Valid pixels (non-cloud) | —% |
| Changed pixels detected | —% of valid |
| Otsu threshold used | — |
| Processing time | — minutes |

### 4.2 Classification Results

> To be filled by Person 2.

| Class | Polygons detected | Total area |
|---|---|---|
| Construction | — | — m² |
| Deforestation | — | — m² |
| Water loss | — | — m² |
| Agricultural change | — | — m² |

### 4.3 Output Files

| File | Size | Description |
|---|---|---|
| `outputs/maps/change_magnitude.tif` | — MB | CVA magnitude raster |
| `outputs/maps/change_mask.tif` | — MB | Binary change mask |
| `data/processed/spectral_delta.tif` | — MB | 4-band spectral delta |
| `outputs/polygons/changes.geojson` | — KB | Change polygons |
| `outputs/predictions/classified.geojson` | — KB | Classified change polygons |

---

## 5. Challenges & Solutions

| Challenge | Solution |
|---|---|
| Sentinel-2 band alignment across dates | Used rasterio.warp.reproject to normalize CRS/grid |
| Cloud contamination | SCL-based masking excludes cloud/shadow pixels |
| Noise in binary change mask | Morphological opening + closing (3×3) |
| [To be filled by Person 2] | — |

---

## 6. What We Would Improve With More Time

- [ ] Time-series analysis across multiple dates
- [ ] SAR (Sentinel-1) data fusion for cloud-resistant change detection
- [ ] Deep learning segmentation model (U-Net) for change classification
- [ ] Real-time data ingestion via Sentinel Hub API
- [ ] Web deployment of the dashboard (Streamlit Cloud or Docker)
- [ ] Automated accuracy assessment with labelled ground truth

---

## 7. Innovation Highlights

1. **Fully automated pipeline** — single command from raw data to interactive map
2. **Free data, zero cost** — uses open Copernicus/ESA satellite data
3. **Generalizable** — works for any AOI with available Sentinel-2 coverage
4. **Modular design** — each module independently testable and replaceable
5. **GIS-native outputs** — all outputs compatible with QGIS and standard GIS tools

---

## 8. Team Contributions

| Person | Contribution |
|---|---|
| Person 1 | Sentinel-2 data pipeline, preprocessing, CVA, change detection | ✅ All modules implemented |
| Person 2 | Vectorization, feature extraction, ML classification, Streamlit dashboard |

---

## 9. References

1. ESA Sentinel-2 User Guide: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi
2. Copernicus Browser: https://browser.dataspace.copernicus.eu/
3. Change Vector Analysis: Malila, W.A. (1980). Change Vector Analysis: An Approach for Detecting Forest Changes with Landsat.
4. Otsu Thresholding: Otsu, N. (1979). A threshold selection method from gray-level histograms.
5. rasterio documentation: https://rasterio.readthedocs.io/
6. scikit-image documentation: https://scikit-image.org/docs/

---

## 10. Repository

GitHub: https://github.com/mohammedrehan143/cipher-x  
Branch: `main`  
Tag: `v1.0-demo`
