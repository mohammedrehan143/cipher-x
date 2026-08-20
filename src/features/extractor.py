"""
Feature Extractor
Samples raster layers per polygon and computes features for ML handoff.
"""

import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.features


FEATURE_COLUMNS = [
    "id", "area_m2", "latitude", "longitude",
    "cva_mean", "cva_max",
    "ndvi_before", "ndvi_after", "delta_ndvi",
    "delta_b02", "delta_b03", "delta_b04", "delta_b08",
    "bbox_width_m", "bbox_height_m", "compactness",
]


def _raster_stats(raster_path: str, geom_gdf: gpd.GeoDataFrame, profile: dict) -> tuple:
    """
    Compute mean and max of a raster inside each polygon.

    Args:
        raster_path: path to single-band or multi-band GeoTIFF
        geom_gdf: GeoDataFrame with polygon geometries (will be reprojected to raster CRS)
        profile: rasterio profile of the raster

    Returns:
        means: list of float, mean value per polygon
        maxs: list of float, max value per polygon
    """
    raster_crs = profile.get("crs")
    if geom_gdf.crs is not None and raster_crs is not None and geom_gdf.crs != raster_crs:
        geom_native = geom_gdf.to_crs(raster_crs)
    else:
        geom_native = geom_gdf

    transform = profile["transform"]
    height = profile["height"]
    width = profile["width"]

    with rasterio.open(raster_path) as src:
        raster = src.read(1)

    means = []
    maxs = []

    for geom in geom_native.geometry:
        try:
            mask = rasterio.features.geometry_mask(
                [geom], out_shape=(height, width), transform=transform, invert=True
            )
            pixels = raster[mask]
            valid = pixels[~np.isnan(pixels)]

            if valid.size > 0:
                means.append(float(np.mean(valid)))
                maxs.append(float(np.max(valid)))
            else:
                means.append(np.nan)
                maxs.append(np.nan)
        except Exception:
            means.append(np.nan)
            maxs.append(np.nan)

    return means, maxs


def _raster_mean(raster_path: str, geom_gdf: gpd.GeoDataFrame, profile: dict, band: int = 1) -> list:
    """Compute mean of a single raster band inside each polygon."""
    raster_crs = profile.get("crs")
    if geom_gdf.crs is not None and raster_crs is not None and geom_gdf.crs != raster_crs:
        geom_native = geom_gdf.to_crs(raster_crs)
    else:
        geom_native = geom_gdf

    transform = profile["transform"]
    height = profile["height"]
    width = profile["width"]

    with rasterio.open(raster_path) as src:
        raster = src.read(band)

    return _compute_masked_means(geom_native, raster, transform, height, width)


def _raster_multi_mean(raster_path: str, geom_gdf: gpd.GeoDataFrame, profile: dict, bands: list) -> list:
    """Compute mean of multiple raster bands inside each polygon (opens file once)."""
    raster_crs = profile.get("crs")
    if geom_gdf.crs is not None and raster_crs is not None and geom_gdf.crs != raster_crs:
        geom_native = geom_gdf.to_crs(raster_crs)
    else:
        geom_native = geom_gdf

    transform = profile["transform"]
    height = profile["height"]
    width = profile["width"]

    with rasterio.open(raster_path) as src:
        rasters = [src.read(b) for b in bands]

    return [_compute_masked_means(geom_native, r, transform, height, width) for r in rasters]


def _compute_masked_means(geom_gdf: gpd.GeoDataFrame, raster: np.ndarray, transform, height: int, width: int) -> list:
    """Compute mean pixel value inside each polygon for a single raster band."""
    means = []
    for geom in geom_gdf.geometry:
        try:
            mask = rasterio.features.geometry_mask(
                [geom], out_shape=(height, width), transform=transform, invert=True
            )
            pixels = raster[mask]
            valid = pixels[~np.isnan(pixels)]
            means.append(float(np.mean(valid)) if valid.size > 0 else np.nan)
        except Exception:
            means.append(np.nan)
    return means


