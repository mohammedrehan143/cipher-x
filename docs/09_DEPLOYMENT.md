# 09 — DEPLOYMENT

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20 (updated: pyproj added to requirements — BUG-02 fix; .env gitignore fix noted)

---

## 1. Overview

CIPHER-X runs entirely locally during the hackathon. No cloud infrastructure is required for the MVP.

---

## 2. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended |
| pip | latest | `python -m pip install --upgrade pip` |
| Git | any | For version control |
| RAM | 8 GB minimum | 16 GB recommended for large AOI |
| Storage | 2 GB free | For Sentinel-2 band files |

**Optional (for visual inspection):**
- QGIS 3.x — open GeoTIFF and GeoJSON outputs

---

## 3. Installation

### 3.1 Clone the Repository

```bash
git clone https://github.com/mohammedrehan143/cipher-x.git
cd cipher-x
```

### 3.2 Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3.3 Install Dependencies

```bash
pip install -r requirements.txt
```

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

```bash
python run_pipeline.py
```

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
```

---

## 7. Demo Day Checklist

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

---

## 8. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: pyproj` | Missing before BUG-02 fix | `pip install pyproj` or `pip install -r requirements.txt` |
| `ModuleNotFoundError: rasterio` | Not installed | `pip install rasterio` or use conda |
| `FileNotFoundError: B02` | Bands not in expected folder | Check file naming contains `B02` |
| `All pixels masked` | Cloud-covered scene | Choose a clearer date |
| `GDAL_DATA not found` | Environment variable missing | `conda install gdal` or set GDAL_DATA |
| `ValueError: No valid pixels` | All pixels are NaN | Entire scene is cloud-covered |
| Change mask all zeros | Threshold too high | Check Otsu value printed to console |
| Dashboard 404 / import error | `app/main.py` not yet built | Person 2 must implement this |
