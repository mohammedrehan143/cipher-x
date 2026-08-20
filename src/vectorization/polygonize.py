"""
Change Mask Vectorization
Converts a binary change mask raster to a GeoDataFrame of change polygons.
"""

import numpy as np
import geopandas as gpd
import rasterio
import rasterio.features
import scipy.ndimage
from shapely.geometry import shape
from pyproj import Transformer


DEFAULT_MIN_AREA_M2 = 500.0
DEFAULT_OPEN_SIZE = 0


def load_and_clean_mask(mask_path: str, open_size: int = DEFAULT_OPEN_SIZE) -> tuple:
    """
    Load binary change mask and optionally apply morphological opening.

    Args:
        mask_path: path to change_mask.tif
        open_size: structuring element size for morphological opening (0 = keep as is)

    Returns:
        mask: (H, W) uint8 array, 0=no change, 1=change
        profile: rasterio profile dict (inherited CRS, transform)
    """
    with rasterio.open(mask_path) as src:
        mask = src.read(1)
        profile = src.profile.copy()

    if open_size > 0:
        struct = scipy.ndimage.generate_binary_structure(2, 1)
        cleaned = scipy.ndimage.binary_opening(
            mask.astype(bool), structure=struct, iterations=open_size
        )
        return cleaned.astype(np.uint8), profile

    return mask.astype(np.uint8), profile


def polygonize_mask(
    mask: np.ndarray,
    profile: dict,
    min_area_m2: float = DEFAULT_MIN_AREA_M2,
) -> gpd.GeoDataFrame:
    """
    Convert a binary mask to a GeoDataFrame of change polygons.

    Steps:
        1. Extract connected regions with rasterio.features.shapes()
        2. Build GeoDataFrame in native CRS
        3. Filter polygons by minimum area
        4. Repair invalid geometries
        5. Calculate area, centroid, lat/lon

    Args:
        mask: (H, W) uint8 array, 1=change
        profile: rasterio profile dict (CRS + transform)
        min_area_m2: minimum polygon area in square metres

    Returns:
        GeoDataFrame with columns: id, geometry, area_m2, latitude, longitude
        CRS: EPSG:4326 (WGS84)
    """
    transform = profile["transform"]
    crs = profile.get("crs")

    # Extract shapes from mask
    shapes = list(rasterio.features.shapes(mask, mask=mask.astype(bool), transform=transform))

    if not shapes:
        print("[WARNING] No change regions found in mask. Returning empty GeoDataFrame.")
        return _empty_gdf()

    # Build geometries and filter area
    geometries = []
    for geom, value in shapes:
        if value == 0:
            continue
        polygon = shape(geom)
        # Repair invalid geometry
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        if polygon.is_empty:
            continue
        geometries.append(polygon)

    if not geometries:
        print("[WARNING] No valid change polygons after filtering. Returning empty GeoDataFrame.")
        return _empty_gdf()

    # Build GeoDataFrame in native CRS
    gdf = gpd.GeoDataFrame(geometry=geometries, crs=crs)

    # Calculate area in square metres (handles both projected UTM CRS and geographic EPSG:4326 degrees)
    if crs is not None and getattr(crs, "is_geographic", False):
        try:
            utm_crs = gdf.estimate_utm_crs()
            gdf["area_m2"] = gdf.to_crs(utm_crs).geometry.area
        except Exception:
            # Fallback approximation for WGS84 degrees -> metres
            centroids = gdf.geometry.centroid
            cos_lats = np.cos(np.radians(centroids.y))
            gdf["area_m2"] = gdf.geometry.area * (111320.0 * cos_lats) * 110540.0
    else:
        gdf["area_m2"] = gdf.geometry.area

    # Filter by minimum area
    gdf = gdf[gdf["area_m2"] >= min_area_m2].copy()
    gdf = gdf.reset_index(drop=True)

    if gdf.empty:
        print("[WARNING] No polygons survived area filter. Returning empty GeoDataFrame.")
        return _empty_gdf()

    # Repair any remaining invalid geometries
    gdf["geometry"] = gdf["geometry"].buffer(0)
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf.reset_index(drop=True)

    # Calculate centroid in native CRS, then reproject to WGS84
    centroids_native = gdf.geometry.centroid
    transformer = None
    if crs is not None and str(crs) != "EPSG:4326":
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    lats = []
    lons = []
    for centroid in centroids_native:
        if transformer is not None:
            lon, lat = transformer.transform(centroid.x, centroid.y)
        else:
            lon, lat = centroid.x, centroid.y
        lons.append(lon)
        lats.append(lat)

    gdf["latitude"] = lats
    gdf["longitude"] = lons

    # Assign sequential id
    gdf["id"] = gdf.index + 1

    # Reorder columns
    gdf = gdf[["id", "geometry", "area_m2", "latitude", "longitude"]]

    # Reproject to WGS84 for GeoJSON output
    gdf = gdf.to_crs("EPSG:4326")

    print(f"       Polygons created: {len(gdf)} (area >= {min_area_m2:.0f} m²)")

    return gdf


def _empty_gdf() -> gpd.GeoDataFrame:
    """Return an empty GeoDataFrame with the correct columns."""
    return gpd.GeoDataFrame(
        columns=["id", "geometry", "area_m2", "latitude", "longitude"],
        geometry="geometry",
        crs="EPSG:4326",
    )
