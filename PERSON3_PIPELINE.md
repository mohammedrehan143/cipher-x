# CIPHER-X — PERSON 3: ML Classification Pipeline

> **Owner:** Person 3
> **Scope:** change_features.csv -> Label creation -> Random Forest training -> Predictions -> predictions.csv
> **NOT in scope:** Preprocessing, CVA, vectorization, feature extraction, Streamlit dashboard
> **Last updated:** 2026-08-20
> **Model:** Random Forest Classifier (scikit-learn)

---

## 1. Repository Audit (as of 2026-08-20)

### What already exists (Person 3 relevant)

| Path | Type | Notes |
|---|---|---|
| `src/models/` | Directory | Has `__init__.py` stub only. Person 3 creates files here. |
| `models/` | Directory | Has `.gitkeep` only. Trained model (.joblib) goes here. |
| `outputs/predictions/` | Directory | Empty. `predictions.csv` goes here. |
| `requirements.txt` | File | numpy, pandas, scikit-learn, scikit-image, scipy, matplotlib, opencv-python, rasterio, geopandas, shapely, streamlit. **joblib** is bundled with scikit-learn so no extra dep needed. |
| `src/features/extractor.py` | File | DONE by Person 2. Defines FEATURE_COLUMNS (16 columns). |
| `src/features/ndvi.py` | File | DONE by Person 2. |
| `src/vectorization/polygonize.py` | File | DONE by Person 2. |
| `run_vectorize.py` | File | DONE by Person 2. Run this first before Person 3 starts. |

### Person 2's Guaranteed Outputs (Person 3's inputs)

Once Person 2 runs `python run_vectorize.py`, these files exist:

| File | Format | Rows | Columns |
|---|---|---|---|
| `outputs/predictions/change_features.csv` | CSV | 1 per polygon | 16 (see below) |
| `outputs/polygons/change_results.geojson` | GeoJSON | 1 per polygon | 16 + geometry |

**Exact 16 columns from Person 2:**

| Column | Type | Notes |
|---|---|---|
| id | int | Polygon ID |
| area_m2 | float | Polygon area in m2 |
| latitude | float | Centroid lat WGS84 |
| longitude | float | Centroid lon WGS84 |
| cva_mean | float | Mean CVA magnitude |
| cva_max | float | Max CVA magnitude |
| ndvi_before | float | May be NaN if bands missing |
| ndvi_after | float | May be NaN if bands missing |
| delta_ndvi | float | May be NaN if ndvi missing |
| delta_b02 | float | Mean delta Blue |
| delta_b03 | float | Mean delta Green |
| delta_b04 | float | Mean delta Red |
| delta_b08 | float | Mean delta NIR |
| bbox_width_m | float | Bounding box width |
| bbox_height_m | float | Bounding box height |
| compactness | float | Shape compactness 0-1 |

### Files in scope for Person 3 to CREATE

| Path | Phase | Purpose |
|---|---|---|
| `src/models/classifier.py` | Phase 2 | Random Forest training + inference logic |
| `src/models/labeller.py` | Phase 1 | Rule-based auto-labeller for prototype training data |
| `data/labels/prototype_labels.csv` | Phase 1 | Labelled training set (hand-editable CSV) |
| `run_classify.py` | Phase 3 | End-to-end ML pipeline runner |
| `outputs/predictions/predictions.csv` | Phase 3 output | Final predictions for Person 4 |
| `models/rf_classifier.joblib` | Phase 3 output | Saved trained model |

### Files NOT to create

- Any new raster processing code (Person 1 / Person 2 domain)
- Any Streamlit dashboard code (out of scope)
- Any deep learning / CNN code (out of scope for 24h MVP)
- Siamese network (future work only)

---

## 2. Critical Data Reality: Labels

### The problem

The CVA pipeline tells us WHERE change happened. The ML model must tell us WHAT TYPE of change it is. These are two completely different questions and CVA output alone cannot answer the second.

We CANNOT pretend the CVA output is the ground truth for classification labels.

### Practical hackathon solution

For the 24-hour MVP, use a two-track approach:

**Track A — Rule-based auto-labelling (primary for demo)**

Use domain knowledge to assign PROVISIONAL labels based on feature thresholds:

