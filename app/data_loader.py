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


def clear_pipeline_cache() -> None:
    """Clear all Streamlit data caches so fresh outputs are loaded immediately."""
    st.cache_data.clear()


@st.cache_data
def get_rgb_composite(folder_path: str) -> tuple:
    """
    Extract and composite True Color RGB (Red B04, Green B03, Blue B02)
    from a Sentinel-2 band folder.

    Returns:
        (rgb_image: np.ndarray (H, W, 3) uint8, bounds: dict or None)
    """
    import rasterio
    from src.preprocessing.loader import find_band_file
    from pyproj import Transformer

    folder = Path(folder_path)
    if not folder.exists():
        return None, None

    try:
        b04_p = find_band_file(folder, "B04")
        b03_p = find_band_file(folder, "B03")
        b02_p = find_band_file(folder, "B02")
    except Exception:
        return None, None

    with rasterio.open(b04_p) as s4, rasterio.open(b03_p) as s3, rasterio.open(b02_p) as s2:
        r = s4.read(1).astype(np.float32)
        g = s3.read(1).astype(np.float32)
        b = s2.read(1).astype(np.float32)
        crs = s4.crs
        bounds = s4.bounds

    rgb = np.stack([r, g, b], axis=-1)

    # 2% - 98% percentile stretch for natural contrast
    p2, p98 = np.percentile(rgb, (2, 98))
    if p98 > p2:
        rgb_norm = np.clip((rgb - p2) / (p98 - p2) * 255.0, 0, 255).astype(np.uint8)
    else:
        rgb_norm = np.clip(rgb / 10000.0 * 255.0, 0, 255).astype(np.uint8)

    # Reproject bounding box to WGS84 lat/lon
    bounds_wgs84 = None
    if crs is not None:
        try:
            if getattr(crs, "is_geographic", False):
                bounds_wgs84 = {
                    "west": bounds.left,
                    "south": bounds.bottom,
                    "east": bounds.right,
                    "north": bounds.top,
                }
            else:
                tf = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
                west, south = tf.transform(bounds.left, bounds.bottom)
                east, north = tf.transform(bounds.right, bounds.top)
                bounds_wgs84 = {
                    "west": min(west, east),
                    "south": min(south, north),
                    "east": max(west, east),
                    "north": max(south, north),
                }
        except Exception:
            bounds_wgs84 = None

    return rgb_norm, bounds_wgs84


def execute_full_pipeline(
    before_dir: str = "data/sentinel/before",
    after_dir: str = "data/sentinel/after",
    min_area: float = 500.0,
) -> tuple[bool, str]:
    """
    Run all 4 CIPHER-X pipeline stages in sequence.
    Returns (success: bool, log_output: str).
    """
    import subprocess
    import sys

    logs = []
    stages = [
        ("Person 1 (Preprocessing + CVA)", [sys.executable, "run_pipeline.py", "--before", before_dir, "--after", after_dir]),
        ("Person 2 (Vectorization + Features)", [sys.executable, "run_vectorize.py", "--min-area", str(min_area)]),
        ("Person 3a (Auto-Labeller)", [sys.executable, "src/models/labeller.py"]),
        ("Person 3b (Train Classifier)", [sys.executable, "src/models/classifier.py"]),
        ("Person 3c (ML Inference)", [sys.executable, "run_classify.py"]),
    ]

    for name, cmd in stages:
        logs.append(f"\n▶ Running {name}...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        logs.append(res.stdout)
        if res.stderr:
            logs.append(f"[STDERR]: {res.stderr}")
        if res.returncode != 0:
            logs.append(f"❌ {name} failed with exit code {res.returncode}")
            return False, "\n".join(logs)
        logs.append(f"✅ {name} completed successfully.")

    clear_pipeline_cache()
    return True, "\n".join(logs)


def execute_auto_extraction(
    aoi: str,
    before_start: str,
    before_end: str,
    after_start: str,
    after_end: str,
    max_cloud: int = 20,
    username: str = None,
    password: str = None,
    min_area: float = 500.0,
) -> tuple[bool, str]:
    """
    Auto-download Sentinel-2 scenes from Copernicus CDSE and run full pipeline.
    """
    from src.preprocessing.downloader import download_sentinel2

    logs = []
    logs.append(f"🛰️ Initiating auto-download for AOI: {aoi}")
    logs.append(f"  BEFORE range: {before_start} to {before_end}")
    logs.append(f"  AFTER range:  {after_start} to {after_end}")

    try:
        download_sentinel2(
            aoi=aoi,
            before_date=(before_start.strip(), before_end.strip()),
            after_date=(after_start.strip(), after_end.strip()),
            before_dir="data/sentinel/before",
            after_dir="data/sentinel/after",
            max_cloud=max_cloud,
            username=username,
            password=password,
        )
        logs.append("✅ Sentinel-2 data extraction finished.")
    except Exception as e:
        logs.append(f"❌ Auto-download failed: {str(e)}")
        return False, "\n".join(logs)

    # Run full pipeline on extracted data
    logs.append("\n⚡ Running complete ML change detection pipeline on extracted data...")
    success, pipe_logs = execute_full_pipeline(min_area=min_area)
    logs.append(pipe_logs)

    clear_pipeline_cache()
    return success, "\n".join(logs)


def generate_sample_dataset(h: int = 300, w: int = 300) -> tuple[bool, str]:
    """
    Generate realistic synthetic Sentinel-2 dataset for immediate demonstration.
    """
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.crs import CRS

    try:
        crs = CRS.from_epsg(32643)  # UTM 43N
        transform = from_bounds(770000.0, 800000.0, 773000.0, 803000.0, w, h)

        def save_tif(path, data, dtype="float32"):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            p = {
                "driver": "GTiff",
                "dtype": dtype,
                "width": w,
                "height": h,
                "count": 1,
                "crs": crs,
                "transform": transform,
                "compress": "deflate",
            }
            with rasterio.open(path, "w", **p) as dst:
                dst.write(data.astype(dtype), 1)

        # Before
        np.random.seed(42)
        base = np.random.rand(h, w).astype(np.float32) * 0.3 + 0.1
        for bd, f in [("B02", 1.0), ("B03", 1.2), ("B04", 0.8), ("B08", 1.5)]:
            save_tif(f"data/sentinel/before/T43PFP_20240115_{bd}_10m.tif", (base * f) * 10000, "uint16")
        scl = np.full((h, w), 4, dtype=np.uint8)
        scl[20:30, 20:30] = 9
        save_tif("data/sentinel/before/T43PFP_20240115_SCL_20m.tif", scl, "uint8")

        # After
        np.random.seed(99)
        base2 = np.random.rand(h, w).astype(np.float32) * 0.3 + 0.1
        base2[60:120, 60:130] += 0.5   # Construction
        base2[20:60, 180:250] -= 0.4   # Deforestation
        base2[150:200, 50:200] += 0.3  # Excavation
        for bd, f in [("B02", 1.0), ("B03", 1.2), ("B04", 0.8), ("B08", 1.5)]:
            save_tif(f"data/sentinel/after/T43PFP_20240601_{bd}_10m.tif", (base2 * f) * 10000, "uint16")
        scl2 = np.full((h, w), 4, dtype=np.uint8)
        save_tif("data/sentinel/after/T43PFP_20240601_SCL_20m.tif", scl2, "uint8")

        # Run pipeline
        success, logs = execute_full_pipeline(min_area=500.0)
        return success, f"Sample Sentinel-2 dataset generated.\n{logs}"
    except Exception as e:
        return False, f"Failed to generate sample dataset: {e}"

