# 09 — DEPLOYMENT

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20 (updated: pyproj added to requirements — BUG-02 fix; .env gitignore fix noted)

---

## 1. Overview

<<<<<<< HEAD
CIPHER-X runs entirely locally during the hackathon. No cloud infrastructure is required for the MVP.
=======
CIPHER-X runs entirely locally during the hackathon. No cloud infrastructure is required for the MVP. This document covers:

1. Local development setup & dependencies
2. Running Person 1 pipeline (preprocessing + CVA)
3. Running Person 2 pipeline (vectorization + features)
4. Running Person 3 pipeline (labelling + Random Forest classification)
5. Running Person 4 dashboard (Streamlit GIS interface)
6. Hackathon demo workflow & troubleshooting
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

---

## 2. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended |
| pip | latest | `python -m pip install --upgrade pip` |
| Git | any | For version control |
<<<<<<< HEAD
| RAM | 8 GB minimum | 16 GB recommended for large AOI |
=======
| GDAL / rasterio deps | auto | Included via pip packages |
| RAM | 8 GB minimum | 16 GB recommended for large AOIs |
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
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

<<<<<<< HEAD
Current packages installed: `numpy, pandas, scikit-learn, scikit-image, scipy, matplotlib, opencv-python, rasterio, geopandas, shapely, pyproj, streamlit`

> **Note (BUG-02 fix, 2026-08-20):** `pyproj` was missing from the original `requirements.txt`. It is now included. If you installed before this fix, run `pip install pyproj` manually.

> **Note for Windows:** If `rasterio` fails, install via conda:
> ```bash
> conda install -c conda-forge rasterio geopandas pyproj
> pip install -r requirements.txt
> ```

### 3.4 Environment Variables (Optional)

```bash
cp .env.example .env
# Edit .env and fill in your Copernicus credentials if using auto-download
```

> **Security (BUG-03 fix, 2026-08-20):** `.env` is now properly listed in `.gitignore`. Never commit the `.env` file — only `.env.example` is safe to commit.

### 3.5 Verify Installation

```bash
python -c "import rasterio, numpy, skimage, scipy, pyproj, geopandas; print('All OK')"
```

---

## 4. Data Setup

### 4.1 Download Sentinel-2 Data

1. Go to https://browser.dataspace.copernicus.eu/
2. Register free → search your Area of Interest → select L2A product
3. Pick **two dates**: one BEFORE the change event, one AFTER
4. Use the **same Sentinel-2 tile** for both dates (same tile code = perfectly aligned by default)
5. Download the `.SAFE` folder

### 4.2 Place Band Files

Navigate inside the `.SAFE` folder:
```
<product>.SAFE/
└── GRANULE/
    └── <granule>/
        └── IMG_DATA/
            ├── R10m/      ← B02, B03, B04, B08 here
            └── R20m/      ← SCL here
```

Copy to:
```
data/sentinel/before/   ← BEFORE date band files
data/sentinel/after/    ← AFTER date band files
```

**File naming (standard ESA format — works automatically):**
```
T43PFP_20230101T054219_B02_10m.jp2
T43PFP_20230101T054219_B03_10m.jp2
T43PFP_20230101T054219_B04_10m.jp2
T43PFP_20230101T054219_B08_10m.jp2
T43PFP_20230101T054219_SCL_20m.jp2
```

---

## 5. Running the Pipelines

### 5.1 Person 1 Pipeline (Preprocessing + CVA)
=======
---

## 4. End-to-End Pipeline Execution
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

### Step 1: Preprocessing & CVA (Person 1)
```bash
python run_pipeline.py
```
<<<<<<< HEAD

With custom paths:
```bash
python run_pipeline.py --before data/sentinel/before --after data/sentinel/after
```

