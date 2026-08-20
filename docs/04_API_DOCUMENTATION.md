# 04 — API DOCUMENTATION

> **Project:** CIPHER-X  
> **Scope:** Internal Python API — all public functions across Person 1, Person 2, and Person 3 modules  
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

**Returns:** `Path` - absolute path to the matched file  
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
- `bands` - `np.ndarray` shape `(4, H, W)`, dtype `float32`, range `[0.0, 1.0]`  
  Band order: `[B02, B03, B04, B08]`
- `scl` - `np.ndarray` shape `(H, W)`, dtype `uint8`, SCL class values `[0-11]`  
  Resampled to match band resolution (nearest neighbour)
- `profile` - `dict` - rasterio profile for saving outputs (CRS, transform, width, height)

**Notes:**
- DN values divided by `10000` for reflectance
- SCL is NOT divided - integer class values preserved
- If SCL not found: returns `None` for `scl`, logs a warning

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
| `src_array` | `np.ndarray` | Source array `(bands, H, W)` or `(H, W)` |
| `src_profile` | `dict` | Rasterio profile of `src_array` |
| `ref_profile` | `dict` | Rasterio profile of the reference (target grid) |
| `resampling` | `str` | `'bilinear'` for bands, `'nearest'` for SCL |

**Returns:** `np.ndarray` - reprojected array matching `ref_profile` shape

---

### `align_images(before_bands, before_scl, before_profile, after_bands, after_scl, after_profile)`

Align AFTER image to BEFORE image grid. BEFORE is the reference.

```python
def align_images(
    before_bands: np.ndarray, before_scl: np.ndarray, before_profile: dict,
    after_bands:  np.ndarray, after_scl:  np.ndarray, after_profile:  dict
) -> tuple[np.ndarray, np.ndarray]
```

**Returns:** `(aligned_after_bands, aligned_after_scl)` - same grid as BEFORE

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

**Returns:** `np.ndarray` bool, shape `(H, W)` - `True` = valid pixel, `False` = masked

---

### `combine_masks(before_mask, after_mask)`

Combine BEFORE and AFTER masks: pixel valid only if valid in BOTH images.

```python
def combine_masks(before_mask: np.ndarray, after_mask: np.ndarray) -> np.ndarray
```

**Returns:** `np.ndarray` bool - `True` = valid in both images

---

### `apply_mask(bands_array, valid_mask)`

Set masked pixels to `NaN` in a float32 band array.

```python
def apply_mask(bands_array: np.ndarray, valid_mask: np.ndarray) -> np.ndarray
```

**Returns:** `np.ndarray` float32 - same shape as `bands_array`, NaN where invalid

---

## 4. Module: `src.cva.compute` (Person 1)

### `compute_delta(before_bands, after_bands, valid_mask)`

Compute per-pixel spectral difference for each band.

```python
def compute_delta(
    before_bands: np.ndarray,  # (4, H, W)
    after_bands:  np.ndarray,  # (4, H, W)
    valid_mask:   np.ndarray   # (H, W) bool
) -> np.ndarray                # (4, H, W) float32
```

**Returns:** `delta` - `after - before`, NaN where `valid_mask` is False

---

### `compute_magnitude(delta_array)`

Compute L2 norm of spectral delta across all bands.

```python
def compute_magnitude(delta_array: np.ndarray) -> np.ndarray
```

**Formula:** `M = sqrt(sum(delta[b]^2 for b in bands))`  
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

## 5. Module: `src.cva.threshold` (Person 1)

### `otsu_threshold(magnitude_array)`

Compute Otsu threshold on valid (non-NaN) pixels.

```python
def otsu_threshold(magnitude_array: np.ndarray) -> float
```

**Returns:** `float` - threshold value

---

### `apply_threshold(magnitude_array, threshold)`

Apply threshold to produce binary change mask.

```python
def apply_threshold(magnitude_array: np.ndarray, threshold: float) -> np.ndarray
```

**Returns:** `np.ndarray` bool `(H, W)` - `True` where `magnitude > threshold` AND valid

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

**Returns:** `np.ndarray` bool - cleaned binary mask

---

### `save_change_mask(mask, profile, output_path)`

Write binary mask as uint8 GeoTIFF (0/1).

```python
def save_change_mask(mask: np.ndarray, profile: dict, output_path: Path) -> None
```

---

## 6. Top-Level Runner: `run_pipeline.py` (Person 1)

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
| 2 | All pixels cloud-masked - no valid data |
| 3 | Unexpected error |

---

## 7. Module: `src.vectorization.polygonize` (Person 2)

### `load_and_clean_mask(mask_path, open_size)`

Load binary change mask raster and apply morphological opening to remove noise.

```python
def load_and_clean_mask(
    mask_path: Path,
    open_size: int = 3
) -> tuple[np.ndarray, dict]
```