| Rule | Provisional Class |
|---|---|
| delta_ndvi < -0.2 AND area_m2 > 5000 | Vegetation Clearing |
| delta_ndvi < -0.15 AND delta_b04 > 0.05 | Vegetation Clearing |
| delta_b02 > 0.05 AND delta_b03 > 0.05 AND area_m2 > 2000 | New Construction |
| cva_mean > 0.3 AND compactness < 0.3 | Road Change / Expansion |
| cva_mean > 0.25 AND delta_b04 < -0.05 AND delta_b08 < -0.05 | Excavation / Mining |
| else | Other Human Change |

These rules are PROVISIONAL and encode reasonable domain heuristics. They are NOT ground truth — they are the starting point. A human expert should review and correct labels in `data/labels/prototype_labels.csv`.

**Track B — Manual labels (if time allows)**

Open `change_results.geojson` in QGIS alongside the actual satellite images. Inspect each polygon visually. Correct or confirm the auto-assigned labels in `prototype_labels.csv`. Even 10-20 manually verified labels improve model honesty significantly.

**Label integrity rule:** Always document whether labels are rule-based (auto) or manually verified. NEVER mix them silently.

### Target classes

| Class ID | Class Name | Spectral Signature |
|---|---|---|
| 0 | New Construction | Increase in B02/B03/B04 (bare surface/concrete), NDVI drops |
| 1 | Road Change / Expansion | Linear shape (low compactness), surface reflectance increase |
| 2 | Vegetation Clearing | Strong NDVI decrease, NIR (B08) decrease, Red (B04) increase |
| 3 | Excavation / Mining | High CVA, exposed soil, large area, irregular shape |
| 4 | Other Human Change | Does not fit the above classes |

**Important:** If the dataset is too small (<15 samples per class), merge Excavation/Mining into Other Human Change and operate with 4 classes. If still too small, use 3 classes (Construction, Vegetation Clearing, Other). Document this clearly.

---

## 3. Pipeline Flow (Person 3's responsibility)

```
outputs/predictions/change_features.csv (from Person 2)
        |
        v
[PHASE 1] labeller.py
  - Load features CSV
  - Inspect actual columns + check for NaN
  - Apply rule-based auto-labelling
  - Save: data/labels/prototype_labels.csv
  - *** HUMAN REVIEW STEP *** (edit labels manually in CSV)
        |
        v
[PHASE 2] classifier.py
  - Load prototype_labels.csv
  - Impute NaN (median strategy)
  - Select ML feature columns (exclude id/lat/lon)
  - Train/validation split (stratified 70/30 or 80/20)
  - Train RandomForestClassifier(n_estimators=100, class_weight='balanced')
  - Evaluate: accuracy, F1, confusion matrix
  - Save model: models/rf_classifier.joblib
        |
        v
[PHASE 3] run_classify.py
  - Load change_features.csv
  - Load rf_classifier.joblib
  - Impute NaN (same strategy as training)
  - Predict: predicted_class + confidence (max class probability)
  - Save: outputs/predictions/predictions.csv
        |
        v
outputs/predictions/predictions.csv (for Person 4)
```

---

## 4. Implementation Phases

---

### PHASE 0 — Environment Check

**Goal:** Confirm scikit-learn and joblib are available.

```bash
python -c "import sklearn, joblib, pandas, numpy; print('Person 3 dependencies OK')"
```

Also create `data/labels/` directory:
```bash
python -c "from pathlib import Path; Path('data/labels').mkdir(parents=True, exist_ok=True); print('data/labels/ created')"
```

**Also confirm Person 2 output exists:**
```bash
python -c "
import os, pandas as pd
f = 'outputs/predictions/change_features.csv'
assert os.path.exists(f), f'MISSING: {f} — run python run_vectorize.py first'
df = pd.read_csv(f)
print(f'Person 2 output: {len(df)} polygons, columns: {list(df.columns)}')
"
```

**Status:** PENDING — waiting for Person 2 to complete their outputs

---

### PHASE 1 — Label Creation (`src/models/labeller.py`)

**Goal:** Auto-label all polygons using domain rules. Save a CSV that can be manually corrected.

**Key function:**

