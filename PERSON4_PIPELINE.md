# CIPHER-X — PERSON 4: Streamlit Interactive GIS Dashboard & Final System Integration

> **Owner:** Person 4 (Frontend & GIS Visualizer / Integration Engineer)  
> **Scope:** Streamlit Dashboard (`app/`) + Full End-to-End Integration (P1 + P2 + P3 outputs)  
> **Target:** SIH 2026 Space-Tech Hackathon — Selection Round Presentation  
> **NOT in scope:** Sentinel-2 raw preprocessing (P1), CVA computation (P1), Vectorization (P2), Feature extraction (P2), Model training (P3)  
> **Last updated:** 2026-08-20  
> **Status:** 📋 Planning Phase Complete — Awaiting Approval to Implement  

---

## 1. 📋 Repository Audit & Current Asset Inventory

### Complete File Inventory (as of 2026-08-20)

| Directory / File | Status | Owner | Description / Contents |
|---|---|---|---|
| `data/sentinel/before/` | 📁 Ready | Person 1 | Directory for BEFORE Sentinel-2 L2A bands (B02, B03, B04, B08, SCL) |
| `data/sentinel/after/` | 📁 Ready | Person 1 | Directory for AFTER Sentinel-2 L2A bands (B02, B03, B04, B08, SCL) |
| `data/aoi/` | 📁 Ready | P1 / P2 | Directory for custom AOI boundary GeoJSON files |
| `data/processed/` | 📁 Ready | Person 1 | Intermediate processed rasters (`spectral_delta.tif`) |
| `data/labels/prototype_labels.csv` | ✅ Exists | Person 3 | Seed training dataset with 8 labelled polygons across change categories |
| `models/rf_classifier.joblib` | ✅ Exists (45.9 KB) | Person 3 | Serialized Random Forest classifier trained on 13 spectral & shape features |
| `models/rf_imputer.joblib` | ✅ Exists (607 B) | Person 3 | Serialized SimpleImputer (median strategy) for NaN resilience |
| `models/rf_metadata.json` | ✅ Exists (2.3 KB) | Person 3 | Full model metadata: feature list, class dictionary, metrics (accuracy, F1, confusion matrix) |
| `outputs/maps/` | 📁 Directory | Person 1 | Target location for `change_magnitude.tif` and `change_mask.tif` |
| `outputs/polygons/` | 📁 Directory | Person 2 | Target location for `change_results.geojson` |
| `outputs/predictions/change_features.csv` | ✅ Exists (9.0 KB) | Person 2 | 30 detected change regions with 16 extracted spatial/spectral features |
| `outputs/predictions/predictions.csv` | ✅ Exists (3.8 KB) | Person 3 | 30 classified change polygons with predicted class, label, confidence, lat/lon, area, CVA mean, delta NDVI |
| `src/preprocessing/` | ✅ Complete | Person 1 | Band loader (`loader.py`), grid aligner (`align.py`), SCL cloud masking (`masking.py`) |
| `src/cva/` | ✅ Complete | Person 1 | CVA delta/magnitude math (`compute.py`), Otsu thresholding & cleaning (`threshold.py`) |
| `src/vectorization/` | ✅ Complete | Person 2 | Raster-to-vector polygonizer (`polygonize.py`) |
| `src/features/` | ✅ Complete | Person 2 | NDVI computer (`ndvi.py`), 16-feature extractor (`extractor.py`) |
| `src/models/` | ✅ Complete | Person 3 | Auto-labeller (`labeller.py`), Random Forest trainer & inference (`classifier.py`) |
| `run_pipeline.py` | ✅ Complete | Person 1 | Person 1 CLI orchestrator |
| `run_vectorize.py` | ✅ Complete | Person 2 | Person 2 CLI orchestrator |
| `run_classify.py` | ✅ Complete | Person 3 | Person 3 CLI orchestrator |
| `demo_test.py` | ✅ Complete | All | Synthetic end-to-end smoke test script |
| `app/README.md` | ✅ Stub | Person 4 | Documentation stub for Streamlit app |
| `app/__init__.py` | ✅ Exists | Person 4 | Package initialization |
| `docs/` (10 files) | ✅ Complete | All | Architecture, Requirements, API, Responsibilities, Testing, Deployment specs |

---

## 2. 🔗 End-to-End System Flow & Data Contracts

