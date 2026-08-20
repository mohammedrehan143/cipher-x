# 09 — DEPLOYMENT

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Overview

CIPHER-X runs entirely locally during the hackathon. No cloud infrastructure is required for the MVP. This document covers:

1. Local development setup
2. Running the pipeline
3. Running the dashboard
4. Optional: Demo environment tips

---

## 2. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended |
| pip | latest | `python -m pip install --upgrade pip` |
| Git | any | For version control |
| GDAL / rasterio deps | auto | Installed via pip |
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

> **Note:** If `rasterio` fails on Windows, install via conda:
> ```bash
> conda install -c conda-forge rasterio
> pip install -r requirements.txt
> ```

### 3.4 Environment Variables (Optional)

```bash
cp .env.example .env
# Edit .env and fill in your Copernicus credentials if using auto-download
```

---

## 4. Data Setup

### 4.1 Manual Data Placement

1. Download Sentinel-2 L2A product from https://browser.dataspace.copernicus.eu/
2. Extract the `.SAFE` folder
3. Navigate to: `GRANULE/<tile>/IMG_DATA/R10m/`
4. Copy these files to `data/sentinel/before/`:
   - `*_B02_10m.jp2`
   - `*_B03_10m.jp2`
   - `*_B04_10m.jp2`
   - `*_B08_10m.jp2`
5. Copy `R20m/*_SCL_20m.jp2` to `data/sentinel/before/`
6. Repeat for AFTER date into `data/sentinel/after/`

### 4.2 Folder Structure After Data Setup

```
data/
├── sentinel/
│   ├── before/
│   │   ├── T43PFP_20230101_B02_10m.jp2
│   │   ├── T43PFP_20230101_B03_10m.jp2
│   │   ├── T43PFP_20230101_B04_10m.jp2
│   │   ├── T43PFP_20230101_B08_10m.jp2
│   │   └── T43PFP_20230101_SCL_20m.jp2
│   └── after/
│       ├── T43PFP_20230601_B02_10m.jp2
│       └── ...
```

---

## 5. Running the Pipeline

### 5.1 Person 1 Pipeline (Preprocessing + CVA)

```bash
python run_pipeline.py
```

With custom paths:
```bash
python run_pipeline.py --before data/sentinel/before --after data/sentinel/after --output outputs/maps
```

**Expected console output:**
```
[1/6] Loading BEFORE bands from data/sentinel/before ...
[2/6] Loading AFTER bands from data/sentinel/after ...
[3/6] Aligning images ...
[4/6] Applying cloud masks ...
[5/6] Computing CVA magnitude ...
[6/6] Generating change mask (Otsu threshold: 0.1234) ...

Pipeline complete.
Outputs:
  outputs/maps/change_magnitude.tif
  outputs/maps/change_mask.tif
  data/processed/spectral_delta.tif

Statistics:
  Valid pixels: 1234567 / 2000000 (61.7%)
  Changed pixels: 45678 / 1234567 (3.7%)
  Magnitude: min=0.0000, max=0.8321, mean=0.0423
```

### 5.2 Verify Outputs

```bash
python -c "
import rasterio, numpy as np
for f in ['outputs/maps/change_magnitude.tif','outputs/maps/change_mask.tif']:
    with rasterio.open(f) as src:
        d = src.read(1)
        print(f, src.shape, src.crs, float(np.nanmin(d)), float(np.nanmax(d)))
"
```

---

## 6. Running the Dashboard (Person 2)

```bash
streamlit run app/main.py
```

Opens at: `http://localhost:8501`

---

## 7. Demo Day Checklist

- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` completed
- [ ] BEFORE and AFTER band files in correct folders
- [ ] `python run_pipeline.py` runs without errors
- [ ] `outputs/maps/change_magnitude.tif` exists
- [ ] `outputs/maps/change_mask.tif` exists
- [ ] Person 2 pipeline run (polygons + classification)
- [ ] `streamlit run app/main.py` opens dashboard
- [ ] Dashboard displays change map correctly
- [ ] Rehearsed 5-minute demo walkthrough

---

## 8. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: rasterio` | Not installed | `pip install rasterio` or use conda |
| `FileNotFoundError: B02` | Bands not in folder | Check file naming pattern |
| `All pixels masked` | Cloud-covered scene | Choose a clearer date |
| `GDAL_DATA not found` | Environment issue | `conda install gdal` or set GDAL_DATA |
| Dashboard 404 | Wrong path | Run from project root directory |