| Parameter | Type | Description |
|---|---|---|
| `mask_path` | `Path` | Path to `outputs/maps/change_mask.tif` |
| `open_size` | `int` | Kernel size for morphological opening (default 3) |

**Returns:**
- `cleaned_mask` - `np.ndarray` uint8 `(H, W)`, values 0 or 1, noise removed
- `profile` - `dict` - rasterio profile (CRS, transform, shape)

---

### `polygonize_mask(mask, profile, min_area_m2)`

Convert binary change mask into a GeoDataFrame of change polygons.

```python
def polygonize_mask(
    mask: np.ndarray,
    profile: dict,
    min_area_m2: float = 1000.0
) -> gpd.GeoDataFrame
```

| Parameter | Type | Description |
|---|---|---|
| `mask` | `np.ndarray` | Cleaned binary mask `(H, W)` |
| `profile` | `dict` | Rasterio profile from the mask raster |
| `min_area_m2` | `float` | Minimum polygon area to keep (default 1000 m2) |

**Returns:** `gpd.GeoDataFrame` with columns:
- `id` - int, sequential identifier
- `geometry` - Polygon geometry (CRS from mask)
- `area_m2` - float, polygon area in square metres
- `latitude` - float, centroid latitude (EPSG:4326)
- `longitude` - float, centroid longitude (EPSG:4326)

---

## 8. Module: `src.features.ndvi` (Person 2)

### `compute_ndvi(band_folder, profile_ref)`

Load B04 and B08 from a Sentinel-2 band folder and compute NDVI aligned to the reference grid.

```python
def compute_ndvi(
    band_folder: Path,
    profile_ref: dict
) -> np.ndarray
```

| Parameter | Type | Description |
|---|---|---|
| `band_folder` | `Path` | Folder containing B04 and B08 band files |
| `profile_ref` | `dict` | Reference rasterio profile to align NDVI to (change mask grid) |

**Returns:** `np.ndarray` float32 `(H, W)` - NDVI values in range [-1, 1]. NaN where B08+B04==0 or bands not found.

---

## 9. Module: `src.features.extractor` (Person 2)

### `extract_features(gdf, magnitude_path, magnitude_profile, spectral_delta_path, spectral_delta_profile, ndvi_before, ndvi_after)`

Enrich a GeoDataFrame of change polygons with raster-sampled and computed features.

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

**Returns:** `pd.DataFrame` with all 16 feature columns.

---

## 10. Top-Level Runner: `run_vectorize.py` (Person 2)

### CLI Usage

```bash
python run_vectorize.py [--min-area FLOAT]
```

| Argument | Default | Description |
|---|---|---|
| `--min-area` | `1000.0` | Minimum polygon area in m2 to keep |

---

## 11. Module: `src.models.labeller` (Person 3)

### `auto_label(df)`

Apply domain heuristic rules to generate provisional training labels from polygon features.

```python
def auto_label(df: pd.DataFrame) -> pd.DataFrame
```

| Parameter | Type | Description |
|---|---|---|
| `df` | `pd.DataFrame` | Feature table (16 columns) from Person 2 |

**Returns:** `pd.DataFrame` with added columns:
- `label` (`int` 0-4)
- `label_name` (`str` e.g., "Vegetation Clearing", "New Construction")
- `label_source` (`str` default: `'auto_rule'`)

---

## 12. Module: `src.models.classifier` (Person 3)

### `load_training_data(labels_path)`

Load labelled CSV, impute missing values with median strategy, and extract feature matrix $X$ and labels $y$.

```python
def load_training_data(
    labels_path: Path
) -> tuple[np.ndarray, np.ndarray, SimpleImputer, list[str]]
```

**Returns:** `(X, y, imputer, feature_names)`

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

**Returns:** `(clf, metrics_dict)` containing accuracy, classification report, and confusion matrix.

---

### `save_artifacts(clf, imputer, metadata, output_dir)`

Save trained model, imputer, and metadata JSON to disk.

```python
def save_artifacts(
    clf: RandomForestClassifier,
    imputer: SimpleImputer,
    metadata: dict,
    output_dir: Path
) -> None
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

## 13. Top-Level Runner: `run_classify.py` (Person 3)

### CLI Usage

```bash
python run_classify.py [--features PATH] [--labels PATH] [--output PATH]
```

| Argument | Default | Description |
|---|---|---|
| `--features` | `outputs/predictions/change_features.csv` | Input features from Person 2 |
| `--labels` | `data/labels/prototype_labels.csv` | Labelled dataset for training |
| `--output` | `outputs/predictions/predictions.csv` | Output predictions for Person 4 |

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Features input missing (run `run_vectorize.py` first) |
| 2 | Model training or inference error |
| 3 | Unexpected error |