```python
def auto_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply rule-based provisional labels to change polygons.

    Args:
        df: DataFrame with 16 feature columns from Person 2

    Returns:
        df with added columns:
          - label: int (0-4), class ID
          - label_name: str, human-readable class name
          - label_source: str, 'auto_rule' or 'manual'
    """
```

**Rules applied in priority order (first match wins):**

```
Rule 1 (Vegetation Clearing):
  delta_ndvi < -0.15  OR  (delta_b08 < -0.05 AND delta_b04 > 0.02)
  -> label = 2, "Vegetation Clearing"

Rule 2 (New Construction):
  delta_b02 > 0.04 AND delta_b03 > 0.04 AND delta_ndvi > -0.1
  -> label = 0, "New Construction"

Rule 3 (Road Change / Expansion):
  compactness < 0.25 AND cva_mean > 0.15
  -> label = 1, "Road Change / Expansion"

Rule 4 (Excavation / Mining):
  cva_mean > 0.28 AND area_m2 > 3000 AND compactness < 0.5
  -> label = 3, "Excavation / Mining"

Default (Other Human Change):
  -> label = 4, "Other Human Change"
```

**Output:** `data/labels/prototype_labels.csv`

Columns: id, all 16 features, label, label_name, label_source

**After running Phase 1:** Open `prototype_labels.csv` in Excel/VS Code and manually correct any labels that look wrong by changing the `label` and `label_name` columns. Change `label_source` to `'manual'` for corrected rows.

**Status:** PENDING

---

### PHASE 2 — Random Forest Classifier (`src/models/classifier.py`)

**Goal:** Train a Random Forest on the labelled data. Evaluate. Save model.

**ML feature columns used for training (13 of the 16):**

```python
ML_FEATURES = [
    "area_m2",
    "cva_mean", "cva_max",
    "ndvi_before", "ndvi_after", "delta_ndvi",
    "delta_b02", "delta_b03", "delta_b04", "delta_b08",
    "bbox_width_m", "bbox_height_m", "compactness",
]
# Excluded from ML: id, latitude, longitude (metadata, not features)
```

**Key functions:**

```python
def load_training_data(labels_path: Path) -> tuple[np.ndarray, np.ndarray, list]:
    """
    Load labelled CSV, impute NaN (median), return X, y, feature names.
    Raises ValueError if fewer than 10 labelled samples found.
    """

def train_classifier(X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    """
    Train RandomForest with balanced class weights.
    Uses 80/20 stratified split for evaluation.
    Prints accuracy, per-class F1, confusion matrix.
    Returns trained classifier fit on FULL dataset (train+val).
    """

def save_model(clf: RandomForestClassifier, path: Path) -> None:
    """Save trained model to disk using joblib."""

def load_model(path: Path) -> RandomForestClassifier:
    """Load model from disk."""

def predict(clf: RandomForestClassifier,
            df: pd.DataFrame,
            imputer: SimpleImputer) -> pd.DataFrame:
    """
    Run inference. Returns DataFrame with:
      id, predicted_class, predicted_label, confidence, all 13 ML features.
    """
```

**Classifier settings:**

```python
RandomForestClassifier(
    n_estimators=100,       # 100 trees: fast enough, good enough for MVP
    max_depth=None,         # full depth for small datasets
    class_weight='balanced',# handles class imbalance automatically
    random_state=42,        # reproducible
    n_jobs=-1,              # use all CPU cores
)
```

**NaN imputation:**

```python
from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy='median')
# Fit on training data, apply same transform on inference data
# Save imputer alongside model for consistent inference
```

**Evaluation output (printed to console):**

```
=== Random Forest Evaluation ===
Training samples: N (after 80/20 split -> train on M, eval on K)
Classes: [0, 1, 2, 3, 4]

Validation Accuracy: X.XX

Classification Report:
              precision  recall  f1-score  support
  Construction    ...
  Road Change     ...
  Veg Clearing    ...
  Excavation      ...
  Other           ...

Confusion Matrix:
[[...]]

NOTE: Dataset is small (N samples). These metrics are indicative only.
Model is retrained on 100% of data before saving.
```

**If too few samples (< 10 total or < 2 per class):**
- Merge minority classes into "Other Human Change"
- If still < 10, print warning and skip evaluation (save model trained on all data)
- Document this clearly in the console output