Person 4 serves as the **unifying integration layer** that brings together the upstream engineering pipeline into a high-impact, presentation-grade interactive dashboard for SIH judges.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               CIPHER-X PIPELINE DATA FLOW                              │
│                                                                                        │
│  [PERSON 1: Satellite & CVA Engine]                                                    │
│  Sentinel-2 Bands (Before/After) ──▶ Alignment ──▶ Cloud Masking ──▶ CVA Magnitude     │
│                                                                      │                 │
│                                            ┌─────────────────────────┴───────────────┐ │
│                                            ▼                                         ▼ │
│                              outputs/maps/change_magnitude.tif   outputs/maps/change_mask.tif
│                                            │                                         │ │
│  [PERSON 2: Vectorization & Features]      │                                         │ │
│  Raster Mask ──▶ Polygonize ──▶ Shape Clean ──▶ Feature Extractor (16 Features)       │
│                                            │                                         │ │
│                                            ┌─────────────────────────┬───────────────┘ │
│                                            ▼                         ▼                 │
│                   outputs/polygons/change_results.geojson   outputs/predictions/       │
│                                                             change_features.csv        │
│                                                                      │                 │
│  [PERSON 3: Machine Learning Classifier]                             ▼                 │
│  Feature Matrix ──▶ Median Impute ──▶ Random Forest Classifier (100 Trees)             │
│                                                                      │                 │
│                                                                      ▼                 │
│                                                             outputs/predictions/       │
│                                                             predictions.csv            │
│                                                                      │                 │
│  [PERSON 4: Interactive GIS Dashboard & Integration]                │                 │
│  outputs/predictions/predictions.csv ──────────────┐                 │                 │
│  outputs/polygons/change_results.geojson ──────────┼─────────────────┘                 │
│  outputs/maps/change_magnitude.tif ────────────────┤                                   │
│  models/rf_metadata.json ──────────────────────────┤                                   │
│                                                    ▼                                   │
│                           ┌──────────────────────────────────┐                         │
│                           │      STREAMLIT GIS DASHBOARD     │                         │
│                           │        (`app/main.py`)           │                         │
│                           │  - Space-Tech Command Center UI  │                         │
│                           │  - Interactive Folium/Leaflet Map│                         │
│                           │  - Before/After Slider & CVA     │                         │
│                           │  - Region Inspector & ML Insights│                         │
│                           │  - Real-time Filter & KPI Matrix │                         │
│                           │  - Automated Executive Report    │                         │
│                           └──────────────────────────────────┘                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 🎯 Judge Demonstration Narrative (The "Winning Demo Flow")

To maximize impact during the SIH internal selection round, the dashboard will follow a cinematic, problem-to-solution narrative:

```
[1. The Global Challenge]
"Rapid unauthorized human expansion, deforestation, and illegal construction require automated surveillance."
         │
         ▼
[2. Temporal Observation]
Show Sentinel-2 BEFORE scene vs AFTER scene side-by-side.
         │
         ▼
[3. Algorithmic Change Detection (CVA)]
Show CVA spectral difference magnitude highlighting anomalous energy flux.
         │
         ▼
[4. Vector Intelligence]
Show automatically extracted polygon boundaries overlaid on an interactive GIS map.
         │
         ▼
[5. AI Identification & Confidence]
Click any polygon → Instant classification: "Vegetation Clearing (78.3% confidence)", Area: 11,885 m², Centroid coordinates, NDVI drop: -0.38.
         │
         ▼
[6. Macro Analytics & Actionable Intelligence]
Summary KPIs: Total changed land (17.4 hectares), Risk distribution chart, Exportable inspection report for authorities.
```

---

## 4. 🧱 Phased Implementation Plan for Person 4

---

### 🔹 PHASE 0: Environment Verification & Zero-Crash Resilience Architecture
* **Goal:** Ensure all required visualization libraries are accessible and build a robust fallback layer so the app runs flawlessly under all edge cases (missing rasters, missing GeoJSON, missing GPU, etc.).
* **Key Steps:**
  1. Verify dependencies (`streamlit`, `geopandas`, `folium` / `streamlit-folium`, `matplotlib`, `rasterio`, `shapely`, `pandas`, `numpy`).
  2. Implement an intelligent synthetic geometry builder: If `outputs/polygons/change_results.geojson` is missing, dynamically generate bounding polygons from `outputs/predictions/predictions.csv` (using `latitude`, `longitude`, and `area_m2` / `bbox_width_m`) so the interactive map NEVER appears blank.
  3. Implement raster preview fallbacks: If high-resolution GeoTIFFs are not yet generated, render synthetic spectral preview visualizations or simulated satellite tiles.
* **Status:** ⏳ Planned

---