def _geometry_features(geom_gdf: gpd.GeoDataFrame) -> dict:
    """Compute bounding box width/height and compactness per polygon."""
    bbox_width = []
    bbox_height = []
    compactness = []

    for geom in geom_gdf.geometry:
        bounds = geom.bounds  # (minx, miny, maxx, maxy)
        w = bounds[2] - bounds[0]
        h = bounds[3] - bounds[1]

        # For WGS84, approximate metres at centroid latitude
        centroid = geom.centroid
        lat_rad = np.radians(centroid.y)
        cos_lat = np.cos(lat_rad)
        w_m = w * 111320.0 * cos_lat
        h_m = h * 110540.0

        bbox_width.append(w_m)
        bbox_height.append(h_m)

        area = geom.area
        perimeter = geom.length
        if perimeter > 0:
            c = (4.0 * np.pi * area) / (perimeter ** 2)
            compactness.append(min(c, 1.0))
        else:
            compactness.append(np.nan)

    return {
        "bbox_width_m": bbox_width,
        "bbox_height_m": bbox_height,
        "compactness": compactness,
    }


def extract_features(
    gdf: gpd.GeoDataFrame,
    magnitude_path: str,
    magnitude_profile: dict,
    spectral_delta_path: str,
    spectral_delta_profile: dict,
    ndvi_before: np.ndarray,
    ndvi_after: np.ndarray,
) -> pd.DataFrame:
    """
    Extract features for each polygon from multiple raster layers.

    Args:
        gdf: GeoDataFrame with polygon geometries (EPSG:4326)
        magnitude_path: path to change_magnitude.tif
        magnitude_profile: rasterio profile for magnitude
        spectral_delta_path: path to spectral_delta.tif
        spectral_delta_profile: rasterio profile for spectral delta
        ndvi_before: (H, W) float32 NDVI before
        ndvi_after: (H, W) float32 NDVI after

    Returns:
        DataFrame with all 16 feature columns
    """
    n = len(gdf)
    if n == 0:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    # CVA magnitude stats
    cva_mean, cva_max = _raster_stats(magnitude_path, gdf, magnitude_profile)

    # Spectral delta means (4 bands: dB02, dB03, dB04, dB08)
    delta_means = _raster_multi_mean(
        spectral_delta_path, gdf, spectral_delta_profile, bands=[1, 2, 3, 4]
    )
    delta_b02, delta_b03, delta_b04, delta_b08 = delta_means

    # NDVI stats per polygon
    raster_crs = magnitude_profile.get("crs")
    if gdf.crs is not None and raster_crs is not None and gdf.crs != raster_crs:
        geom_native = gdf.to_crs(raster_crs)
    else:
        geom_native = gdf

    transform = magnitude_profile["transform"]
    height = magnitude_profile["height"]
    width = magnitude_profile["width"]

    ndvi_before_vals = []
    ndvi_after_vals = []

    for geom in geom_native.geometry:
        try:
            mask = rasterio.features.geometry_mask(
                [geom], out_shape=(height, width), transform=transform, invert=True
            )
            before_valid = ndvi_before[mask]
            after_valid = ndvi_after[mask]

            before_clean = before_valid[~np.isnan(before_valid)]
            after_clean = after_valid[~np.isnan(after_valid)]

            ndvi_before_vals.append(float(np.mean(before_clean)) if before_clean.size > 0 else np.nan)
            ndvi_after_vals.append(float(np.mean(after_clean)) if after_clean.size > 0 else np.nan)
        except Exception:
            ndvi_before_vals.append(np.nan)
            ndvi_after_vals.append(np.nan)

    delta_ndvi = [
        (a - b) if not (np.isnan(a) or np.isnan(b)) else np.nan
        for a, b in zip(ndvi_after_vals, ndvi_before_vals)
    ]

    # Geometry features
    geom_feats = _geometry_features(gdf)

    # Build DataFrame
    df = pd.DataFrame({
        "id": gdf["id"].values,
        "area_m2": gdf["area_m2"].values,
        "latitude": gdf["latitude"].values,
        "longitude": gdf["longitude"].values,
        "cva_mean": cva_mean,
        "cva_max": cva_max,
        "ndvi_before": ndvi_before_vals,
        "ndvi_after": ndvi_after_vals,
        "delta_ndvi": delta_ndvi,
        "delta_b02": delta_b02,
        "delta_b03": delta_b03,
        "delta_b04": delta_b04,
        "delta_b08": delta_b08,
        "bbox_width_m": geom_feats["bbox_width_m"],
        "bbox_height_m": geom_feats["bbox_height_m"],
        "compactness": geom_feats["compactness"],
    })

    return df[FEATURE_COLUMNS]
