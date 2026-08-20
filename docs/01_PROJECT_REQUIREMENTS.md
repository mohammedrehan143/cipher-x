# 01 — PROJECT REQUIREMENTS

> **Project:** CIPHER-X  
> **Event:** Smart India Hackathon (SIH) 2026 — Space Tech Track  
> **Team:** 2nd-year Engineering Students (4-Person Team)  
> **Last Updated:** 2026-08-20

---

## 1. Problem Statement

Detect **human-related land-use / land-cover changes** from multi-temporal satellite imagery (Sentinel-2), classify the type of change using Machine Learning, and present the results on an interactive GIS dashboard.

**Use cases include:**
- Illegal construction or encroachment detection
- Deforestation and forest degradation
- Agricultural land conversion & clearing
- Urban expansion and infrastructure / road expansion
- Excavation, mining, and water body changes

---

## 2. Functional Requirements

### FR-01 — Data Ingestion (Person 1)
- The system SHALL accept Sentinel-2 L2A imagery as input (BEFORE + AFTER dates).
- The system SHALL support `.jp2` and `.tif` band files.
- Band files SHALL be placed in `data/sentinel/before/` and `data/sentinel/after/`.
- The system SHALL read bands B02, B03, B04, B08, and the SCL layer.

### FR-02 — Preprocessing (Person 1)
- The system SHALL convert DN values to surface reflectance (÷ 10000).
- The system SHALL align BEFORE and AFTER images to the same CRS, grid, and resolution.
- The system SHALL generate a cloud/shadow validity mask using the SCL band.
- Masked pixels SHALL be excluded from all downstream analysis.

### FR-03 — Change Vector Analysis (Person 1)
- The system SHALL compute per-pixel spectral delta across B02, B03, B04, B08.
- The system SHALL compute CVA magnitude: $M = \sqrt{\Delta B02^2 + \Delta B03^2 + \Delta B04^2 + \Delta B08^2}$.
- The system SHALL output a continuous change magnitude raster (`change_magnitude.tif`).

### FR-04 — Change Detection (Person 1)
- The system SHALL apply Otsu thresholding to the magnitude raster.
- The system SHALL apply morphological operations to remove noise from the binary mask.
- The system SHALL output a binary change mask (`change_mask.tif`).

### FR-05 — Vectorization (Person 2)
- The system SHALL convert the change mask raster into polygon GeoJSON (`change_results.geojson`).
- Polygons with area smaller than a configurable minimum (`min_area_m2`) SHALL be filtered out.
- Output polygons SHALL retain geographic centroids in WGS84 (latitude, longitude).

### FR-06 — Feature Extraction (Person 2)
- The system SHALL extract 16 spectral, index-based, and geometric features per change polygon.
- Features SHALL include: area ($m^2$), latitude, longitude, CVA mean, CVA max, NDVI before, NDVI after, $\Delta\text{NDVI}$, $\Delta\text{B02}$, $\Delta\text{B03}$, $\Delta\text{B04}$, $\Delta\text{B08}$, bounding box width ($m$), bounding box height ($m$), compactness.
- Features SHALL be exported as `outputs/predictions/change_features.csv` for ML processing.

### FR-07 — ML Classification (Person 3)
- The system SHALL train a balanced `RandomForestClassifier` on labelled polygon features.
- The system SHALL classify each change polygon into a target human-activity category:
  1. `New Construction` (Class 0)
  2. `Road Change / Expansion` (Class 1)
  3. `Vegetation Clearing` (Class 2)
  4. `Excavation / Mining` (Class 3)
  5. `Other Human Change` (Class 4)
- The system SHALL predict the class label and a confidence score ($0.0 - 1.0$) for each polygon.
- Output SHALL be exported to `outputs/predictions/predictions.csv`.

### FR-08 — Dashboard & GIS Visualization (Person 4)
- The system SHALL display a Streamlit-based interactive map (`app/main.py`).
- The dashboard SHALL join `change_results.geojson` with `predictions.csv` on `id`.
- The dashboard SHALL show change polygons colored by predicted class with confidence filtering.

---

## 3. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Processing time (10km × 10km AOI) | < 5 minutes on CPU end-to-end |
| NFR-02 | Hardware compatibility | Minimum 8GB RAM, standard laptop CPU, no GPU required |
| NFR-03 | File path robustness | All paths project-relative via `pathlib.Path` |
| NFR-04 | Reproducibility | Clean command execution: `run_pipeline.py` -> `run_vectorize.py` -> `run_classify.py` -> `streamlit run app/main.py` |
| NFR-05 | Modularity & Code Quality | Functions < 60 lines with docstrings and type annotations |
| NFR-06 | Standardized Formats | GeoTIFF, GeoJSON (EPSG:4326), CSV, joblib models |

---

## 4. Constraints

- 24-hour hackathon window — practical working MVP over speculative research models
- No commercial or paid API keys — use open Copernicus Sentinel-2 data
- 4-person collaborative team working in parallel on modular sub-components

---

## 5. Success Criteria

| Criterion | Measurement |
|---|---|
| Pipeline runs end-to-end | `run_pipeline.py`, `run_vectorize.py`, and `run_classify.py` complete with exit code 0 |
| Change detection is valid | `change_mask.tif` contains non-trivial change pixels |
| Polygons generated | Valid polygons in `outputs/polygons/change_results.geojson` with 16 features |
| ML Predictions generated | `outputs/predictions/predictions.csv` contains predicted class and confidence scores |
| Dashboard renders | Streamlit app opens and renders interactive polygon map with statistics |