### 🔹 PHASE 1: Data Integration & State Management Layer (`app/data_loader.py`)
* **Goal:** Build high-performance, cached data ingestion module that reads and validates all upstream artifacts.
* **Key Functions:**
  - `load_predictions_data()`: Reads `outputs/predictions/predictions.csv` and `models/rf_metadata.json` with `@st.cache_data`.
  - `load_change_polygons()`: Loads `outputs/polygons/change_results.geojson` and merges with predictions on `id`.
  - `load_raster_metadata()`: Reads metadata/bounds from `outputs/maps/change_magnitude.tif` if available.
  - `compute_kpi_summary()`: Computes total change area (m² / hectares), class breakdown counts, mean confidence, and highest-risk region.
* **Status:** ⏳ Planned

---

### 🔹 PHASE 2: Space-Tech UI Design System & Dashboard Header
* **Goal:** Establish a modern, dark-themed ISRO/NASA Space-Tech styling with custom CSS, intuitive navigation, and status badges.
* **Visual Components:**
  - Header with CIPHER-X Logo, SIH 2026 Space-Tech badge, and subtitle: *"Satellite-based detection and classification of significant land-use changes using Sentinel-2 temporal imagery and machine learning."*
  - System Telemetry Banner: Pipeline Status indicators (Person 1 CVA: ✅, Person 2 Vector: ✅, Person 3 ML: ✅, System Health: 100%).
  - Sidebar Controls: Filter by Change Class (Multi-select), Confidence Threshold Slider (0.0 – 1.0), Area Range Slider, Basemap Switcher (Satellite Hybrid, OpenStreetMap, Dark CartoDB).
* **Status:** ⏳ Planned

---

### 🔹 PHASE 3: Interactive GIS Map Component (`app/map_view.py`)
* **Goal:** Embed a responsive, full-featured interactive GIS map displaying all detected change polygons.
* **Features:**
  - Color-coded change polygons according to SIH class standard:
    * 🏗️ **New Construction:** `#FF6B35` (Vibrant Orange)
    * 🛣️ **Road Change / Expansion:** `#4A90D9` (Cyan / Blue)
    * 🌲 **Vegetation Clearing:** `#E63946` (Crimson Red)
    * ⛏️ **Excavation / Mining:** `#9C6644` (Earth Brown)
    * ❓ **Other Human Change:** `#8D99AE` (Slate Grey)
  - Interactive Tooltips & Click Popups: Displaying `Region ID`, `Classification`, `Confidence %`, `Area (m²)`, and `Coordinates`.
  - Layer Controls: Toggle change polygons, centroid markers, and choropleth risk overlay.
  - Auto-center & zoom-to-selection when an AOI is chosen in the inspector.
* **Status:** ⏳ Planned

---

### 🔹 PHASE 4: Selected AOI Deep-Dive Inspector
* **Goal:** Dedicated high-density intelligence panel when a judge clicks or selects a specific change polygon.
* **Detailed Readout:**
  - **Header Card:** Change Region ID (e.g., `#27`), Class Badge, and Confidence Meter (with color rating: High > 80%, Medium 60-80%, Review < 60%).
  - **Geographic Specs:** Latitude, Longitude, Area in m² and Hectares, Compactness index, Bounding box dimensions.
  - **Spectral Analytics:**
    * CVA Magnitude: Mean & Peak magnitude inside polygon.
    * NDVI Change: $\Delta \text{NDVI} = \text{NDVI}_{\text{after}} - \text{NDVI}_{\text{before}}$ with visual vegetation delta gauge.
    * Band-level reflectance shifts ($\Delta B02, \Delta B03, \Delta B04, \Delta B08$).
  - **AI Model Decision Explanation:** Feature contribution overview showing why Random Forest chose this class.
* **Status:** ⏳ Planned

---

### 🔹 PHASE 5: Before / After Satellite & CVA Visualization Engine
* **Goal:** Provide side-by-side or split visual comparison demonstrating the raw satellite evidence.
* **Features:**
  - Before Scene (Sentinel-2 L2A Natural Color RGB: B04, B03, B02).
  - After Scene (Sentinel-2 L2A Natural Color RGB: B04, B03, B02).
  - CVA Spectral Change Magnitude Heatmap (Jet/Viridis colormap showing intensity of change).
  - Masked Vector Overlay illustrating exact detected boundary.
* **Status:** ⏳ Planned

---

### 🔹 PHASE 6: Macro Analytics, Feature Importance & Technical Metrics
* **Goal:** Showcase scientific rigor and ML transparency to the judges.
* **Analytics Tabs:**
  - **Class Distribution:** Donut chart & Bar chart of detected activity types across the entire AOI.
  - **Confidence Distribution:** Histogram of prediction confidence scores.
  - **Feature Importance Chart:** Extracted directly from `models/rf_metadata.json` showing Random Forest feature ranking (e.g., `ndvi_after`, `delta_ndvi`, `cva_max`, `delta_b02`).
  - **Confusion Matrix & Model Accuracy:** Live view of model validation metrics ($1.00$ accuracy on prototype validation set).
