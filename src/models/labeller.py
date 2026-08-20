"""
Prototype Labeller
Rule-based auto-labelling to generate a provisional training set from polygon features.
These labels serve as bootstrapping data for the Random Forest classifier.
"""

import numpy as np
import pandas as pd


CLASS_NAMES = {
    0: "New Construction",
    1: "Road Change / Expansion",
    2: "Vegetation Clearing",
    3: "Excavation / Mining",
    4: "Other Human Change",
}

MEDIUM_AREA_M2 = 2000.0
SMALL_AREA_M2 = 800.0
LARGE_AREA_M2 = 5000.0
ELONGATION_RATIO = 2.5
CVA_LOW = 0.15
CVA_HIGH = 0.35
NDVI_DROP_THRESHOLD = -0.05
NDVI_STRONG_DROP = -0.15
HIGH_COMPACTNESS = 0.55


def auto_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply domain heuristic rules to generate provisional training labels.

    Classification priority (evaluated top-down; first match wins):
        1. Vegetation Clearing (Class 2):
           Strong negative delta_ndvi (< -0.15) with moderate-to-large area.
           The dominant real-world change class for satellite-based detection.
        2. Road Change / Expansion (Class 1):
           Elongated geometry (bbox_width / bbox_height > 2.5 or inverse),
           moderate CVA, small-to-medium area.
        3. New Construction (Class 0):
           High CVA magnitude, high compactness (close to building footprint),
           medium-to-large area, low or negative delta_ndvi.
        4. Excavation / Mining (Class 3):
           High CVA magnitude, very low compactness (irregular shape),
           large area, with spectral delta patterns (B02/B03 dominant).
        5. Other Human Change (Class 4):
           Catch-all for remaining changed polygons.

    Args:
        df: DataFrame with 16 feature columns from Person 2.

    Returns:
        DataFrame with added columns: label (int 0-4), label_name (str), label_source (str).
    """
    labels = []
    label_names = []

    for _, row in df.iterrows():
        lbl = _classify_row(row)
        labels.append(lbl)
        label_names.append(CLASS_NAMES[lbl])

    out = df.copy()
    out["label"] = labels
    out["label_name"] = label_names
    out["label_source"] = "auto_rule"

    _print_distribution(out)
    return out


def _classify_row(row: pd.Series) -> int:
    """Classify a single polygon row using feature thresholds."""
    delta_ndvi = _safe(row.get("delta_ndvi"), 0.0)
    cva_mean = _safe(row.get("cva_mean"), 0.0)
    cva_max = _safe(row.get("cva_max"), 0.0)
    area = _safe(row.get("area_m2"), 0.0)
    compactness = _safe(row.get("compactness"), 0.0)
    w = _safe(row.get("bbox_width_m"), 0.0)
    h = _safe(row.get("bbox_height_m"), 0.0)
    delta_b02 = _safe(row.get("delta_b02"), 0.0)
    delta_b03 = _safe(row.get("delta_b03"), 0.0)

    # --- Class 2: Vegetation Clearing ---
    # Dominant signal: strong NDVI drop with meaningful change area
    if delta_ndvi < NDVI_STRONG_DROP and area >= SMALL_AREA_M2:
        return 2

    # Moderate NDVI drop with moderate CVA — still likely vegetation clearing
    if delta_ndvi < NDVI_DROP_THRESHOLD and cva_mean > CVA_LOW and area >= MEDIUM_AREA_M2:
        return 2

    # --- Class 1: Road Change / Expansion ---
    # Key geometric signature: elongated polygon
    elongation = _elongation(w, h)
    if elongation > ELONGATION_RATIO and area < LARGE_AREA_M2:
        return 1
    if elongation > ELONGATION_RATIO * 1.5 and cva_mean < CVA_HIGH:
        return 1

    # --- Class 0: New Construction ---
    # High compactness + high CVA + moderate area — building-like footprint
    if (compactness > HIGH_COMPACTNESS
            and cva_mean > CVA_HIGH
            and area >= MEDIUM_AREA_M2
            and delta_ndvi < 0.0):
        return 0

    # High CVA with strong magnitude but not vegetation clearing
    if (cva_max > 0.6
            and compactness > 0.4
            and area >= MEDIUM_AREA_M2
            and delta_ndvi >= NDVI_DROP_THRESHOLD):
        return 0

    # --- Class 3: Excavation / Mining ---
    # High CVA + low compactness + large area (irregular large disturbed region)
    if (cva_mean > CVA_HIGH
            and compactness < 0.35
            and area >= LARGE_AREA_M2):
        return 3

    # Blue/Green delta dominant with low compactness — spectral signature of exposed soil/rock
    blue_green_dominance = abs(delta_b02) + abs(delta_b03)
    if (blue_green_dominance > 0.05
            and compactness < 0.4
            and cva_mean > CVA_LOW):
        return 3

    # --- Class 4: Other Human Change ---
    return 4


def _safe(val, default):
    """Return value or default if NaN/None."""
    if val is None:
        return default
    try:
        if np.isnan(val):
            return default
    except (TypeError, ValueError):
        return default
    return float(val)


def _elongation(w, h):
    """Compute elongation ratio (longer side / shorter side)."""
    if w <= 0 or h <= 0:
        return 1.0
    return max(w, h) / min(w, h)


def _print_distribution(df: pd.DataFrame):
    """Print class distribution summary."""
    counts = df["label_name"].value_counts()
    total = len(df)
    print("\n       Provisional label distribution:")
    for name in CLASS_NAMES.values():
        cnt = counts.get(name, 0)
        pct = cnt / total * 100 if total > 0 else 0
        print(f"         {name}: {cnt} ({pct:.1f}%)")
    print(f"         Total: {total}")


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="CIPHER-X Rule-Based Auto-Labeller")
    parser.add_argument(
        "--features",
        type=str,
        default="outputs/predictions/change_features.csv",
        help="Path to change_features.csv from Person 2",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/labels/prototype_labels.csv",
        help="Output path for labelled CSV",
    )
    args = parser.parse_args()

    features_path = Path(args.features)
    output_path = Path(args.output)

    print("[1/3] Loading features...")
    if not features_path.exists():
        print(f"[ERROR] Missing: {features_path}")
        print("        Run 'python run_vectorize.py' first.")
        exit(1)

    df = pd.read_csv(features_path)
    print(f"       Loaded {len(df)} polygons, columns: {list(df.columns)}")

    nan_summary = df[["ndvi_before", "ndvi_after", "delta_ndvi", "delta_b02"]].isna().sum()
    print(f"       NaN counts: {dict(nan_summary)}")

    print("[2/3] Applying rule-based auto-labelling...")
    labelled = auto_label(df)

    print("[3/3] Saving labelled CSV...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labelled.to_csv(output_path, index=False)
    print(f"       Saved: {output_path}")
    print(f"       HUMAN REVIEW: Open this CSV, correct labels, set label_source='manual' for verified rows.")
