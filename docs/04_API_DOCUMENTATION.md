# 04 — API DOCUMENTATION

> **Project:** CIPHER-X  
> **Scope:** Internal Python API — all public functions in Person 1 modules  
> **Last Updated:** 2026-08-20

---

## 1. Module: `src.preprocessing.loader`

### `find_band_file(folder, band_name)`

Locate a specific Sentinel-2 band file inside a folder.

```python
def find_band_file(folder: Path, band_name: str) -> Path
```

| Parameter | Type | Description |
|---|---|---|
| `folder` | `Path` | Directory to search (e.g., `data/sentinel/before/`) |
| `band_name` | `str` | Band identifier: `"B02"`, `"B03"`, `"B04"`, `"B08"`, `"SCL"` |

**Returns:** `Path` — absolute path to the matched file  
**Raises:** `FileNotFoundError` if no matching file is found

**Glob pattern used:** `*{band_name}*.jp2` then `*{band_name}*.tif`

---

### `load_bands(folder)`

Load Sentinel-2 B02, B03, B04, B08 and SCL from a folder. Scales reflectance bands to [0, 1].

```python
def load_bands(folder: Path) -> tuple[np.ndarray, np.ndarray, dict]
```

| Parameter | Type | Description |
|---|---|---|
| `folder` | `Path` | Band files directory |

**Returns:**
- `bands` — `np.ndarray` shape `(4, H, W)`, dtype `float32`, range `[0.0, 1.0]`  
  Band order: `[B02, B03, B04, B08]`
- `scl` — `np.ndarray` shape `(H, W)`, dtype `uint8`, SCL class values `[0–11]`  
  Resampled to match band resolution (nearest neighbour)
- `profile` — `dict` — rasterio profile for saving outputs (CRS, transform, width, height)

**Notes:**
- DN values divided by `10000` for reflectance
- SCL is NOT divided — integer class values preserved
- If SCL not found: returns `None` for `scl`, logs a warning

---

## 2. Module: `src.preprocessing.align`

### `align_to_reference(src_array, src_profile, ref_profile, resampling)`

Reproject and resample `src_array` to match `ref_profile`'s CRS, transform, and shape.

```python
def align_to_reference(
    src_array: np.ndarray,
    src_profile: dict,
    ref_profile: dict,
    resampling: str = 'bilinear'
) -> np.ndarray
```

| Parameter | Type | Description |
|---|---|---|
| `src_array` | `np.ndarray` | Source array `(bands, H, W)` or `(H, W)` |
| `src_profile` | `dict` | Rasterio profile of `src_array` |
| `ref_profile` | `dict` | Rasterio profile of the reference (target grid) |
| `resampling` | `str` | `'bilinear'` for bands, `'nearest'` for SCL |

**Returns:** `np.ndarray` — reprojected array matching `ref_profile` shape

---

### `align_images(before_bands, before_scl, before_profile, after_bands, after_scl, after_profile)`

Align AFTER image to BEFORE image grid. BEFORE is the reference.

```python
def align_images(
    before_bands: np.ndarray, before_scl: np.ndarray, before_profile: dict,
    after_bands:  np.ndarray, after_scl:  np.ndarray, after_profile:  dict
) -> tuple[np.ndarray, np.ndarray]
```

**Returns:** `(aligned_after_bands, aligned_after_scl)` — same grid as BEFORE

---

## 3. Module: `src.preprocessing.masking`

### `scl_to_mask(scl_array, mask_classes)`

Convert an SCL array into a boolean validity mask.

```python
def scl_to_mask(
    scl_array: np.ndarray,
    mask_classes: list[int] = [0, 1, 3, 8, 9, 10]
) -> np.ndarray
```

**Returns:** `np.ndarray` bool, shape `(H, W)` — `True` = valid pixel, `False` = masked

---

### `combine_masks(before_mask, after_mask)`

Combine BEFORE and AFTER masks: pixel valid only if valid in BOTH images.

```python
def combine_masks(before_mask: np.ndarray, after_mask: np.ndarray) -> np.ndarray
```

**Returns:** `np.ndarray` bool — `True` = valid in both images

---

### `apply_mask(bands_array, valid_mask)`

Set masked pixels to `NaN` in a float32 band array.

```python
def apply_mask(bands_array: np.ndarray, valid_mask: np.ndarray) -> np.ndarray
```

**Returns:** `np.ndarray` float32 — same shape as `bands_array`, NaN where invalid

---

## 4. Module: `src.cva.compute`

### `compute_delta(before_bands, after_bands, valid_mask)`

Compute per-pixel spectral difference for each band.

```python
def compute_delta(
    before_bands: np.ndarray,  # (4, H, W)
    after_bands:  np.ndarray,  # (4, H, W)
    valid_mask:   np.ndarray   # (H, W) bool
) -> np.ndarray                # (4, H, W) float32
```

**Returns:** `delta` — `after - before`, NaN where `valid_mask` is False

---

### `compute_magnitude(delta_array)`

Compute L2 norm of spectral delta across all bands.

```python
def compute_magnitude(delta_array: np.ndarray) -> np.ndarray
```

**Formula:** `M = sqrt(sum(delta[b]² for b in bands))`  
**Returns:** `np.ndarray` shape `(H, W)`, float32

---

### `save_raster(array, profile, output_path)`

Write a numpy array to GeoTIFF.

```python
def save_raster(
    array: np.ndarray,
    profile: dict,
    output_path: Path
) -> None
```

Automatically handles 2D `(H, W)` and 3D `(bands, H, W)` arrays.

---

## 5. Module: `src.cva.threshold`

### `otsu_threshold(magnitude_array)`

Compute Otsu threshold on valid (non-NaN) pixels.

```python
def otsu_threshold(magnitude_array: np.ndarray) -> float
```

**Returns:** `float` — threshold value

---

### `apply_threshold(magnitude_array, threshold)`

Apply threshold to produce binary change mask.

```python
def apply_threshold(magnitude_array: np.ndarray, threshold: float) -> np.ndarray
```

**Returns:** `np.ndarray` bool `(H, W)` — `True` where `magnitude > threshold` AND valid

---

### `clean_mask(binary_mask, open_size, close_size)`

Apply morphological opening then closing to remove noise.

```python
def clean_mask(
    binary_mask: np.ndarray,
    open_size:   int = 3,
    close_size:  int = 3
) -> np.ndarray
```

**Returns:** `np.ndarray` bool — cleaned binary mask

---

### `save_change_mask(mask, profile, output_path)`

Write binary mask as uint8 GeoTIFF (0/1).

```python
def save_change_mask(mask: np.ndarray, profile: dict, output_path: Path) -> None
```

---

## 6. Top-Level Runner: `run_pipeline.py`

### CLI Usage

```bash
python run_pipeline.py [--before PATH] [--after PATH] [--output PATH]
```

| Argument | Default | Description |
|---|---|---|
| `--before` | `data/sentinel/before` | BEFORE bands folder |
| `--after` | `data/sentinel/after` | AFTER bands folder |
| `--output` | `outputs/maps` | Output folder for maps |

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Input data missing or unreadable |
| 2 | All pixels cloud-masked — no valid data |
| 3 | Unexpected error |