**Saved files:**
- `models/rf_classifier.joblib` — trained Random Forest
- `models/rf_imputer.joblib` — fitted SimpleImputer (must be saved for inference)
- `models/rf_metadata.json` — class names, feature list, training date, sample count

**Status:** PENDING

---

### PHASE 3 — Inference Runner (`run_classify.py`)

**Goal:** Load model, run on all polygons, save predictions.

**Usage:**

```bash
python run_classify.py
# with custom input:
python run_classify.py --features outputs/predictions/change_features.csv
```

**Execution flow:**

```
[1/5] Checking Person 2 outputs exist...
[2/5] Loading trained model (models/rf_classifier.joblib)...
[3/5] Loading features (outputs/predictions/change_features.csv)...
[4/5] Running inference on N polygons...
[5/5] Saving predictions...

Done. Outputs written to:
  outputs/predictions/predictions.csv

Summary:
  Total polygons classified: N
  Class distribution:
    New Construction:      X (XX%)
    Road Change:           X (XX%)
    Vegetation Clearing:   X (XX%)
    Excavation / Mining:   X (XX%)
    Other Human Change:    X (XX%)
  Mean confidence: X.XX
  Low confidence (<0.5): X polygons flagged
```

**Exit Codes:**

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Person 2 outputs missing (run run_vectorize.py first) |
| 2 | Model not trained (run Phase 2 first: python src/models/classifier.py) |
| 3 | Too few features to run inference |
| 4 | Unexpected error |

**Status:** PENDING

---

### PHASE 4 — Verification

**Goal:** Confirm predictions.csv is valid and ready for Person 4.

**Checklist:**
- [ ] `outputs/predictions/predictions.csv` exists and is readable
- [ ] `models/rf_classifier.joblib` exists
- [ ] `models/rf_imputer.joblib` exists
- [ ] `models/rf_metadata.json` exists
- [ ] predictions.csv has columns: id, predicted_class, predicted_label, confidence
- [ ] predicted_class values are in {0, 1, 2, 3, 4}
- [ ] confidence values are in [0.0, 1.0]
- [ ] Row count matches change_features.csv row count
- [ ] No class gets 100% of predictions (model is not completely degenerate)

**Verification script:**

```bash
python -c "
import pandas as pd, json, os

# Check predictions
assert os.path.exists('outputs/predictions/predictions.csv'), 'predictions.csv MISSING'
df = pd.read_csv('outputs/predictions/predictions.csv')
print(f'Predictions: {len(df)} rows')
print(f'Columns: {list(df.columns)}')
print(f'Class distribution:')
print(df['predicted_label'].value_counts())
print(f'Confidence range: {df.confidence.min():.3f} - {df.confidence.max():.3f}')
assert df.confidence.between(0, 1).all(), 'Confidence out of [0,1] range'

# Check model files
for f in ['models/rf_classifier.joblib', 'models/rf_imputer.joblib', 'models/rf_metadata.json']:
    assert os.path.exists(f), f'MISSING: {f}'
    print(f'OK: {f}')

print('ALL P3 VERIFICATION PASSED')
"
```

**Status:** PENDING

---

## 5. Output Specification for Person 4

### Primary: `outputs/predictions/predictions.csv`

**All columns Person 4 will receive:**

| Column | Type | Description |
|---|---|---|
| id | int | Polygon ID (matches change_results.geojson) |
| predicted_class | int | Class integer: 0-4 |
| predicted_label | str | Human-readable class name |
| confidence | float | Max class probability (0.0 to 1.0) |
| area_m2 | float | Polygon area (pass-through from Person 2) |
| latitude | float | Centroid latitude (pass-through) |
| longitude | float | Centroid longitude (pass-through) |
| cva_mean | float | Mean CVA magnitude (pass-through) |
| delta_ndvi | float | NDVI change (pass-through) |

**Note to Person 4:** Join predictions.csv with `outputs/polygons/change_results.geojson` on `id` to get the full polygon geometry for map display.

### How Person 4 loads and joins:

