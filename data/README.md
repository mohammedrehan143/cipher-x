# Data

Raw and processed datasets for CIPHER-X.

## Structure

```
data/
├── sentinel/
│   ├── before/          ← Drop BEFORE S2 band files here (B02, B03, B04, B08, SCL)
│   └── after/           ← Drop AFTER S2 band files here
├── aoi/                 ← Optional AOI GeoJSON boundary
└── processed/           ← Intermediate rasters (spectral_delta.tif)
```

## Sentinel-2 Band Files

Expected naming patterns (auto-matched by glob):
- `*B02*.jp2` / `*B02*.tif` — Blue (10m)
- `*B03*.jp2` / `*B03*.tif` — Green (10m)
- `*B04*.jp2` / `*B04*.tif` — Red (10m)
- `*B08*.jp2` / `*B08*.tif` — NIR (10m)
- `*SCL*.jp2` / `*SCL*.tif` — Scene Classification (20m, resampled to 10m)

## How to Get Sentinel-2 Data (Free)

1. **Copernicus Browser**: https://browser.dataspace.copernicus.eu/
2. **Sentinel Hub EO Browser**: https://apps.sentinel-hub.com/eo-browser/

Download L2A product, extract band files from `GRANULE/<tile>/IMG_DATA/`.

> **Note:** Do not commit large raster files to Git. Use `.gitignore` or external storage.
