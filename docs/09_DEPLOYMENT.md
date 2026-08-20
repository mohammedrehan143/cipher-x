# 09 — DEPLOYMENT

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Overview

CIPHER-X runs entirely locally during the hackathon. No cloud infrastructure is required for the MVP. This document covers:

1. Local development setup & dependencies
2. Running Person 1 pipeline (preprocessing + CVA)
3. Running Person 2 pipeline (vectorization + features)
4. Running Person 3 pipeline (labelling + Random Forest classification)
5. Running Person 4 dashboard (Streamlit GIS interface)
6. Hackathon demo workflow & troubleshooting

---

## 2. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended |
| pip | latest | `python -m pip install --upgrade pip` |
| Git | any | For version control |
| GDAL / rasterio deps | auto | Included via pip packages |
| RAM | 8 GB minimum | 16 GB recommended for large AOIs |
| Storage | 2 GB free | For Sentinel-2 band files |

---

## 3. Installation

### 3.1 Clone the Repository & Setup Virtualenv

```bash
git clone https://github.com/mohammedrehan143/cipher-x.git
cd cipher-x

# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

### 3.2 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. End-to-End Pipeline Execution

### Step 1: Preprocessing & CVA (Person 1)
```bash
python run_pipeline.py
```
**Outputs:**
- `outputs/maps/change_magnitude.tif`
- `outputs/maps/change_mask.tif`
- `data/processed/spectral_delta.tif`

---

### Step 2: Vectorization & Feature Extraction (Person 2)
```bash
python run_vectorize.py --min-area 1000
```
**Outputs:**
- `outputs/polygons/change_results.geojson`
- `outputs/predictions/change_features.csv`

---

### Step 3: ML Classification (Person 3)
```bash
python run_classify.py
```
**Outputs:**
- `data/labels/prototype_labels.csv`
- `models/rf_classifier.joblib`
- `models/rf_imputer.joblib`
- `models/rf_metadata.json`
- `outputs/predictions/predictions.csv`

---

### Step 4: Launch Interactive GIS Dashboard (Person 4)
```bash
streamlit run app/main.py
```
Opens locally at: `http://localhost:8501`

---

## 5. Demo Day Checklist

**Before Demo:**
- [ ] Virtual environment activated
- [ ] Raw Sentinel-2 bands in `data/sentinel/before/` and `data/sentinel/after/`
- [ ] Person 1 `run_pipeline.py` produces clean change maps
- [ ] Person 2 `run_vectorize.py` generates valid polygons and 16 features
- [ ] Person 3 `run_classify.py` trains RF model and generates predictions with confidence
- [ ] Person 4 `app/main.py` opens and renders classified polygons on satellite map
- [ ] Rehearsed 5-minute presentation flow

---

## 6. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: rasterio / geopandas` | Missing dependency | `pip install -r requirements.txt` |
| `FileNotFoundError: outputs/maps/...` | Person 1 pipeline not run | Run `python run_pipeline.py` first |
| `FileNotFoundError: outputs/predictions/change_features.csv` | Person 2 pipeline not run | Run `python run_vectorize.py` first |
| `FileNotFoundError: outputs/predictions/predictions.csv` | Person 3 pipeline not run | Run `python run_classify.py` first |
| `All pixels masked` | High cloud coverage in scene | Choose clearer acquisition dates |
| `No polygons found` | Area threshold too high | Lower threshold: `python run_vectorize.py --min-area 100` |
| `Class distribution imbalanced` | Natural scene variation | Random Forest uses `class_weight='balanced'` |
