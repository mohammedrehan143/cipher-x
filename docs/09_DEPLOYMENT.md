# 09 — DEPLOYMENT

> **Project:** CIPHER-X  
> **Last Updated:** 2026-08-20

---

## 1. Overview

CIPHER-X runs entirely locally during the hackathon. No cloud infrastructure is required for the MVP. This document covers:

1. Local development setup
2. Running Person 1 pipeline (preprocessing + CVA)
3. Running Person 2 pipeline (vectorization + features)
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
> conda install -c conda-forge rasterio geopandas
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

## 5. Running Person 1 Pipeline (Preprocessing + CVA)

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

**Verify Person 1 outputs:**
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

## 6. Running Person 2 Pipeline (Vectorization + Features)

> **Prerequisite:** Person 1 pipeline must have completed successfully first.

```bash
python run_vectorize.py
```

With custom minimum polygon area:
```bash
python run_vectorize.py --min-area 500
```

**Expected console output:**
```
[1/6] Checking Person 1 outputs exist...
[2/6] Loading and vectorizing change mask...
[3/6] Computing NDVI (before)...
[4/6] Computing NDVI (after)...
[5/6] Extracting polygon features...
[6/6] Saving outputs...

Done. Outputs written to:
  outputs/polygons/change_results.geojson
  outputs/predictions/change_features.csv

Summary:
  Total change polygons: 47
  Total changed area: 1234567 m2 (123.5 ha)
  Polygon area range: 1012 m2 - 98765 m2
  Mean CVA magnitude: 0.2341
  Mean delta NDVI: -0.1823
  Columns exported: [id, area_m2, latitude, longitude, ...]
```

**Verify Person 2 outputs:**
```bash
python -c "
import geopandas as gpd, pandas as pd
gdf = gpd.read_file('outputs/polygons/change_results.geojson')
df = pd.read_csv('outputs/predictions/change_features.csv')
print('GeoJSON:', gdf.shape, 'CRS:', gdf.crs)
print('CSV:', df.shape)
print('Columns:', list(df.columns))
"
```

---

## 7. Demo Day Checklist

**Before the demo:**
- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` completed without errors
- [ ] BEFORE and AFTER band files in correct folders
- [ ] `python run_pipeline.py` runs without errors
- [ ] `outputs/maps/change_magnitude.tif` exists and readable
- [ ] `outputs/maps/change_mask.tif` exists and readable
- [ ] `python run_vectorize.py` runs without errors
- [ ] `outputs/polygons/change_results.geojson` opens correctly in QGIS
- [ ] `outputs/predictions/change_features.csv` has correct 16 columns
- [ ] Person 3 ML model runs on change_features.csv
- [ ] Rehearsed 5-minute demo walkthrough

**During demo:**
1. Show `data/sentinel/before/` and `data/sentinel/after/` (raw input)
2. Run `python run_pipeline.py` (live or cached)
3. Run `python run_vectorize.py` (live or cached)
4. Open `change_results.geojson` in QGIS — show polygons on map
5. Open attribute table — show feature values per polygon
6. Show `change_features.csv` — explain ML handoff

---

## 8. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: rasterio` | Not installed | `pip install rasterio` or use conda |
| `ModuleNotFoundError: geopandas` | Not installed | `pip install geopandas` or use conda |
| `FileNotFoundError: B02` | Bands not in folder | Check file naming pattern (*B02*.jp2) |
| `All pixels masked` | Cloud-covered scene | Choose a clearer date |
| `GDAL_DATA not found` | Environment issue | `conda install gdal` or set GDAL_DATA |
| `No polygons found` | Mask all zeros or area filter too large | Check change_mask.tif; try `--min-area 100` |
| `KeyError: latitude` | Feature extraction failed | Check B04/B08 band files exist in before/after |
| GeoJSON not in QGIS | Wrong CRS | Confirm output CRS is EPSG:4326 |
