# 10 — FINAL REPORT

> **Project:** CIPHER-X  
> **Event:** Smart India Hackathon (SIH) 2026 — Space Tech Track  
> **Team:** [Team Name]  
> **Date:** 2026-08-20  
> **Status:** In Progress (to be completed at submission)

---

## 1. Project Summary

CIPHER-X is an end-to-end satellite change detection and intelligence system that uses multitemporal Sentinel-2 imagery to identify, vectorize, classify, and visualize human-related land-use changes. The system ingests raw satellite bands, performs preprocessing and Change Vector Analysis (CVA), extracts GIS attributes per change polygon, classifies change regions into distinct human-activity types using a balanced Random Forest model, and presents findings on an interactive Streamlit GIS dashboard.

---

## 2. Problem Addressed

Unauthorized land-use changes — illegal construction, deforestation, encroachment, mining/excavation — are difficult to monitor across vast geographic regions. Traditional field surveys are slow and expensive. CIPHER-X provides an automated, near-real-time monitoring capability using freely available Sentinel-2 satellite data.

---

## 3. Technical Approach

### 3.1 Pipeline Overview

```
Sentinel-2 L2A (BEFORE + AFTER)
        ↓
[Person 1] Preprocessing: Band extraction, reflectance scaling, cloud/shadow masking, CRS alignment
        ↓
[Person 1] CVA: Spectral difference & L2 magnitude computation, Otsu thresholding & morphological cleanup
        ↓
[Person 2] Vectorization: Raster-to-vector polygonization, invalid geometry repair, WGS84 centroids
        ↓
[Person 2] Feature Extraction: 16 attributes (CVA mean/max, NDVI before/after/delta, spectral deltas, shape metrics)
        ↓
[Person 3] ML Classification: Rule-assisted prototype labelling, median imputation, balanced Random Forest, confidence scoring
        ↓
[Person 4] Visualization: Interactive Streamlit GIS dashboard with polygon overlays, metric filters & analytics
```

### 3.2 Key Technical Decisions

| Area | Decision | Justification |
|---|---|---|
| Input Data | Sentinel-2 L2A | Free, 10m spatial resolution, pre-calibrated surface reflectance |
| Change Detection | Change Vector Analysis (CVA) | Multi-spectral, direction-aware, fast L2 magnitude computation |
| Thresholding | Automatic Otsu Thresholding | Non-parametric, robust on bimodal magnitude histograms |
| Vectorization | `rasterio.features.shapes()` | Direct GeoJSON polygon creation with Shapely geometry repair |
| Features | 16 Spectral & Geometric Attributes | Captures change intensity, vegetation loss, spectral signatures, and compactness |
| ML Classifier | `RandomForestClassifier` | Resilient to small prototype datasets, non-linear feature interactions, fast training, native probability outputs |
| ML Strategy | Supervised with Prototype Labels | Distinct boundary between change discovery (CVA) and change classification (ML) |
| Confidence | Maximum Class Probability | Clear interpretability for end-users and dashboard filtering |
| Frontend | Streamlit + Folium/PyDeck | Rapid Python-native GIS visualizer with zero JavaScript friction |

---

## 4. Results & Deliverables

### 4.1 System Deliverables

| File | Description | Producer | Consumer |
|---|---|---|---|
| `outputs/maps/change_magnitude.tif` | CVA change magnitude raster | Person 1 | Person 2 |
| `outputs/maps/change_mask.tif` | Binary change mask | Person 1 | Person 2 |
| `data/processed/spectral_delta.tif` | 4-band spectral delta raster | Person 1 | Person 2 |
| `outputs/polygons/change_results.geojson` | Change polygons with 16 features | Person 2 | Person 3 & Person 4 |
| `outputs/predictions/change_features.csv` | Feature dataset table | Person 2 | Person 3 |
| `data/labels/prototype_labels.csv` | Training dataset with provisional/verified labels | Person 3 | Person 3 |
| `models/rf_classifier.joblib` | Trained Random Forest model | Person 3 | System |
| `outputs/predictions/predictions.csv` | Class predictions with confidence scores | Person 3 | Person 4 |
| `app/main.py` | Interactive GIS Dashboard | Person 4 | Judges / Users |

---

## 5. Challenges & Solutions

| Challenge | Solution |
|---|---|
| Cross-date CRS & grid mismatch | Reprojected AFTER scene to match BEFORE grid with bilinear interpolation |
| Cloud & shadow false positives | SCL-based mask combined across both dates (logical AND for validity) |
| Rasterization noise | Morphological opening + minimum area threshold filtering |
| Missing ground-truth ML labels | Built rule-based heuristic labeller for prototype training set with manual audit capability |
| Feature missing values (NaNs) | Median imputation pipeline saved and serialized alongside model |
| Extreme class imbalance | Balanced class weighting (`class_weight='balanced'`) in Random Forest |

---

## 6. Team Contributions

| Role | Person | Responsibilities |
|---|---|---|
| **Person 1** | Satellite Data Engineer | Preprocessing, cloud masking, CVA delta & magnitude, change mask |
| **Person 2** | GIS & Feature Engineer | Vectorization, NDVI calculation, 16-feature extraction, GeoJSON/CSV generation |
| **Person 3** | ML Engineer | Prototype labelling, Random Forest model training, batch inference, confidence scoring |
| **Person 4** | Frontend & GIS Visualizer | Streamlit GIS dashboard, interactive layer overlays, statistics & filters |

---

## 7. References

1. ESA Sentinel-2 MSI Technical Guide: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi
2. Malila, W. A. (1980). Change Vector Analysis: An Approach for Detecting Forest Changes with Landsat.
3. Otsu, N. (1979). A threshold selection method from gray-level histograms.
4. Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.
