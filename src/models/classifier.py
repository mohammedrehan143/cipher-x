"""
Random Forest Classifier
Data loading, median imputation, balanced RF training, evaluation, and batch inference.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


# 13 numeric features for the classifier (excludes id, latitude, longitude)
FEATURE_COLS = [
    "area_m2", "cva_mean", "cva_max",
    "ndvi_before", "ndvi_after", "delta_ndvi",
    "delta_b02", "delta_b03", "delta_b04", "delta_b08",
    "bbox_width_m", "bbox_height_m", "compactness",
]

CLASS_NAMES = {
    0: "New Construction",
    1: "Road Change / Expansion",
    2: "Vegetation Clearing",
    3: "Excavation / Mining",
    4: "Other Human Change",
}


def load_training_data(labels_path: Path) -> tuple:
    """
    Load labelled CSV and prepare feature matrix X and label vector y.

    Applies median imputation for NaN values.
    Expects labels CSV to have a 'label' column (int 0-4).

    Args:
        labels_path: Path to prototype_labels.csv

    Returns:
        (X, y, imputer, feature_names)
        X: np.ndarray (n_samples, 13) — imputed feature matrix
        y: np.ndarray (n_samples,) — integer labels
        imputer: fitted SimpleImputer
        feature_names: list of 13 feature column names
    """
    df = pd.read_csv(labels_path)

    if "label" not in df.columns:
        raise ValueError(f"Labels CSV missing 'label' column. Found: {list(df.columns)}")

    missing_features = [c for c in FEATURE_COLS if c not in df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns in labels CSV: {missing_features}")

    y = df["label"].values.astype(int)
    X_raw = df[FEATURE_COLS].values.astype(np.float64)

    imputer = SimpleImputer(strategy="median")
    X = imputer.fit_transform(X_raw)

    return X, y, imputer, FEATURE_COLS


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list,
) -> tuple:
    """
    Train a balanced RandomForestClassifier with train/validation split.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Label vector (n_samples,)
        feature_names: List of feature column names

    Returns:
        (clf, metrics) tuple:
            clf: trained RandomForestClassifier
            metrics: dict with accuracy, classification_report, confusion_matrix
    """
    n_samples = len(y)
    n_classes = len(np.unique(y))

    # For very small datasets, skip the train/val split and train on all data
    if n_samples < 20 or n_classes < 2:
        print(f"[WARNING] Only {n_samples} samples / {n_classes} classes — training on full dataset")
        X_train, X_val, y_train, y_val = X, X, y, y
    else:
        stratify = y if min(np.bincount(y)) >= 2 else None
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify,
        )

    n_estimators = min(200, max(50, n_samples * 2))
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    present_classes = sorted(set(y_val) | set(y_pred))
    target_names_present = [CLASS_NAMES.get(i, f"Class {i}") for i in present_classes]
    report = classification_report(
        y_val, y_pred,
        labels=present_classes,
        target_names=target_names_present,
        zero_division=0,
        output_dict=True,
    )
    cm = confusion_matrix(y_val, y_pred).tolist()

    metrics = {
        "accuracy": float(accuracy),
        "classification_report": report,
        "confusion_matrix": cm,
        "n_train": int(len(y_train)),
        "n_val": int(len(y_val)),
        "n_classes": int(n_classes),
        "feature_importances": {
            name: float(imp)
            for name, imp in zip(feature_names, clf.feature_importances_)
        },
    }

    print(f"\n=== Random Forest Evaluation ===")
    print(f"Training samples: {len(y_train)} (after 80/20 split -> train on {len(y_train)}, eval on {len(y_val)})")
    print(f"Classes: {sorted(CLASS_NAMES.keys())}")
    print(f"\nValidation Accuracy: {accuracy:.4f}")

    present_classes = sorted(set(y_val) | set(y_pred))
    target_names_present = [CLASS_NAMES.get(i, f"Class {i}") for i in present_classes]
    report_str = classification_report(
        y_val, y_pred,
        labels=present_classes,
        target_names=target_names_present,
        zero_division=0,
    )
    print(f"\nClassification Report:\n{report_str}")

    cm = confusion_matrix(y_val, y_pred)
    print(f"Confusion Matrix:\n{cm}")

    if n_samples < 50:
        print(f"\nNOTE: Dataset is small ({n_samples} samples). These metrics are indicative only.")
        print(f"Model is retrained on 100% of data before saving.")

    return clf, metrics


def save_artifacts(
    clf,
    imputer,
    metadata: dict,
    output_dir: Path,
) -> None:
    """
    Save trained model, imputer, and metadata JSON to disk.

    Outputs:
        models/rf_classifier.joblib
        models/rf_imputer.joblib
        models/rf_metadata.json

    Args:
        clf: trained RandomForestClassifier
        imputer: fitted SimpleImputer
        metadata: dict with feature names, metrics, class mapping, etc.
        output_dir: output directory (default: models/)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    clf_path = output_dir / "rf_classifier.joblib"
    imputer_path = output_dir / "rf_imputer.joblib"
    meta_path = output_dir / "rf_metadata.json"

    joblib.dump(clf, clf_path)
    joblib.dump(imputer, imputer_path)

    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_type": "RandomForestClassifier",
        "feature_names": FEATURE_COLS,
        "class_names": CLASS_NAMES,
        "n_estimators": clf.n_estimators,
        "n_features": int(clf.n_features_in_),
        "classes": clf.classes_.tolist(),
    }
    meta.update(metadata)

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print(f"       Saved: {clf_path}")
    print(f"       Saved: {imputer_path}")
    print(f"       Saved: {meta_path}")


