# Preprocessing — Sentinel-2 Data Pipeline

Handles data loading, CRS/grid alignment, and cloud/shadow masking for Sentinel-2 L2A imagery.

## Modules

### `loader.py` — Band Loader

Reads Sentinel-2 band files (B02, B03, B04, B08, SCL) from a folder and returns numpy arrays.

```python
from src.preprocessing.loader import load_bands
from pathlib import Path

bands, scl, profile = load_bands(Path("data/sentinel/before"))
# bands: (4, H, W) float32 [0.0–1.0] — order: [B02, B03, B04, B08]
# scl:   (H, W)    uint8   [0–11]
# profile: dict    rasterio profile
```

**Key details:**
- Reflectance scaling: DN ÷ 10000
- SCL resampled to 10m via nearest neighbour if needed
- Glob patterns: `*B02*.jp2`, `*B02*.tif`, etc.

### `align.py` — Image Alignment

Ensures BEFORE and AFTER arrays are on the exact same CRS, grid, and extent using `rasterio.warp.reproject`.

```python
from src.preprocessing.align import align_images

after_bands, after_scl = align_images(
    before_bands, before_scl, before_profile,
    after_bands, after_scl, after_profile,
)
```

**Resampling:**
- Bands → bilinear (smooth continuous values)
- SCL → nearest neighbour (preserve class integers)

### `masking.py` — Cloud/Shadow Masking

Builds boolean validity masks from the SCL band. Invalid classes: 0 (no data), 1 (defective), 3 (cloud shadow), 8 (cloud medium), 9 (cloud high), 10 (cirrus).

```python
from src.preprocessing.masking import scl_to_mask, combine_masks, apply_mask

valid = scl_to_mask(scl)              # True = valid
combined = combine_masks(b1, b2)      # True where BOTH valid
masked = apply_mask(bands, combined)  # NaN where invalid
```

**Fallback:** If SCL not found → warning logged, all pixels treated as valid.

## Output

All functions return numpy arrays and rasterio profile dicts — no files written directly by preprocessing modules.
