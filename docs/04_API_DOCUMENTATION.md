# 04 — API DOCUMENTATION

> **Project:** CIPHER-X  
> **Scope:** Internal Python API — all public functions across Person 1 and Person 2 modules  
> **Last Updated:** 2026-08-20 (updated: BUG-01 fix reflected in compute_magnitude; BUG-04 fix reflected in align_images)

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
**Glob patterns tried:** `*{band_name}*.jp2` → `*{band_name}*.tif` → `*{band_name}*.tiff`

---

### `load_bands(folder)`

Load Sentinel-2 B02, B03, B04, B08 and SCL from a folder. Scales reflectance DN to [0, 1].

```python
def load_bands(folder: Path) -> tuple[np.ndarray, np.ndarray, dict]
```

| Parameter | Type | Description |
|---|---|---|
| `folder` | `Path` | Directory containing band files |

**Returns:**
- `bands` — `np.ndarray` shape `(4, H, W)`, dtype `float32`, range `[0.0, 1.0]`  
  Band order: `[B02, B03, B04, B08]`
- `scl` — `np.ndarray` shape `(H, W)`, dtype `uint8`, SCL class values `[0–11]`  
  Resampled to match 10m band resolution via nearest-neighbour
- `profile` — `dict` — rasterio profile for saving outputs (CRS, transform, width, height, count=4, dtype=float32)

**Notes:**
- DN values divided by `10000.0` for reflectance
- SCL is NOT divided — integer class values 0–11 preserved
- If SCL not found: returns synthetic all-valid SCL (class 4), logs a warning

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
| `src_array` | `np.ndarray` | Source array `(bands, H, W)` |
| `src_profile` | `dict` | Rasterio profile matching `src_array` (CRS, transform, count) |
| `ref_profile` | `dict` | Rasterio profile of the reference (target grid) |
| `resampling` | `str` | `'bilinear'` for continuous bands, `'nearest'` for SCL integer classes |

**Returns:** `np.ndarray` — reprojected array with same spatial extent and shape as `ref_profile`

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

**Short-circuit:** If CRS, transform, and shape already match, returns AFTER arrays unchanged (no reprojection).

> **BUG-04 fix (2026-08-20):** SCL is now aligned using a dedicated 1-band `scl_profile` (`count=1, dtype=uint8`)
> instead of reusing `after_profile` which has `count=4`. This ensures profile metadata accurately
> reflects the single SCL band being reprojected.

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

**Default masked classes:** 0 (no data), 1 (saturated), 3 (cloud shadow), 8 (cloud medium), 9 (cloud high), 10 (thin cirrus)

**Returns:** `np.ndarray` bool, shape `(H, W)` — `True` = valid pixel, `False` = masked

---

### `combine_masks(before_mask, after_mask)`

Combine BEFORE and AFTER masks — pixel valid only if valid in BOTH images.

```python
def combine_masks(before_mask: np.ndarray, after_mask: np.ndarray) -> np.ndarray
```

**Returns:** `np.ndarray` bool — logical AND of both masks

---

### `apply_mask(bands_array, valid_mask)`

Set masked pixels to `NaN` in a float32 band array.

```python
def apply_mask(bands_array: np.ndarray, valid_mask: np.ndarray) -> np.ndarray
```

**Returns:** `np.ndarray` float32 — same shape as `bands_array`, NaN where `valid_mask` is False

---

## 4. Module: `src.cva.compute`

### `compute_delta(before_bands, after_bands, valid_mask)`

Compute per-pixel spectral difference for each band.

```python
def compute_delta(
    before_bands: np.ndarray,  # (4, H, W) float32
    after_bands:  np.ndarray,  # (4, H, W) float32
    valid_mask:   np.ndarray   # (H, W) bool
) -> np.ndarray                # (4, H, W) float32
```

**Returns:** `delta = after - before`, NaN where `valid_mask` is False

---

### `compute_magnitude(delta_array)`

Compute L2 norm of spectral delta across all bands.

```python
def compute_magnitude(delta_array: np.ndarray) -> np.ndarray
```

**Formula:** `M = sqrt(ΔB02² + ΔB03² + ΔB04² + ΔB08²)`

**Returns:** `np.ndarray` shape `(H, W)`, float32

> **BUG-01 fix (2026-08-20):** `np.nansum` returns 0 (not NaN) when all input values are NaN —
> this caused cloud-masked pixels to appear as magnitude=0 instead of NaN, skewing the Otsu
> threshold. Fix: after computing `nansum`, a mask of all-NaN pixels is detected via
> `np.all(np.isnan(delta_array), axis=0)` and those positions are explicitly set to `np.nan`.

---

### `save_raster(array, profile, output_path)`

Write a numpy array to GeoTIFF with correct CRS and transform.

```python
def save_raster(
    array: np.ndarray,
    profile: dict,
    output_path: str | Path
) -> None
```

Handles 2D `(H, W)` and 3D `(bands, H, W)` arrays automatically.  
Always writes with `compress='deflate'` and appropriate `nodata` (NaN for float, 0 for int).

---

## 5. Module: `src.cva.threshold`

### `otsu_threshold(magnitude_array)`

