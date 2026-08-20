# 02 — PROJECT ARCHITECTURE

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             CIPHER-X SYSTEM                             │
│                                                                         │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────────┐  │
│  │  DATA LAYER  │───▶│  PROCESSING CORE │───▶│     OUTPUT LAYER     │  │
│  │              │    │                  │    │                      │  │
│  │ Sentinel-2   │    │ Person 1: CVA    │    │ GeoTIFF change maps  │  │
│  │ BEFORE/AFTER │    │ Person 2: Vector │    │ GeoJSON polygons     │  │
│  │ SCL bands    │    │ Person 3: ML     │    │ Predictions CSV      │  │
│  │ AOI GeoJSON  │    │ Person 4: App    │    │ Streamlit Dashboard  │  │
│  └──────────────┘    └──────────────────┘    └──────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pipeline Data Flow

```
data/sentinel/before/          data/sentinel/after/
      │                               │
      ▼                               ▼
  loader.py ────────────────────── loader.py      (Person 1)
  (B02,B03,B04,B08,SCL)           (B02,B03,B04,B08,SCL)
      │                               │
      └──────────┬────────────────────┘
                 ▼
            align.py                              (Person 1)
       (reproject to same CRS/grid)
                 │
                 ▼
            masking.py                            (Person 1)
       (SCL cloud/shadow mask)
                 │
                 ▼
            compute.py  ──────────────▶  data/processed/spectral_delta.tif
       (CVA delta + magnitude)
                 │
                 ▼
     outputs/maps/change_magnitude.tif
                 │
                 ▼
          threshold.py                            (Person 1)
       (Otsu + morphological)
                 │
                 ▼
     outputs/maps/change_mask.tif
                 │                             ← Person 2 picks up here
                 ▼
          polygonize.py                           (Person 2)
       (cleanup + raster-to-vector)
                 │
                 ▼
     outputs/polygons/change_results.geojson
                 │
                 ▼
         extractor.py + ndvi.py                   (Person 2)
       (sample 16 features per polygon)
                 │
                 ▼
     outputs/predictions/change_features.csv
                 │                             ← Person 3 picks up here
                 ▼
          labeller.py                             (Person 3)
       (rule-based provisional labelling)
                 │
                 ▼
     data/labels/prototype_labels.csv
                 │
                 ▼
          classifier.py                           (Person 3)
       (Random Forest training & model evaluation)
                 │
                 ▼
     models/rf_classifier.joblib
     models/rf_imputer.joblib
     models/rf_metadata.json
                 │
                 ▼
         run_classify.py                          (Person 3)
       (inference: class + confidence)
                 │
                 ▼
     outputs/predictions/predictions.csv
                 │                             ← Person 4 picks up here
                 ▼
          app/main.py                             (Person 4)
       (Streamlit Dashboard: GIS map, filters, metrics)
```

---

## 3. Repository Structure

