# CIPHER-X

Satellite-based change detection system for the SIH 2026 Space-Tech MVP.

## MVP Pipeline

Sentinel-2 BEFORE/AFTER → Preprocessing → Change Vector Analysis (CVA) → Change Mask → Polygons / Features → Random Forest → GeoJSON / GIS → Streamlit Dashboard

## Project Structure

```
cipher-x/
├── src/
│   ├── preprocessing/
│   │   ├── loader.py      — Read S2 bands
│   │   ├── align.py       — CRS/grid alignment
│   │   └── masking.py     — SCL cloud masking
│   └── cva/
│       ├── compute.py     — CVA delta + magnitude
│       └── threshold.py   — Otsu + morphological cleanup
├── data/
│   ├── sentinel/before/   — BEFORE S2 band files
│   ├── sentinel/after/    — AFTER S2 band files
│   ├── aoi/               — Optional AOI GeoJSON
│   └── processed/         — Intermediate rasters
├── outputs/
│   ├── maps/              — change_magnitude.tif, change_mask.tif
│   ├── polygons/          — For Person 2
│   └── predictions/       — For Person 2
├── run_pipeline.py        — End-to-end runner
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
# Place S2 band files in data/sentinel/before/ and data/sentinel/after/
python run_pipeline.py

# Or with custom paths:
python run_pipeline.py --before data/sentinel/before --after data/sentinel/after
```

**Outputs:**
- `outputs/maps/change_magnitude.tif` — CVA magnitude (float32)
- `outputs/maps/change_mask.tif` — Binary change mask (uint8, 0/1)
- `data/processed/spectral_delta.tif` — 4-band spectral delta (float32)

## Scope

The current MVP uses Sentinel-2 imagery and a classical computer-vision / machine-learning pipeline.

- **Person 1:** Preprocessing + CVA (implemented)
- **Person 2:** Vectorization + Features + ML + Dashboard (in progress)

LISS-4 processing and Siamese CNN are postponed to a future/optional stage.

## License

See LICENSE.
