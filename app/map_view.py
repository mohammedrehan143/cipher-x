"""
CIPHER-X Interactive Sentinel-2 GIS Map Component
Supports Live Sentinel-2 Satellite Tile Layers, Local GeoTIFF Overlays,
Interactive Polygons with Rich Popups, and Dual Before/After Swipe Map.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import folium
from folium import plugins
from folium.raster_layers import ImageOverlay
import streamlit as st
from streamlit_folium import st_folium
import pydeck as pdk

from app.data_loader import CLASS_COLORS, get_rgb_composite

# ── Tile Layer Definitions ───────────────────────────────────────────────────
SATELLITE_TILES = {
    "Sentinel-2 Cloudless (EOX)": {
        "url": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg",
        "attr": "Sentinel-2 cloudless - https://s2maps.eu by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2020)",
        "max_zoom": 17,
    },
    "ESRI World Imagery (High-Res Satellite)": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri World Imagery",
        "max_zoom": 19,
    },
    "Google Satellite Hybrid": {
        "url": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        "attr": "Google Maps Satellite",
        "max_zoom": 20,
    },
    "CartoDB Dark Matter": {
        "url": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "attr": "&copy; CartoDB &copy; OpenStreetMap contributors",
        "max_zoom": 19,
    },
    "OpenStreetMap Standard": {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "&copy; OpenStreetMap contributors",
        "max_zoom": 19,
    },
}


def render_interactive_folium_map(
    filtered_df: pd.DataFrame,
    center_lat: float,
    center_lon: float,
    zoom_start: int = 12,
    poly_opacity: float = 0.65,
    show_before_overlay: bool = True,
    show_after_overlay: bool = True,
    show_magnitude_overlay: bool = True,
    show_markers: bool = True,
    selected_basemap: str = "ESRI World Imagery (High-Res Satellite)",
):
    """
    Render a full-featured Leaflet GIS Map with real Sentinel-2 satellite tiles,
    geo-referenced Sentinel-2 optical imagery overlays, and interactive change polygons.
    """
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True,
    )

    # 1. Base Tile Layers
    for name, cfg in SATELLITE_TILES.items():
        is_default = (name == selected_basemap)
        folium.TileLayer(
            tiles=cfg["url"],
            attr=cfg["attr"],
            name=name,
            max_zoom=cfg["max_zoom"],
            overlay=False,
            control=True,
            show=is_default,
        ).add_to(m)

    # 2. Local Sentinel-2 BEFORE Scene Overlay
    if show_before_overlay:
        rgb_before, bounds_before = get_rgb_composite("data/sentinel/before")
        if rgb_before is not None and bounds_before is not None:
            # Leaflet bounds format: [[south, west], [north, east]]
            img_bounds = [
                [bounds_before["south"], bounds_before["west"]],
                [bounds_before["north"], bounds_before["east"]],
            ]
            ImageOverlay(
                image=rgb_before,
                bounds=img_bounds,
                opacity=0.85,
                name="📸 Sentinel-2 BEFORE Scene (Optical RGB)",
                show=False,
                interactive=True,
            ).add_to(m)

    # 3. Local Sentinel-2 AFTER Scene Overlay
    if show_after_overlay:
        rgb_after, bounds_after = get_rgb_composite("data/sentinel/after")
        if rgb_after is not None and bounds_after is not None:
            img_bounds = [
                [bounds_after["south"], bounds_after["west"]],
                [bounds_after["north"], bounds_after["east"]],
            ]
            ImageOverlay(
                image=rgb_after,
                bounds=img_bounds,
                opacity=0.85,
                name="📸 Sentinel-2 AFTER Scene (Optical RGB)",
                show=False,
                interactive=True,
            ).add_to(m)

    # 4. Local CVA Change Magnitude Overlay
    if show_magnitude_overlay:
        mag_path = Path("outputs/maps/change_magnitude.tif")
        if mag_path.exists():
            try:
                import rasterio
                import matplotlib.pyplot as plt
                import matplotlib.colors as mcolors

                with rasterio.open(mag_path) as src:
                    mag_data = src.read(1)
                    crs = src.crs
                    b = src.bounds

                # Convert to RGBA colormap
                valid = mag_data[~np.isnan(mag_data)]
                if valid.size > 0:
                    norm = mcolors.Normalize(vmin=float(np.percentile(valid, 2)), vmax=float(np.percentile(valid, 98)))
                    cmap = plt.get_cmap("turbo")
                    mag_colored = cmap(norm(mag_data))
                    mag_colored[np.isnan(mag_data), 3] = 0.0  # Transparent where invalid

                    from pyproj import Transformer
                    if crs is not None and getattr(crs, "is_geographic", False):
                        m_bounds = [[b.bottom, b.left], [b.top, b.right]]
                    else:
                        tf = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
                        west, south = tf.transform(b.left, b.bottom)
                        east, north = tf.transform(b.right, b.top)
                        m_bounds = [[min(south, north), min(west, east)], [max(south, north), max(west, east)]]

                    ImageOverlay(
                        image=mag_colored,
                        bounds=m_bounds,
                        opacity=0.75,
                        name="🔥 CVA Change Magnitude Heatmap",
                        show=False,
                        interactive=True,
                    ).add_to(m)
            except Exception:
                pass

    # 5. Detected Change Polygons Layer
    polygon_group = folium.FeatureGroup(name="🔴 Classified Change Polygons", show=True)

    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            lat = row["latitude"]
            lon = row["longitude"]
            area = row["area_m2"]
            label = row["predicted_label"]
            conf = row["confidence"]
            rid = int(row["id"])
            cva_mean = row.get("cva_mean", 0.0)
            delta_ndvi = row.get("delta_ndvi", np.nan)

            w_m = row.get("bbox_width_m", 200) if "bbox_width_m" in row.index else 200
            h_m = row.get("bbox_height_m", 200) if "bbox_height_m" in row.index else 200
            if pd.isna(w_m) or w_m <= 0:
                w_m = 200
            if pd.isna(h_m) or h_m <= 0:
                h_m = 200

            dlat = h_m / 110540.0
            dlon = w_m / (111320.0 * np.cos(np.radians(lat))) if abs(lat) < 90 else w_m / 111320.0

            poly_coords = [
                [lat - dlat / 2, lon - dlon / 2],
                [lat - dlat / 2, lon + dlon / 2],
                [lat + dlat / 2, lon + dlon / 2],
                [lat + dlat / 2, lon - dlon / 2],
            ]

            color = CLASS_COLORS.get(label, "#8D99AE")
            ndvi_str = f"{delta_ndvi:.4f}" if not pd.isna(delta_ndvi) else "N/A"

            # Styled Popup HTML
            popup_html = f"""
            <div style="font-family:sans-serif; min-width:200px; padding:4px;">
                <div style="font-size:14px; font-weight:bold; color:#1E232F; margin-bottom:4px;">
                    Region #{rid}
                </div>
                <div style="background:{color}; color:white; padding:3px 8px; border-radius:10px; font-size:12px; font-weight:bold; display:inline-block; margin-bottom:8px;">
                    {label}
                </div>
                <table style="width:100%; font-size:12px; border-collapse:collapse;">
                    <tr><td style="color:#555; padding:2px 0;"><b>ML Confidence:</b></td><td><b>{conf:.1%}</b></td></tr>
                    <tr><td style="color:#555; padding:2px 0;"><b>Area:</b></td><td>{area:,.0f} m² ({area/10000:.3f} ha)</td></tr>
                    <tr><td style="color:#555; padding:2px 0;"><b>CVA Magnitude:</b></td><td>{cva_mean:.4f}</td></tr>
                    <tr><td style="color:#555; padding:2px 0;"><b>ΔNDVI:</b></td><td>{ndvi_str}</td></tr>
                    <tr><td style="color:#555; padding:2px 0;"><b>Coordinates:</b></td><td>{lat:.5f}, {lon:.5f}</td></tr>
                </table>
            </div>
            """

            folium.Polygon(
                locations=poly_coords,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=poly_opacity,
                tooltip=f"<b>Region #{rid}:</b> {label} ({conf:.1%})",
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(polygon_group)

            if show_markers:
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=4,
                    color="#FFFFFF",
                    weight=1.5,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9,
                    tooltip=f"#{rid} - {label}",
                ).add_to(polygon_group)

    polygon_group.add_to(m)

    # 6. Plugins & Controls
    plugins.Fullscreen(position="topright").add_to(m)
    plugins.MeasureControl(position="topleft", primary_length_unit="meters", primary_area_unit="sqmeters").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    return m


def render_split_before_after_map(center_lat: float, center_lon: float, zoom_start: int = 12):
    """
    Render a side-by-side swipe comparison map for Before vs After Sentinel-2 imagery.
    """
    rgb_before, bounds_b = get_rgb_composite("data/sentinel/before")
    rgb_after, bounds_a = get_rgb_composite("data/sentinel/after")

    if rgb_before is None or rgb_after is None:
        st.warning("⚠️ Both BEFORE and AFTER Sentinel-2 scenes are required for the split-screen comparison viewer.")
        return None

    # Use Folium DualMap for comparison
    dm = plugins.DualMap(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        layout="horizontal",
    )

    # Base Satellite tiles
    sat_url = SATELLITE_TILES["ESRI World Imagery (High-Res Satellite)"]["url"]
    sat_attr = SATELLITE_TILES["ESRI World Imagery (High-Res Satellite)"]["attr"]

    folium.TileLayer(tiles=sat_url, attr=sat_attr, name="Satellite Base").add_to(dm.m1)
    folium.TileLayer(tiles=sat_url, attr=sat_attr, name="Satellite Base").add_to(dm.m2)

    if bounds_b is not None:
        ImageOverlay(
            image=rgb_before,
            bounds=[[bounds_b["south"], bounds_b["west"]], [bounds_b["north"], bounds_b["east"]]],
            opacity=0.9,
            name="BEFORE Optical RGB",
        ).add_to(dm.m1)

    if bounds_a is not None:
        ImageOverlay(
            image=rgb_after,
            bounds=[[bounds_a["south"], bounds_a["west"]], [bounds_a["north"], bounds_a["east"]]],
            opacity=0.9,
            name="AFTER Optical RGB",
        ).add_to(dm.m2)

    return dm
