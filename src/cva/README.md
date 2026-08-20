# CVA — Change Vector Analysis

Computes per-pixel spectral change between aligned BEFORE and AFTER Sentinel-2 images, then thresholds the result into a binary change mask.

## Modules

### `compute.py` — Spectral Delta & Magnitude

```python
from src.cva.compute import compute_delta, compute_magnitude, save_raster

delta = compute_delta(before_masked, after_masked, valid_mask)
# delta: (4, H, W) float32 — per-band difference, NaN where invalid

magnitude = compute_magnitude(delta)
# magnitude: (H, W) float32 — Euclidean distance across bands

save_raster(magnitude, profile, "outputs/maps/change_magnitude.tif")
```

**Formulas:**
- `delta[b] = after[b] - before[b]` for b in [B02, B03, B04, B08]
- `M = sqrt(delta_B02² + delta_B03² + delta_B04² + delta_B08²)`

### `threshold.py` — Otsu Thresholding & Morphological Cleanup

```python
from src.cva.threshold import otsu_threshold, apply_threshold, clean_mask, save_change_mask

threshold = otsu_threshold(magnitude)        # automatic threshold
binary = apply_threshold(magnitude, threshold)  # bool array
cleaned = clean_mask(binary)                   # open → close, 3×3
save_change_mask(cleaned, profile, "outputs/maps/change_mask.tif")
```

**Steps:**
1. Otsu threshold on valid (non-NaN) pixels
2. Binary thresholding: `magnitude > threshold`
3. Morphological opening (removes salt noise)
4. Morphological closing (fills holes)
5. Cloud-masked pixels set to 0

## Outputs

| File | Format | Description |
|---|---|---|
| `data/processed/spectral_delta.tif` | GeoTIFF float32, 4 bands | [ΔB02, ΔB03, ΔB04, ΔB08] |
| `outputs/maps/change_magnitude.tif` | GeoTIFF float32, 1 band | Continuous magnitude |
| `outputs/maps/change_mask.tif` | GeoTIFF uint8, 1 band | Binary 0/1 |