```python
import pandas as pd
import geopandas as gpd

# Load predictions
preds = pd.read_csv("outputs/predictions/predictions.csv")

# Load geometry
gdf = gpd.read_file("outputs/polygons/change_results.geojson")

# Join on id
result = gdf.merge(preds[["id","predicted_class","predicted_label","confidence"]], on="id")
# result is a GeoDataFrame with geometry + predictions
# Pass to Streamlit / folium / QGIS
```

---

## 6. Class Reference (for Person 4 display)

| Class ID | Label | Suggested Map Colour | Icon |
|---|---|---|---|
| 0 | New Construction | #FF6B35 (orange) | Building |
| 1 | Road Change / Expansion | #4A90D9 (blue) | Road |
| 2 | Vegetation Clearing | #D32F2F (red) | Tree-slash |
| 3 | Excavation / Mining | #7B3F00 (brown) | Shovel |
| 4 | Other Human Change | #9E9E9E (grey) | Question mark |

---

## 7. Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| Model | RandomForestClassifier | Fast to train, handles small datasets, outputs probabilities, interpretable feature importances |
| No Siamese CNN / deep learning | Intentional | 24-hour MVP; no labelled pixel-pair data; RF sufficient for feature-based classification |
| class_weight='balanced' | Yes | Expected class imbalance (most polygons may be Vegetation Clearing or Other) |
| NaN imputation | SimpleImputer(strategy='median') | NDVI features may be NaN when bands missing; median is robust |
| Imputer saved separately | models/rf_imputer.joblib | Must apply SAME imputation at inference as at training |
| Label source | Rule-based first, human corrected | Transparent: never pretend auto-rules are ground truth |
| Feature set | 13 of 16 (exclude id, lat, lon) | lat/lon would make model location-specific, not generalizable |
| Evaluation split | Stratified 80/20 | Preserve class distribution in small datasets |
| Model saved format | joblib | Standard for sklearn; fast load |
| Confidence | max class probability | Most intuitive for Person 4 display |
| Metadata JSON | Yes | Preserves class names, feature list, training date for reproducibility |

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Person 2 outputs not ready | Phase 0 checks; clear error if missing |
| Too few labelled samples (<10) | Skip evaluation, warn, train on all data anyway |
| All polygons labelled "Other" by rules | Review rules; lower thresholds; inspect real data |
| Class imbalance | class_weight='balanced' in RF; merge rare classes |
| NaN features crash model | SimpleImputer applied before any sklearn call |
| Model overfits tiny dataset | Document limitation clearly; RF with max_depth=5 as fallback |
| Person 4 cannot find polygon geometry | Join on 'id'; document join code in this file and in README |
| Auto-labels incorrect for demo | Open prototype_labels.csv in Excel, fix 10-20 key labels manually |

---

## 9. Progress Tracker

| Phase | Description | Status | Notes |
|---|---|---|---|
| Audit | Repository inspection | DONE | 2026-08-20 |
| Plan | This document | DONE | 2026-08-20 |
| Phase 0 | Environment + Person 2 output check | PENDING | Waiting for P2 to complete |
| Phase 1 | labeller.py + prototype_labels.csv | PENDING | |
| Phase 2 | classifier.py + model training | PENDING | |
| Phase 3 | run_classify.py + predictions.csv | PENDING | |
| Phase 4 | Verification | PENDING | |

---

## 10. Cross-Person Interface Summary

```
PERSON 2 OUTPUTS                PERSON 3 READS            PERSON 3 OUTPUTS
────────────────                ──────────────            ─────────────────
change_features.csv  ────────►  labeller.py   ────►  prototype_labels.csv
                                classifier.py ────►  models/rf_classifier.joblib
                                              ────►  models/rf_imputer.joblib
                                              ────►  models/rf_metadata.json
change_features.csv  ────────►  run_classify  ────►  predictions.csv

                                                         PERSON 4 READS
                                                         ─────────────────
                                                         predictions.csv ──► Dashboard display
                                                         change_results.geojson ──► Map geometry (join on id)
```

---

## 11. Update Log

| Date | Update |
|---|---|
| 2026-08-20 | Repository fully audited. Person 2 code inspected (extractor.py, run_vectorize.py). All 16 feature columns confirmed. Full phased ML plan written. Waiting for Person 2 to complete their outputs before coding begins. |
