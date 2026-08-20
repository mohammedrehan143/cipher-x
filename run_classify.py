"""
CIPHER-X ML Inference Runner
Loads the trained Random Forest model and runs inference on all polygons.

Usage:
    python run_classify.py
    python run_classify.py --features outputs/predictions/change_features.csv

Exit Codes:
    0 - Success
    1 - Person 2 outputs missing (run run_vectorize.py first)
    2 - Model not trained (run python src/models/classifier.py first)
    3 - Too few features to run inference
    4 - Unexpected error
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.models.classifier import CLASS_NAMES, predict_features

FEATURES_DEFAULT = "outputs/predictions/change_features.csv"
MODEL_DIR = "models"
OUTPUT_CSV = "outputs/predictions/predictions.csv"


def main():
    parser = argparse.ArgumentParser(description="CIPHER-X Inference Runner")
    parser.add_argument(
        "--features",
        type=str,
        default=FEATURES_DEFAULT,
        help="Path to change_features.csv from Person 2",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=MODEL_DIR,
        help="Directory containing rf_classifier.joblib and rf_imputer.joblib",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_CSV,
        help="Output path for predictions CSV",
    )
    args = parser.parse_args()

    features_path = Path(args.features)
    model_dir = Path(args.model_dir)
    output_path = Path(args.output)

    # --- [1/5] Check Person 2 outputs exist ---
    print("[1/5] Checking Person 2 outputs exist...")
    if not features_path.exists():
        print(f"[ERROR] Missing: {features_path}")
        print("        Run 'python run_vectorize.py' first.")
        sys.exit(1)

    df = pd.read_csv(features_path)
    print(f"       Found {features_path}: {len(df)} polygons")

    # --- [2/5] Load trained model ---
    print("[2/5] Loading trained model...")
    import joblib

    clf_path = model_dir / "rf_classifier.joblib"
    imputer_path = model_dir / "rf_imputer.joblib"

    if not clf_path.exists() or not imputer_path.exists():
        print(f"[ERROR] Model not found in {model_dir}/")
        print("        Run training first: python src/models/classifier.py")
        sys.exit(2)

    clf = joblib.load(clf_path)
    imputer = joblib.load(imputer_path)
    print(f"       Loaded: {clf_path}")
    print(f"       Loaded: {imputer_path}")

    # --- [3/5] Load features ---
    print("[3/5] Loading features...")
    n_features = len(df)
    if n_features < 1:
        print("[ERROR] Too few polygons to classify.")
        sys.exit(3)
    print(f"       {n_features} polygons ready for inference")

    # --- [4/5] Run inference ---
    print(f"[4/5] Running inference on {n_features} polygons...")
    try:
        predictions = predict_features(clf, imputer, df)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(3)

    # --- [5/5] Save predictions ---
    print("[5/5] Saving predictions...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_path, index=False)
    print(f"       Saved: {output_path}")

    # Summary
    class_counts = predictions["predicted_label"].value_counts()
    total = len(predictions)
    mean_conf = predictions["confidence"].mean()
    low_conf = int((predictions["confidence"] < 0.5).sum())

    print(f"\nDone. Outputs written to:")
    print(f"  {output_path}")
    print(f"\nSummary:")
    print(f"  Total polygons classified: {total}")
    print(f"  Class distribution:")
    for cls_id, cls_name in sorted(CLASS_NAMES.items()):
        cnt = class_counts.get(cls_name, 0)
        pct = cnt / total * 100 if total > 0 else 0
        print(f"    {cls_name:30s} {cnt:4d} ({pct:5.1f}%)")
    print(f"  Mean confidence: {mean_conf:.4f}")
    if low_conf > 0:
        print(f"  Low confidence (<0.5): {low_conf} polygons flagged")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(4)
