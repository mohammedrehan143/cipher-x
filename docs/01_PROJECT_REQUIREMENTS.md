# 01 — PROJECT REQUIREMENTS

> **Project:** CIPHER-X  
> **Event:** Smart India Hackathon (SIH) 2026 — Space Tech Track  
> **Team:** 2nd-year Engineering Students  
> **Last Updated:** 2026-08-20

---

## 1. Problem Statement

Detect **human-related land-use / land-cover changes** from multi-temporal satellite imagery (Sentinel-2), classify the type of change, and present the results on an interactive GIS dashboard.

**Use cases include:**
- Illegal construction or encroachment detection
- Deforestation and forest degradation
- Agricultural land conversion
- Urban expansion and sprawl
- Water body reduction (lakes, ponds)

---

## 2. Functional Requirements

### FR-01 — Data Ingestion
- The system SHALL accept Sentinel-2 L2A imagery as input (BEFORE + AFTER dates).
- The system SHALL support `.jp2` and `.tif` band files.
- Band files SHALL be placed in `data/sentinel/before/` and `data/sentinel/after/`.
- The system SHALL read bands B02, B03, B04, B08, and the SCL layer.

### FR-02 — Preprocessing
- The system SHALL convert DN values to surface reflectance (÷ 10000).
- The system SHALL align BEFORE and AFTER images to the same CRS, grid, and resolution.
- The system SHALL generate a cloud/shadow validity mask using the SCL band.
- Masked pixels SHALL be excluded from all downstream analysis.

### FR-03 — Change Vector Analysis (CVA)
- The system SHALL compute per-pixel spectral delta across B02, B03, B04, B08.
- The system SHALL compute CVA magnitude: M = sqrt(ΔB02² + ΔB03² + ΔB04² + ΔB08²).
- The system SHALL output a continuous change magnitude raster.

### FR-04 — Change Detection
- The system SHALL apply Otsu thresholding to the magnitude raster.
- The system SHALL apply morphological operations to remove noise from the binary mask.
- The system SHALL output a binary change mask (0 = no change, 1 = change).

### FR-05 — Vectorization
- The system SHALL convert the change mask raster into polygon GeoJSON.
- Output polygons SHALL retain magnitude statistics as attributes.

### FR-06 — Feature Extraction
- The system SHALL extract spectral, textural, and index-based features per change polygon.
- Features SHALL include: NDVI delta, NDWI delta, mean/std per band delta.

### FR-07 — ML Classification
- The system SHALL classify each change polygon into a human-activity category.
- Minimum categories: Construction, Deforestation, Water Loss, Agricultural Change.
- The classifier SHALL be trainable on labelled samples.

### FR-08 — Dashboard
- The system SHALL display a Streamlit-based interactive map.
- The dashboard SHALL show: change polygons overlaid on imagery, class labels, magnitude heatmap.
- The dashboard SHALL allow filtering by change class and date.

---

## 3. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Processing time (10km × 10km AOI) | < 5 minutes on CPU |
| NFR-02 | Pipeline must run on student laptops | Min 8GB RAM, no GPU required |
| NFR-03 | All paths must be project-relative | No hardcoded absolute paths |
| NFR-04 | Reproducibility | Any team member can run `python run_pipeline.py` |
| NFR-05 | Code readability | Functions < 50 lines, docstrings on every public function |
| NFR-06 | Output formats | GeoTIFF + GeoJSON (QGIS-compatible) |

---

## 4. Constraints

- 24-hour hackathon window — MVP over perfection
- No commercial API keys — use only free Copernicus/ESA data
- Team size: 2 people working in parallel on separate modules
- Internet may be limited — pre-download all required data before the event

---

## 5. Success Criteria

| Criterion | Measurement |
|---|---|
| Pipeline runs end-to-end | `python run_pipeline.py` completes without errors |
| Change mask is non-trivial | Contains both 0 and 1 values; visually reasonable |
| Polygons generated | At least 1 valid GeoJSON polygon in `outputs/polygons/` |
| Dashboard loads | Streamlit app opens and renders the change map |
| Classification works | At least 2 classes predicted on test data |

---

## 6. Out of Scope (MVP)

- Atmospheric correction beyond L2A standard
- Time-series analysis (> 2 dates)
- SAR data fusion
- Real-time streaming
- User authentication