def predict_features(clf, imputer, df: pd.DataFrame) -> pd.DataFrame:
    """
    Run batch inference on feature table to predict change class and confidence.

    Args:
        clf: trained RandomForestClassifier
        imputer: fitted SimpleImputer
        df: DataFrame with 16 feature columns from Person 2

    Returns:
        DataFrame with columns:
            id, predicted_class, predicted_label, confidence,
            plus pass-through features (area_m2, latitude, longitude, cva_mean, delta_ndvi)
    """
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    X_raw = df[FEATURE_COLS].values.astype(np.float64)
    X = imputer.transform(X_raw)

    predictions = clf.predict(X)
    probabilities = clf.predict_proba(X)
    confidence = np.max(probabilities, axis=1)

    pred_labels = [CLASS_NAMES.get(int(p), f"Class {int(p)}") for p in predictions]

    result = pd.DataFrame({
        "id": df["id"].values,
        "predicted_class": predictions.astype(int),
        "predicted_label": pred_labels,
        "confidence": np.round(confidence, 4),
        "area_m2": df["area_m2"].values,
        "latitude": df["latitude"].values,
        "longitude": df["longitude"].values,
        "cva_mean": df["cva_mean"].values,
        "delta_ndvi": df["delta_ndvi"].values,
    })

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CIPHER-X Random Forest Classifier Training")
    parser.add_argument(
        "--labels",
        type=str,
        default="data/labels/prototype_labels.csv",
        help="Path to labelled CSV from Phase 1",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Output directory for model artifacts",
    )
    args = parser.parse_args()

    labels_path = Path(args.labels)
    output_dir = Path(args.output_dir)

    if not labels_path.exists():
        print(f"[ERROR] Missing: {labels_path}")
        print("        Run Phase 1 first: python src/models/labeller.py")
        exit(1)

    print("[1/3] Loading labelled training data...")
    X, y, imputer, feature_names = load_training_data(labels_path)
    print(f"       Loaded {len(y)} samples, {len(set(y))} classes")

    print("[2/3] Training Random Forest classifier...")
    clf, metrics = train_model(X, y, feature_names)

    print("[3/3] Saving model artifacts...")
    metadata = {
        "metrics": metrics,
        "labels_source": str(labels_path),
    }
    save_artifacts(clf, imputer, metadata, output_dir)

    print("\nDone. Model training complete.")
    print(f"  Use 'python run_classify.py' to run inference on new polygons.")
