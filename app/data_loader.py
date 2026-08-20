"""
CIPHER-X Data Loader
Cached, zero-crash data ingestion for the Streamlit dashboard.
Handles missing upstream files gracefully with synthetic fallbacks.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ── Paths ────────────────────────────────────────────────────────────────────
PREDICTIONS_CSV = Path("outputs/predictions/predictions.csv")
FEATURES_CSV = Path("outputs/predictions/change_features.csv")
GEOJSON_FILE = Path("outputs/polygons/change_results.geojson")
MAGNITUDE_TIF = Path("outputs/maps/change_magnitude.tif")
MASK_TIF = Path("outputs/maps/change_mask.tif")
METADATA_JSON = Path("models/rf_metadata.json")
MODEL_JOBLIB = Path("models/rf_classifier.joblib")

# ── Class definitions ────────────────────────────────────────────────────────
CLASS_NAMES = {
    0: "New Construction",
    1: "Road Change / Expansion",
    2: "Vegetation Clearing",
    3: "Excavation / Mining",
    4: "Other Human Change",
}
CLASS_COLORS = {
    "New Construction": "#FF6B35",
    "Road Change / Expansion": "#3A86FF",
    "Vegetation Clearing": "#E63946",
    "Excavation / Mining": "#9C6644",
    "Other Human Change": "#8D99AE",
}
CLASS_ICONS = {
    "New Construction": "building",
    "Road Change / Expansion": "road",
    "Vegetation Clearing": "tree",
    "Excavation / Mining": "pickaxe",
    "Other Human Change": "question",
}


# ── Cached loaders ──────────────────────────────────────────────────────────
@st.cache_data
def load_predictions() -> pd.DataFrame:
    """Load predictions.csv. Returns empty DataFrame if missing."""
    if not PREDICTIONS_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(PREDICTIONS_CSV)
    return df


@st.cache_data
def load_features() -> pd.DataFrame:
    """Load change_features.csv. Returns empty DataFrame if missing."""
    if not FEATURES_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(FEATURES_CSV)


@st.cache_data
def load_metadata() -> dict:
    """Load rf_metadata.json. Returns empty dict if missing."""
    if not METADATA_JSON.exists():
        return {}
    with open(METADATA_JSON, "r") as f:
        return json.load(f)


@st.cache_data
def load_geojson() -> dict:
    """Load change_results.geojson. Returns empty dict if missing."""
    if not GEOJSON_FILE.exists():
        return {}
    with open(GEOJSON_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_polygons_as_dataframe() -> pd.DataFrame:
    """
    Load GeoJSON polygons and merge with predictions.
    Falls back to synthetic bounding boxes if GeoJSON is missing.
    """
    predictions = load_predictions()
    if predictions.empty:
        return pd.DataFrame()

    geojson = load_geojson()

    if geojson and "features" in geojson and geojson["features"]:
        polygons = pd.DataFrame(
            [f["properties"] for f in geojson["features"]]
        )
        if "id" in polygons.columns:
            merged = predictions.merge(polygons, on="id", how="left", suffixes=("", "_geo"))
            return merged

    return _synthesize_polygons(predictions)


def _synthesize_polygons(predictions: pd.DataFrame) -> pd.DataFrame:
    """Build approximate bounding-box polygons from centroids + area."""
    features = load_features()
    if not features.empty and "bbox_width_m" in features.columns:
        merged = predictions.merge(
            features[["id", "bbox_width_m", "bbox_height_m", "compactness"]],
            on="id", how="left",
        )
    else:
        merged = predictions.copy()
        merged["bbox_width_m"] = np.sqrt(merged["area_m2"]) * 0.8
        merged["bbox_height_m"] = merged["area_m2"] / merged["bbox_width_m"].clip(lower=1)
        merged["compactness"] = 0.5

    merged["geometry_synthetic"] = merged.apply(_centroid_to_bbox, axis=1)
    return merged


def _centroid_to_bbox(row) -> dict:
    """Create a GeoJSON-style bounding box polygon from centroid + dimensions."""
    lat = row["latitude"]
    lon = row["longitude"]
    w_m = row.get("bbox_width_m", 200)
    h_m = row.get("bbox_height_m", 200)

    dlat = h_m / 110540.0
    dlon = w_m / (111320.0 * np.cos(np.radians(lat))) if abs(lat) < 90 else w_m / 111320.0

    return {
        "type": "Polygon",
        "coordinates": [[
            [lon - dlon / 2, lat - dlat / 2],
            [lon + dlon / 2, lat - dlat / 2],
            [lon + dlon / 2, lat + dlat / 2],
            [lon - dlon / 2, lat + dlat / 2],
            [lon - dlon / 2, lat - dlat / 2],
        ]],
    }


@st.cache_data
def compute_kpi_summary() -> dict:
    """Compute dashboard KPI summary from predictions data."""
    df = load_predictions()
    if df.empty:
        return {
            "total_polygons": 0,
            "total_area_m2": 0,
            "total_area_ha": 0,
            "mean_confidence": 0,
            "class_counts": {},
            "class_areas": {},
            "low_confidence_count": 0,
        }

    total_area = df["area_m2"].sum()
    class_counts = df["predicted_label"].value_counts().to_dict()
    class_areas = df.groupby("predicted_label")["area_m2"].sum().to_dict()

    return {
        "total_polygons": len(df),
        "total_area_m2": float(total_area),
        "total_area_ha": float(total_area / 10000),
        "mean_confidence": float(df["confidence"].mean()),
        "class_counts": class_counts,
        "class_areas": class_areas,
        "low_confidence_count": int((df["confidence"] < 0.5).sum()),
    }


@st.cache_data
def get_feature_importances() -> pd.DataFrame:
    """Extract feature importances from model metadata."""
    meta = load_metadata()
    importances = meta.get("metrics", {}).get("feature_importances", {})
    if not importances:
        return pd.DataFrame(columns=["feature", "importance"])

    df = pd.DataFrame([
        {"feature": k, "importance": v}
        for k, v in importances.items()
    ])
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


def check_pipeline_status() -> dict:
    """Check which pipeline stages have completed."""
    return {
        "Person 1 (CVA)": MAGNITUDE_TIF.exists() and MASK_TIF.exists(),
        "Person 2 (Vectors)": GEOJSON_FILE.exists() and FEATURES_CSV.exists(),
        "Person 3 (ML)": MODEL_JOBLIB.exists() and PREDICTIONS_CSV.exists(),
        "Dashboard Data": not load_predictions().empty,
    }