**Expected console output:**
```
[1/6] Loading BEFORE bands...
       Shape: (4, 10980, 10980)
[2/6] Loading AFTER bands...
       Shape: (4, 10980, 10980)
[3/6] Images already aligned — skipping reprojection.
[4/6] Applying cloud masks...
       Valid pixels: 78.3%
[5/6] Computing CVA magnitude...
[6/6] Generating binary change mask...
       Otsu threshold: 0.043218

Done. Outputs written to:
  outputs/maps/change_magnitude.tif
  outputs/maps/change_mask.tif
  data/processed/spectral_delta.tif

Statistics:
  Changed pixels: 45678 / 1234567 (3.70%)
  Magnitude: min=nan, max=0.8321, mean=0.0423
  Otsu threshold: 0.043218
```

### 5.2 Person 2 Pipeline (Vectorization + Features)

```bash
python run_vectorize.py
```

With custom minimum area:
```bash
python run_vectorize.py --min-area 500
```

### 5.3 Dashboard

```bash
streamlit run app/main.py
```

Opens at: `http://localhost:8501`

---

## 6. Verify Outputs

```bash
python -c "
import rasterio, numpy as np
for f in ['outputs/maps/change_magnitude.tif',
          'outputs/maps/change_mask.tif',
          'data/processed/spectral_delta.tif']:
    with rasterio.open(f) as src:
        d = src.read(1)
        print(f'{f}')
        print(f'  shape={src.shape}, bands={src.count}, crs={src.crs}')
        print(f'  min={float(np.nanmin(d)):.4f}, max={float(np.nanmax(d)):.4f}')
        print(f'  NaN pixels: {int(np.isnan(d).sum())} (should be > 0 if clouds exist)')
"
=======
**Outputs:**
- `outputs/maps/change_magnitude.tif`
- `outputs/maps/change_mask.tif`
- `data/processed/spectral_delta.tif`

---

### Step 2: Vectorization & Feature Extraction (Person 2)
```bash
python run_vectorize.py --min-area 1000
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
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

<<<<<<< HEAD
- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` completed
- [ ] BEFORE and AFTER band files in correct folders
- [ ] `python run_pipeline.py` runs without errors
- [ ] `outputs/maps/change_magnitude.tif` exists (NaN for clouds, not zeros — BUG-01 fixed)
- [ ] `outputs/maps/change_mask.tif` exists
- [ ] `python run_vectorize.py` runs without errors
- [ ] `outputs/polygons/change_results.geojson` exists
- [ ] `streamlit run app/main.py` opens dashboard
- [ ] Rehearsed 5-minute demo walkthrough
=======
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
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213

---

## 6. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
<<<<<<< HEAD
| `ModuleNotFoundError: pyproj` | Missing before BUG-02 fix | `pip install pyproj` or `pip install -r requirements.txt` |
| `ModuleNotFoundError: rasterio` | Not installed | `pip install rasterio` or use conda |
| `FileNotFoundError: B02` | Bands not in expected folder | Check file naming contains `B02` |
| `All pixels masked` | Cloud-covered scene | Choose a clearer date |
| `GDAL_DATA not found` | Environment variable missing | `conda install gdal` or set GDAL_DATA |
| `ValueError: No valid pixels` | All pixels are NaN | Entire scene is cloud-covered |
| Change mask all zeros | Threshold too high | Check Otsu value printed to console |
| Dashboard 404 / import error | `app/main.py` not yet built | Person 2 must implement this |
=======
| `ModuleNotFoundError: rasterio / geopandas` | Missing dependency | `pip install -r requirements.txt` |
| `FileNotFoundError: outputs/maps/...` | Person 1 pipeline not run | Run `python run_pipeline.py` first |
| `FileNotFoundError: outputs/predictions/change_features.csv` | Person 2 pipeline not run | Run `python run_vectorize.py` first |
| `FileNotFoundError: outputs/predictions/predictions.csv` | Person 3 pipeline not run | Run `python run_classify.py` first |
| `All pixels masked` | High cloud coverage in scene | Choose clearer acquisition dates |
| `No polygons found` | Area threshold too high | Lower threshold: `python run_vectorize.py --min-area 100` |
| `Class distribution imbalanced` | Natural scene variation | Random Forest uses `class_weight='balanced'` |
>>>>>>> 2b6cb418495339e11cf427b62342a836c6bf2213