* **Status:** ⏳ Planned

---

### 🔹 PHASE 7: Export, Reporting & Presentation Polish
* **Goal:** Complete packaging with one-click report generator for field teams and authorities.
* **Features:**
  - "Download GeoJSON" button for QGIS / ArcGIS integration.
  - "Download Predictions CSV" button for data auditing.
  - Executive Inspection Summary Card (ready for print / presentation).
  - Keyboard shortcuts & demo guide in sidebar.
* **Status:** ⏳ Planned

---

## 5. 🎨 Design System & Visual Palette

```
Background:         #0E1117 (Deep Obsidian Navy)
Card Surface:       #1E232F (Dark Slate Panel)
Border Highlight:   #2E384D (Subtle Steel Blue)
Primary Accent:     #00D2FF (Cyan Laser)
Secondary Accent:   #7928CA (Electric Purple)
Text Primary:       #FFFFFF (Pure White)
Text Secondary:     #94A3B8 (Cool Slate)

Class Colors:
- New Construction:       #FF6B35  [Building]
- Road Expansion:         #3A86FF  [Roadway]
- Vegetation Clearing:    #E63946  [Tree-Slash]
- Excavation / Mining:    #9C6644  [Excavator]
- Other Human Change:     #8D99AE  [Question Mark]
```

---

## 6. 🛡️ Robustness & Anti-Crash Safety Matrix

| Failure Scenario | Upstream Cause | Person 4 Fallback Mechanism | User Experience |
|---|---|---|---|
| `change_results.geojson` missing | Person 2 didn't run vectorizer | Generate synthetic polygon boxes around centroids from `predictions.csv` | Map renders instantly with accurate coordinates & tags |
| GeoTIFF files missing in `outputs/maps/` | Person 1 pipeline not run | Render high-contrast synthetic spectral preview maps using matplotlib / numpy | Visual comparison displays cleanly with "Simulated Raster" badge |
| Missing bands in `data/sentinel/` | User didn't download raw S2 tiles | Use cached predictions and precomputed feature distributions | Dashboard opens in < 1 second with full interactivity |
| Single-class or small predictions set | Prototype dataset (< 50 rows) | Gracefully handle empty chart buckets, show exact row counts | Metrics adjust dynamically without index/key errors |
| `folium` / `streamlit-folium` render issue | Browser iframe restriction | Provide Pydeck / Plotly fallback map option | Map always displays regardless of environment |

---

## 7. 📊 Progress Tracker

| Phase | Description | Status | Target Completion | Notes |
|---|---|---|---|---|
| **Phase 0** | Repo Audit & Integration Architecture Plan | ✅ **DONE** | 2026-08-20 | Full inventory & contracts verified |
| **Phase 1** | Data Loader & Resilience Layer (`app/data_loader.py`) | ⏳ Pending Go-Ahead | — | Ready to implement |
| **Phase 2** | UI Layout, Theme & Telemetry Header | ⏳ Pending Go-Ahead | — | Ready to implement |
| **Phase 3** | Interactive GIS Map (`app/map_component.py`) | ⏳ Pending Go-Ahead | — | Ready to implement |
| **Phase 4** | Selected Region Deep-Dive Inspector | ⏳ Pending Go-Ahead | — | Ready to implement |
| **Phase 5** | Before/After & CVA Visualizer | ⏳ Pending Go-Ahead | — | Ready to implement |
| **Phase 6** | ML Analytics, Feature Importance & Metrics | ⏳ Pending Go-Ahead | — | Ready to implement |
| **Phase 7** | End-to-End Verification & Presentation Polish | ⏳ Pending Go-Ahead | — | Ready to implement |

---

## 8. 📝 Update Log

| Timestamp | Event / Update Description |
|---|---|
| **2026-08-20 T15:05** | Completed thorough repository audit across P1, P2, and P3 deliverables. Verified existence of `predictions.csv` (30 regions), `change_features.csv` (30 rows, 16 features), `rf_classifier.joblib`, `rf_imputer.joblib`, and `rf_metadata.json`. |
| **2026-08-20 T15:10** | Authored `PERSON4_PIPELINE.md` master plan. Established zero-crash fallback design, 7 implementation phases, design system, and SIH judge demo flow. All work planned cleanly with zero code pollution prior to user approval. |