Compute Otsu threshold on valid (non-NaN) pixels.

```python
def otsu_threshold(magnitude_array: np.ndarray) -> float
```

**Returns:** `float` — threshold value (via `skimage.filters.threshold_otsu`)  
**Raises:** `ValueError` if all pixels are NaN (no valid data at all)

---

### `apply_threshold(magnitude_array, threshold)`

Apply threshold to produce binary change mask.

```python
def apply_threshold(magnitude_array: np.ndarray, threshold: float) -> np.ndarray
```

**Returns:** `np.ndarray` bool `(H, W)` — `True` where `magnitude > threshold` AND not NaN

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

**Steps:** `binary_opening(open_size iterations)` → `binary_closing(close_size iterations)`  
**Returns:** `np.ndarray` uint8 — cleaned binary mask (0 or 1)

---

### `save_change_mask(mask, profile, output_path)`

Write binary mask as uint8 GeoTIFF (0=no change, 1=change).

```python
def save_change_mask(mask: np.ndarray, profile: dict, output_path: str | Path) -> None
```

Writes with `dtype=uint8`, `nodata=0`, `compress=deflate`.

---

## 6. Module: `src.vectorization.polygonize`

### `load_and_clean_mask(mask_path, open_size)`

Load binary change mask from disk and apply morphological opening.

```python
def load_and_clean_mask(mask_path: str, open_size: int = 3) -> tuple[np.ndarray, dict]
```

**Returns:** `(cleaned_mask, profile)` — uint8 mask + rasterio profile

---

### `polygonize_mask(mask, profile, min_area_m2)`

Convert binary mask to GeoDataFrame of change polygons.

```python
def polygonize_mask(
    mask: np.ndarray,
    profile: dict,
    min_area_m2: float = 1000.0
) -> gpd.GeoDataFrame
```

**Steps:** `rasterio.features.shapes()` → filter by area → repair geometry → add lat/lon centroid → reproject to EPSG:4326

**Returns:** `GeoDataFrame` with columns: `id, geometry, area_m2, latitude, longitude` (CRS: EPSG:4326)  
**Returns empty GDF** (not error) if no polygons pass the area filter.

---

## 7. Module: `src.features.ndvi`

### `compute_ndvi(band_folder, profile_ref)`

Compute NDVI from B04 (Red) and B08 (NIR) in a folder.

```python
def compute_ndvi(band_folder: Path, profile_ref: dict) -> np.ndarray
```

**Formula:** `NDVI = (B08 - B04) / (B08 + B04)` — NaN where denominator is 0  
**Returns:** `np.ndarray` shape `(H, W)`, float32, range `[-1, 1]`, NaN where invalid  
**Fallback:** Returns all-NaN array with a warning if B04 or B08 not found.

---

## 8. Module: `src.features.extractor`

### `extract_features(gdf, magnitude_path, magnitude_profile, spectral_delta_path, spectral_delta_profile, ndvi_before, ndvi_after)`

Extract 16 features per polygon from raster layers.

```python
def extract_features(
    gdf: gpd.GeoDataFrame,
    magnitude_path: str, magnitude_profile: dict,
    spectral_delta_path: str, spectral_delta_profile: dict,
    ndvi_before: np.ndarray,
    ndvi_after: np.ndarray
) -> pd.DataFrame
```

**Output columns (16 total):**

| Column | Description |
|---|---|
| `id` | Sequential polygon ID |
| `area_m2` | Polygon area in square metres |
| `latitude` | Centroid latitude (WGS84) |
| `longitude` | Centroid longitude (WGS84) |
| `cva_mean` | Mean CVA magnitude inside polygon |
| `cva_max` | Max CVA magnitude inside polygon |
| `ndvi_before` | Mean NDVI before change |
| `ndvi_after` | Mean NDVI after change |
| `delta_ndvi` | `ndvi_after - ndvi_before` |
| `delta_b02` | Mean ΔB02 (Blue) inside polygon |
| `delta_b03` | Mean ΔB03 (Green) inside polygon |
| `delta_b04` | Mean ΔB04 (Red) inside polygon |
| `delta_b08` | Mean ΔB08 (NIR) inside polygon |
| `bbox_width_m` | Bounding box width (metres) |
| `bbox_height_m` | Bounding box height (metres) |
| `compactness` | 4π·area/perimeter² (1=perfect circle, 0=very elongated) |

---

## 9. Top-Level Runners

### `run_pipeline.py` — Person 1 pipeline

```bash
python run_pipeline.py [--before PATH] [--after PATH]
```

| Arg | Default | Description |
|---|---|---|
| `--before` | `data/sentinel/before` | BEFORE bands folder |
| `--after` | `data/sentinel/after` | AFTER bands folder |

Exit codes: `0`=success, `1`=data missing or all-cloud, `3`=unexpected error

### `run_vectorize.py` — Person 2 pipeline

```bash
python run_vectorize.py [--min-area FLOAT]
```

| Arg | Default | Description |
|---|---|---|
| `--min-area` | `1000.0` | Minimum polygon area in m² |

Exit codes: `0`=success, `1`=Person 1 outputs missing or no polygons found
