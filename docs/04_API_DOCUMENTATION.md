# 04 — API DOCUMENTATION

> **Project:** CIPHER-X  
> **Scope:** Internal Python API — all public functions across Person 1, Person 2, Person 3, and Person 4 modules  
> **Last Updated:** 2026-08-20  

---

## 1. Module: `src.preprocessing.loader` (Person 1)

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

## 2. Module: `src.preprocessing.align` (Person 1)

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

---

## 3. Module: `src.preprocessing.masking` (Person 1)

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

## 4. Module: `src.cva.compute` (Person 1)

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

**Formula:** $M = \sqrt{\Delta B02^2 + \Delta B03^2 + \Delta B04^2 + \Delta B08^2}$  
**Returns:** `np.ndarray` shape `(H, W)`, float32

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

---

## 5. Module: `src.cva.threshold` (Person 1)

### `otsu_threshold(magnitude_array)`

Compute Otsu threshold on valid (non-NaN) pixels.

```python
def otsu_threshold(magnitude_array: np.ndarray) -> float
```

**Returns:** `float` — threshold value via `skimage.filters.threshold_otsu`

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

**Returns:** `np.ndarray` uint8 — cleaned binary mask (0 or 1)

---

### `save_change_mask(mask, profile, output_path)`

Write binary mask as uint8 GeoTIFF (0=no change, 1=change).

```python
def save_change_mask(mask: np.ndarray, profile: dict, output_path: str | Path) -> None
```

---

## 6. Module: `src.vectorization.polygonize` (Person 2)

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

**Returns:** `gpd.GeoDataFrame` with columns:
- `id` - int, sequential identifier
- `geometry` - Polygon geometry (CRS from mask)
- `area_m2` - float, polygon area in square metres
- `latitude` - float, centroid latitude (EPSG:4326)
- `longitude` - float, centroid longitude (EPSG:4326)

---

## 7. Module: `src.features.ndvi` (Person 2)

### `compute_ndvi(band_folder, profile_ref)`

Compute NDVI from B04 (Red) and B08 (NIR) in a folder.

```python
def compute_ndvi(band_folder: Path, profile_ref: dict) -> np.ndarray
```

**Returns:** `np.ndarray` float32 `(H, W)` - NDVI values in range [-1, 1]. NaN where B08+B04==0 or bands not found.

---

## 8. Module: `src.features.extractor` (Person 2)

### `extract_features(gdf, magnitude_path, magnitude_profile, spectral_delta_path, spectral_delta_profile, ndvi_before, ndvi_after)`

Extract 16 features per polygon from raster layers.

```python
def extract_features(
    gdf: gpd.GeoDataFrame,
    magnitude_path: str,
    magnitude_profile: dict,
    spectral_delta_path: str,
    spectral_delta_profile: dict,
    ndvi_before: np.ndarray,
    ndvi_after: np.ndarray,
) -> pd.DataFrame
```

**Returns:** `pd.DataFrame` with all 16 feature columns:
`id`, `area_m2`, `latitude`, `longitude`, `cva_mean`, `cva_max`, `ndvi_before`, `ndvi_after`, `delta_ndvi`, `delta_b02`, `delta_b03`, `delta_b04`, `delta_b08`, `bbox_width_m`, `bbox_height_m`, `compactness`.

---

## 9. Module: `src.models.labeller` (Person 3)

### `auto_label(df)`

Apply domain heuristic rules to generate provisional training labels from polygon features.

```python
def auto_label(df: pd.DataFrame) -> pd.DataFrame
```

**Returns:** `pd.DataFrame` with added columns: `label` (0-4), `label_name`, `label_source`.

---

## 10. Module: `src.models.classifier` (Person 3)

### `load_training_data(labels_path)`

Load labelled CSV, impute missing values with median strategy, and extract feature matrix $X$ and labels $y$.

```python
def load_training_data(
    labels_path: Path
) -> tuple[np.ndarray, np.ndarray, SimpleImputer, list[str]]
```

---

### `train_model(X, y, feature_names)`

Train a balanced `RandomForestClassifier` with train/validation evaluation.

```python
def train_model(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str]
) -> tuple[RandomForestClassifier, dict]
```

---

### `predict_features(clf, imputer, df)`

Run batch inference on feature table to predict change class and confidence score.

```python
def predict_features(
    clf: RandomForestClassifier,
    imputer: SimpleImputer,
    df: pd.DataFrame
) -> pd.DataFrame
```

**Returns:** `pd.DataFrame` containing `id`, `predicted_class`, `predicted_label`, `confidence`, plus pass-through attributes.

---

## 11. Top-Level CLI Runners

- **Person 1:** `python run_pipeline.py [--before PATH] [--after PATH]`
- **Person 2:** `python run_vectorize.py [--min-area FLOAT]`
- **Person 3:** `python run_classify.py [--features PATH] [--labels PATH] [--output PATH]`
- **Person 4:** `streamlit run app/main.py`
