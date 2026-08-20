# 02 — PROJECT ARCHITECTURE

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CIPHER-X SYSTEM                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  DATA LAYER  │───▶│  PROCESSING CORE │───▶│ OUTPUT LAYER │  │
│  │              │    │                  │    │              │  │
│  │ Sentinel-2   │    │  Preprocessing   │    │ GeoTIFF maps │  │
│  │ BEFORE/AFTER │    │  CVA             │    │ GeoJSON poly │  │
│  │ SCL bands    │    │  Vectorization   │    │ Predictions  │  │
│  │ AOI GeoJSON  │    │  Features        │    │ Dashboard    │  │
│  └──────────────┘    │  ML Model        │    └──────────────┘  │
│                      └──────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Pipeline Data Flow

```
data/sentinel/before/          data/sentinel/after/
      │                               │
      ▼                               ▼
  loader.py ────────────────────── loader.py
  (B02,B03,B04,B08,SCL)           (B02,B03,B04,B08,SCL)
      │                               │
      └──────────┬────────────────────┘
                 ▼
            align.py
       (reproject to same CRS/grid)
                 │
                 ▼
           masking.py
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
          threshold.py
       (Otsu + morphological)
                 │
                 ▼
     outputs/maps/change_mask.tif
                 │                             ← Person 2 picks up here
                 ▼
          vectorize.py  (Person 2)
                 │
                 ▼
     outputs/polygons/changes.geojson
                 │
                 ▼
         features.py  (Person 2)
                 │
                 ▼
          ml_model.py  (Person 2)
                 │
                 ▼
     outputs/predictions/classified.geojson
                 │
                 ▼
          app/  Streamlit Dashboard  (Person 2)
```

---

## 3. Repository Structure

```
cipher-x/
│
├── docs/                          ← Documentation (this folder)
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
│   ├── preprocessing/             ← PERSON 1
│   │   ├── __init__.py
│   │   ├── loader.py              ← Read S2 bands
│   │   ├── align.py               ← CRS/grid alignment
│   │   └── masking.py             ← SCL cloud masking
│   ├── cva/                       ← PERSON 1
│   │   ├── __init__.py
│   │   ├── compute.py             ← CVA delta + magnitude
│   │   └── threshold.py           ← Otsu + morphological cleanup
│   ├── vectorization/             ← PERSON 2
│   ├── features/                  ← PERSON 2
│   └── models/                    ← PERSON 2
│
├── app/                           ← PERSON 2 — Streamlit dashboard
│
├── data/
│   ├── sentinel/
│   │   ├── before/                ← BEFORE S2 bands go here
│   │   └── after/                 ← AFTER S2 bands go here
│   ├── aoi/                       ← AOI GeoJSON (optional)
│   └── processed/                 ← Intermediate rasters
│
├── models/                        ← Trained ML model weights
├── notebooks/                     ← Exploration notebooks
├── outputs/
│   ├── maps/                      ← change_magnitude.tif, change_mask.tif
│   ├── polygons/                  ← changes.geojson
│   └── predictions/               ← classified.geojson
│
├── run_pipeline.py                ← End-to-end runner (Person 1 scope)
├── requirements.txt
├── .env.example
├── .gitignore
├── PERSON1_PIPELINE.md
└── README.md
```

---

## 4. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.10+ |
| Raster I/O | rasterio | latest |
| Numerical | numpy | latest |
| Spatial | geopandas, shapely | latest |
| Image processing | scikit-image, scipy | latest |
| ML | scikit-learn | latest |
| Visualisation | matplotlib | latest |
| Dashboard | Streamlit | latest |
| Data format (raster) | GeoTIFF | — |
| Data format (vector) | GeoJSON | — |
| Satellite data source | Copernicus / ESA | Sentinel-2 L2A |

---

## 5. Person Responsibilities Summary

| Person | Modules | Input | Output |
|---|---|---|---|
| Person 1 | preprocessing, cva | Raw S2 bands | change_magnitude.tif, change_mask.tif, spectral_delta.tif |
| Person 2 | vectorization, features, models, app | change_mask.tif, spectral_delta.tif | classified.geojson, Streamlit dashboard |

---

## 6. Interface Contract (Person 1 → Person 2)

Person 1 guarantees these files will exist after `python run_pipeline.py`:

| File | Format | Bands | CRS | Dtype |
|---|---|---|---|---|
| `outputs/maps/change_mask.tif` | GeoTIFF | 1 (uint8, 0/1) | Input S2 CRS | uint8 |
| `outputs/maps/change_magnitude.tif` | GeoTIFF | 1 (float32) | Input S2 CRS | float32 |
| `data/processed/spectral_delta.tif` | GeoTIFF | 4 [ΔB02,ΔB03,ΔB04,ΔB08] | Input S2 CRS | float32 |