```
cipher-x/
│
├── docs/                          ← Architecture, API, Data, Responsibilities
│   ├── 01_PROJECT_REQUIREMENTS.md
│   ├── 02_PROJECT_ARCHITECTURE.md
│   ├── 03_DATABASE_DESIGN.md
│   ├── 04_API_DOCUMENTATION.md
│   ├── 05_MODULE_RESPONSIBILITIES.md
│   ├── 06_GIT_WORKFLOW.md
│   ├── 07_TESTING_PLAN.md
│   ├── 08_SECURITY.md
│   ├── 09_DEPLOYMENT.md
│   └── 10_FINAL_REPORT.md
│
├── src/                           ← Core processing modules
│   ├── __init__.py
│   ├── preprocessing/             ← PERSON 1 (loader, align, masking)
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── align.py
│   │   └── masking.py
│   ├── cva/                       ← PERSON 1 (compute, threshold)
│   │   ├── __init__.py
│   │   ├── compute.py
│   │   └── threshold.py
│   ├── vectorization/             ← PERSON 2 (polygonize)
│   │   ├── __init__.py
│   │   └── polygonize.py
│   ├── features/                  ← PERSON 2 (extractor, ndvi)
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   └── ndvi.py
│   └── models/                    ← PERSON 3 (classifier, labeller)
│       ├── __init__.py
│       ├── labeller.py
│       └── classifier.py
│
├── app/                           ← PERSON 4 — Streamlit interactive GIS dashboard
│   ├── __init__.py
│   └── main.py
│
├── data/
│   ├── sentinel/
│   │   ├── before/                ← BEFORE S2 bands
│   │   └── after/                 ← AFTER S2 bands
│   ├── aoi/                       ← AOI GeoJSON (optional)
│   ├── labels/                    ← PERSON 3 (prototype_labels.csv)
│   └── processed/                 ← Intermediate rasters (spectral_delta.tif)
│
├── models/                        ← PERSON 3 (rf_classifier.joblib, imputer, metadata)
├── notebooks/                     ← Exploration notebooks
├── outputs/
│   ├── maps/                      ← PERSON 1 (change_magnitude.tif, change_mask.tif)
│   ├── polygons/                  ← PERSON 2 (change_results.geojson)
│   └── predictions/               ← PERSON 2 (change_features.csv), PERSON 3 (predictions.csv)
│
├── run_pipeline.py                ← PERSON 1 end-to-end runner
├── run_vectorize.py               ← PERSON 2 end-to-end runner
├── run_classify.py                ← PERSON 3 end-to-end runner
├── PERSON1_PIPELINE.md            ← PERSON 1 master plan
├── PERSON2_PIPELINE.md            ← PERSON 2 master plan
├── PERSON3_PIPELINE.md            ← PERSON 3 master plan
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Language | Python 3.10+ | Core language |
| Raster Processing | rasterio, GDAL | Band reading, warping, mask generation |
| Numerical & Array | numpy, scipy | CVA calculations, morphological filtering |
| Spatial Vectors | geopandas, shapely | Polygonization, CRS projection, geometry metrics |
| Machine Learning | scikit-learn, joblib | Random Forest classifier, imputation, serialization |
| Frontend / UI | streamlit, folium / pydeck | Interactive GIS map, filtering, metrics dashboard |
| Formats | GeoTIFF, GeoJSON, CSV | QGIS-compatible data exchange |

---

## 5. Person Responsibilities & Handoff Summary

| Person | Focus Area | Inputs | Key Deliverables | Downstream Hand-off |
|---|---|---|---|---|
| **Person 1** | Satellite Preprocessing & CVA | Raw Sentinel-2 L2A bands | `change_mask.tif`, `change_magnitude.tif`, `spectral_delta.tif` | Person 2 |
| **Person 2** | GIS Vectorization & Features | Person 1 rasters + raw bands | `change_results.geojson`, `change_features.csv` (16 cols) | Person 3 & Person 4 |
| **Person 3** | ML Classification | `change_features.csv` | `predictions.csv`, `models/rf_classifier.joblib` | Person 4 |
| **Person 4** | Interactive Dashboard | `change_results.geojson` + `predictions.csv` | Streamlit GIS app (`app/main.py`) | End-users / Judges |

---

## 6. Cross-Person Interface Contracts

```
[Person 1]
  outputs/maps/change_mask.tif
  outputs/maps/change_magnitude.tif
  data/processed/spectral_delta.tif
        │
        ▼
[Person 2]
  outputs/polygons/change_results.geojson
  outputs/predictions/change_features.csv
        │
        ▼
[Person 3]
  outputs/predictions/predictions.csv (id, predicted_class, predicted_label, confidence, ...)
  models/rf_classifier.joblib
        │
        ▼
[Person 4]
  Streamlit app joins `change_results.geojson` and `predictions.csv` on `id`
  Displays interactive map, statistics, and classification breakdown.
```
