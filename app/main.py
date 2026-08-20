"""
CIPHER-X — Streamlit Interactive GIS Dashboard & Sentinel-2 Command Center
Space-Tech Change Detection, Auto-Extraction & Machine Learning Platform

Usage:
    streamlit run app/main.py
"""

import io
import json
import os
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import pydeck as pdk
from PIL import Image

from app.data_loader import (
    CLASS_COLORS,
    CLASS_ICONS,
    CLASS_NAMES,
    check_pipeline_status,
    compute_kpi_summary,
    get_feature_importances,
    load_features,
    load_metadata,
    load_predictions,
    get_rgb_composite,
    execute_full_pipeline,
    execute_auto_extraction,
    generate_sample_dataset,
    clear_pipeline_cache,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CIPHER-X | Sentinel-2 Satellite Change Detection",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    .block-container { padding-top: 1rem; }
    h1, h2, h3, h4 { color: #FFFFFF !important; }
    .stMetric label { color: #94A3B8 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #00D2FF !important; }
    div[data-testid="stSidebar"] { background-color: #1E232F; }
    div[data-testid="stSidebar"] label { color: #94A3B8; }
    .class-badge {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 0.82rem; font-weight: 600; color: #fff; margin: 2px;
    }
    .panel-card {
        background-color: #161B26; border: 1px solid #283245;
        border-radius: 10px; padding: 15px; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ── Data loading ─────────────────────────────────────────────────────────────
predictions = load_predictions()
features = load_features()
metadata = load_metadata()
kpi = compute_kpi_summary()
pipeline = check_pipeline_status()
importances = get_feature_importances()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Pipeline Status, Quick Actions & Filters
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🛰️ CIPHER-X Control")

    st.markdown("### Pipeline Status")
    for stage, ok in pipeline.items():
        icon = "✅" if ok else "❌"
        st.markdown(f"{icon} **{stage}**")

    st.divider()

    # Quick pipeline actions
    st.markdown("### ⚡ Quick Pipeline Actions")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶ Run Pipeline", use_container_width=True, help="Run all 4 stages on current local Sentinel-2 data"):
            with st.spinner("Executing pipeline stages..."):
                ok, log_out = execute_full_pipeline(min_area=200.0)
                if ok:
                    st.success("Pipeline executed successfully!")
                    st.rerun()
                else:
                    st.error("Pipeline run failed. Check logs in Extraction panel.")
    with col_btn2:
        if st.button("🧪 Demo Data", use_container_width=True, help="Generate sample Sentinel-2 data & run pipeline"):
            with st.spinner("Generating sample dataset..."):
                ok, log_out = generate_sample_dataset()
                if ok:
                    st.success("Sample dataset loaded!")
                    st.rerun()
                else:
                    st.error("Failed to generate demo data.")

    st.divider()

    # Filters
    if not predictions.empty:
        st.markdown("### 🔍 Filters")

        class_options = sorted(predictions["predicted_label"].unique().tolist())
        selected_classes = st.multiselect(
            "Change Class",
            options=class_options,
            default=class_options,
        )

        min_c = float(predictions["confidence"].min()) if not pd.isna(predictions["confidence"].min()) else 0.0
        max_c = float(predictions["confidence"].max()) if not pd.isna(predictions["confidence"].max()) else 1.0
        conf_min, conf_max = st.slider(
            "Confidence Range",
            0.0, 1.0,
            (min_c, max_c),
            step=0.05,
        )

        max_a = float(predictions["area_m2"].max()) if not pd.isna(predictions["area_m2"].max()) else 1000.0
        area_min, area_max = st.slider(
            "Area (m²)",
            0.0,
            max_a,
            (0.0, max_a),
            step=100.0,
        )
    else:
        selected_classes = []
        conf_min, conf_max = 0.0, 1.0
        area_min, area_max = 0.0, 1.0

    st.divider()
    st.markdown("### 🚀 SIH 2026 Space-Tech MVP")
    st.caption("Sentinel-2 CVA + ML Land Change Detection")

# ── Apply sidebar filters ────────────────────────────────────────────────────
if not predictions.empty:
    mask = (
        predictions["predicted_label"].isin(selected_classes)
        & predictions["confidence"].between(conf_min, conf_max)
        & predictions["area_m2"].between(area_min, area_max)
    )
    filtered = predictions[mask].copy()
else:
    filtered = predictions.copy()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("# 🛰️ CIPHER-X — Satellite Change Detection Command Center")
st.markdown(
    "**End-to-End Autonomous Platform** — "
    "Automated Sentinel-2 data extraction, CVA change detection, vector polygonization, "
    "and Random Forest land-use classification."
)

# ══════════════════════════════════════════════════════════════════════════════
# AUTO DATA EXTRACTION & PIPELINE CONTROL PANEL
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🛰️ **Sentinel-2 Auto Data Extraction & Pipeline Control Panel**", expanded=(predictions.empty)):
    st.markdown("### 📥 Copernicus Sentinel-2 Auto-Downloader & Ingestion")
    st.write("Extract multi-temporal Sentinel-2 L2A imagery directly from Copernicus Data Space Ecosystem (CDSE) or run the complete analytical pipeline.")

    tab_auto, tab_local, tab_demo = st.tabs([
        "🌐 Copernicus Auto-Download",
        "📂 Local Data Pipeline",
        "🧪 Demo Dataset Generator"
    ])

    with tab_auto:
        col_aoi, col_dates = st.columns(2)

        with col_aoi:
            st.markdown("#### 1. Area of Interest (AOI)")
            aoi_preset = st.selectbox(
                "Preset AOI Locations",
                [
                    "Custom Bounding Box",
                    "Bengaluru Urban, Karnataka (77.55, 12.90, 77.70, 13.05)",
                    "Hyderabad Airport Region, Telangana (78.35, 17.20, 78.50, 17.35)",
                    "Delhi NCR Urban Expansion (77.10, 28.50, 77.30, 28.70)",
                    "Singrauli Mining Zone, MP (82.60, 24.10, 82.75, 24.25)",
                ]
            )

            if aoi_preset == "Custom Bounding Box":
                col_w, col_s, col_e, col_n = st.columns(4)
                w_lon = col_w.number_input("West Lon", value=77.55, format="%.4f")
                s_lat = col_s.number_input("South Lat", value=12.90, format="%.4f")
                e_lon = col_e.number_input("East Lon", value=77.70, format="%.4f")
                n_lat = col_n.number_input("North Lat", value=13.05, format="%.4f")
                aoi_str = f"{w_lon},{s_lat},{e_lon},{n_lat}"
            else:
                coords = aoi_preset.split("(")[-1].replace(")", "").strip()
                aoi_str = coords

            st.info(f"Target AOI Bbox: `{aoi_str}`")

        with col_dates:
            st.markdown("#### 2. Temporal Acquisition Windows")
            c_d1, c_d2 = st.columns(2)
            b_start = c_d1.date_input("BEFORE Start", date(2024, 1, 1))
            b_end = c_d2.date_input("BEFORE End", date(2024, 1, 31))

            c_d3, c_d4 = st.columns(2)
            a_start = c_d3.date_input("AFTER Start", date(2024, 6, 1))
            a_end = c_d4.date_input("AFTER End", date(2024, 6, 30))

            max_cloud = st.slider("Max Cloud Cover (%)", 0, 50, 20)

        st.markdown("#### 3. Copernicus CDSE Credentials")
        col_u, col_p = st.columns(2)
        cdse_user = col_u.text_input("Username / Email", value=os.getenv("COPERNICUS_USERNAME", ""))
        cdse_pass = col_p.text_input("Password", type="password", value=os.getenv("COPERNICUS_PASSWORD", ""))

        if st.button("🚀 Auto-Extract from Copernicus & Run Full Pipeline", type="primary", use_container_width=True):
            if not cdse_user or not cdse_pass:
                st.warning("⚠️ Please provide Copernicus CDSE credentials to auto-download Sentinel-2 data.")
            else:
                with st.spinner("Connecting to Copernicus CDSE, downloading Sentinel-2 bands, and executing pipeline..."):
                    status_placeholder = st.empty()
                    success, log_text = execute_auto_extraction(
                        aoi=aoi_str,
                        before_start=str(b_start),
                        before_end=str(b_end),
                        after_start=str(a_start),
                        after_end=str(a_end),
                        max_cloud=max_cloud,
                        username=cdse_user,
                        password=cdse_pass,
                        min_area=200.0,
                    )
                    if success:
                        st.success("🎉 Sentinel-2 Auto-Extraction & Pipeline Complete!")
                        st.code(log_text)
                        st.rerun()
                    else:
                        st.error("Extraction or Pipeline failed.")
                        st.code(log_text)

    with tab_local:
        st.markdown("#### Run Pipeline on Data in `data/sentinel/`")
        st.write("Processes existing Sentinel-2 scenes in `data/sentinel/before/` and `data/sentinel/after/` through CVA change detection, vectorization, auto-labelling, and ML inference.")
        min_poly_area = st.number_input("Minimum Polygon Area (m²)", min_value=10.0, max_value=5000.0, value=200.0, step=50.0)

        if st.button("⚡ Execute Pipeline on Local Sentinel-2 Data", type="primary"):
            with st.spinner("Running CVA, Vectorization, and ML inference..."):
                success, log_text = execute_full_pipeline(min_area=min_poly_area)
                if success:
                    st.success("✅ Pipeline execution finished!")
                    st.code(log_text)
                    st.rerun()
                else:
                    st.error("Pipeline failed. See log output:")
                    st.code(log_text)

    with tab_demo:
        st.markdown("#### Instant Demo Sentinel-2 Dataset")
        st.write("Generates realistic synthetic Sentinel-2 multi-band scenes simulating **New Construction, Deforestation, and Excavation** and runs all stages end-to-end.")
        if st.button("🧪 Generate Demo Sentinel-2 Dataset & Run Pipeline"):
            with st.spinner("Generating synthetic Sentinel-2 scenes and running ML pipeline..."):
                success, log_text = generate_sample_dataset()
                if success:
                    st.success("✅ Demo dataset generated and analyzed!")
                    st.code(log_text)
                    st.rerun()
                else:
                    st.error("Failed to generate demo dataset:")
                    st.code(log_text)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# KPI METRICS ROW
# ══════════════════════════════════════════════════════════════════════════════
if not predictions.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Change Regions", kpi["total_polygons"])
    c2.metric("Total Changed Area", f"{kpi['total_area_ha']:.2f} ha ({kpi['total_area_m2']:,.0f} m²)")
    c3.metric("Mean ML Confidence", f"{kpi['mean_confidence']:.1%}")
    c4.metric("Low Confidence (<50%)", kpi["low_confidence_count"])

st.divider()

from app.map_view import render_interactive_folium_map, render_split_before_after_map

# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE GIS SATELLITE MAP
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🗺️ Sentinel-2 Change Detection GIS Map")

map_col1, map_col2, map_col3 = st.columns([2, 1, 1])
map_engine = map_col1.radio(
    "GIS Map Engine / View Mode",
    [
        "🗺️ Leaflet Sentinel-2 GIS Map (Interactive Popups & Overlays)",
        "🔄 Before vs After Dual Optical Map",
        "🛰️ PyDeck WebGL Satellite Map",
        "🔥 CVA Magnitude Heatmap",
    ],
    horizontal=True,
)

center_lat = float(filtered["latitude"].mean()) if not filtered.empty and not pd.isna(filtered["latitude"].mean()) else 12.9716
center_lon = float(filtered["longitude"].mean()) if not filtered.empty and not pd.isna(filtered["longitude"].mean()) else 77.5946

if map_engine == "🔄 Before vs After Dual Optical Map":
    st.markdown("### 🔄 Sentinel-2 Before vs After Optical Scene Comparison")
    st.caption("Side-by-side synchronized Sentinel-2 optical RGB scenes (Left: BEFORE change, Right: AFTER change). Pan or zoom either map to compare changes.")
    dual_map = render_split_before_after_map(center_lat=center_lat, center_lon=center_lon, zoom_start=12)
    if dual_map is not None:
        from streamlit_folium import st_folium
        st_folium(dual_map, width="100%", height=530, returned_objects=[])

elif map_engine == "🔥 CVA Magnitude Heatmap":
    st.markdown("### 🔥 Change Vector Analysis (CVA) Magnitude Continuous Heatmap")
    mag_path = Path("outputs/maps/change_magnitude.tif")
    if mag_path.exists():
        import rasterio
        import matplotlib.pyplot as plt

        with rasterio.open(mag_path) as src:
            mag_data = src.read(1)

        fig, ax = plt.subplots(figsize=(10, 4.5))
        cax = ax.imshow(mag_data, cmap="turbo")
        fig.colorbar(cax, ax=ax, label="CVA Spectral Magnitude (L2 Norm)")
        ax.set_title("CVA Change Magnitude Spectral Surface", color="white", fontsize=11)
        ax.axis("off")
        fig.patch.set_facecolor("#0E1117")
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Change magnitude raster not generated yet. Run pipeline to generate `outputs/maps/change_magnitude.tif`.")

elif map_engine == "🛰️ PyDeck WebGL Satellite Map":
    basemap_style = map_col2.selectbox(
        "Basemap Style",
        ["Satellite Imagery (ESRI World)", "Dark Canvas (Carto)", "OpenStreetMap", "Road / Streets"],
    )
    poly_opacity = map_col3.slider("Polygon Fill Opacity", 20, 255, 140, step=10)

    if filtered.empty:
        st.info("No polygons match current filters. Adjust filters in the sidebar.")
    else:
        geojson_features = []
        for _, row in filtered.iterrows():
            lat = row["latitude"]
            lon = row["longitude"]
            area = row["area_m2"]
            label = row["predicted_label"]
            conf = row["confidence"]
            rid = row["id"]

            w_m = row.get("bbox_width_m", 200) if "bbox_width_m" in row.index else 200
            h_m = row.get("bbox_height_m", 200) if "bbox_height_m" in row.index else 200
            if pd.isna(w_m) or w_m <= 0:
                w_m = 200
            if pd.isna(h_m) or h_m <= 0:
                h_m = 200

            dlat = h_m / 110540.0
            dlon = w_m / (111320.0 * np.cos(np.radians(lat))) if abs(lat) < 90 else w_m / 111320.0

            coords = [
                [lon - dlon / 2, lat - dlat / 2],
                [lon + dlon / 2, lat - dlat / 2],
                [lon + dlon / 2, lat + dlat / 2],
                [lon - dlon / 2, lat + dlat / 2],
                [lon - dlon / 2, lat - dlat / 2],
            ]

            hex_col = CLASS_COLORS.get(label, "#8D99AE").lstrip("#")
            rgb_col = [int(hex_col[i:i+2], 16) for i in (0, 2, 4)]

            feature = {
                "type": "Feature",
                "properties": {
                    "id": int(rid),
                    "predicted_label": label,
                    "confidence": float(conf),
                    "area_m2": float(area),
                    "fill_color": rgb_col,
                },
                "geometry": {"type": "Polygon", "coordinates": [coords]},
            }
            geojson_features.append(feature)

        geojson_data = {"type": "FeatureCollection", "features": geojson_features}

        tile_urls = {
            "Satellite Imagery (ESRI World)": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Dark Canvas (Carto)": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "OpenStreetMap": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "Road / Streets": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        }
        tile_url = tile_urls.get(basemap_style, tile_urls["Satellite Imagery (ESRI World)"])

        satellite_tile_layer = pdk.Layer(
            "TileLayer",
            data=tile_url,
            min_zoom=0,
            max_zoom=19,
            tile_size=256,
            render_sub_layers=lambda props: pdk.Layer("BitmapLayer", **props),
        )

        polygon_layer = pdk.Layer(
            "GeoJsonLayer",
            data=geojson_data,
            get_fill_color=f"[properties.fill_color[0], properties.fill_color[1], properties.fill_color[2], {poly_opacity}]",
            get_line_color="[255, 255, 255, 220]",
            get_line_width=2,
            pickable=True,
            auto_highlight=True,
            filled=True,
            stroked=True,
        )

        deck = pdk.Deck(
            layers=[satellite_tile_layer, polygon_layer],
            initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=11, pitch=0),
            tooltip={"html": "<b>Region #{id}</b><br>{predicted_label}<br>Conf: {confidence:.1%}<br>Area: {area_m2:,.0f} m²"},
        )
        st.pydeck_chart(deck, use_container_width=True, height=520)

else:
    # Leaflet Sentinel-2 GIS Map (Default)
    basemap_choice = map_col2.selectbox(
        "Default Satellite Basemap",
        [
            "Sentinel-2 Cloudless (EOX)",
            "ESRI World Imagery (High-Res Satellite)",
            "Google Satellite Hybrid",
            "CartoDB Dark Matter",
            "OpenStreetMap Standard",
        ],
    )
    poly_op = map_col3.slider("Polygon Fill Opacity", 0.1, 1.0, 0.65, step=0.05)

    col_layers1, col_layers2, col_layers3 = st.columns(3)
    show_b = col_layers1.checkbox("📸 Include Sentinel-2 BEFORE Overlay", value=True)
    show_a = col_layers2.checkbox("📸 Include Sentinel-2 AFTER Overlay", value=True)
    show_h = col_layers3.checkbox("🔥 Include CVA Heatmap Overlay", value=True)

    folium_map = render_interactive_folium_map(
        filtered_df=filtered,
        center_lat=center_lat,
        center_lon=center_lon,
        zoom_start=12,
        poly_opacity=poly_op,
        show_before_overlay=show_b,
        show_after_overlay=show_a,
        show_magnitude_overlay=show_h,
        selected_basemap=basemap_choice,
    )

    from streamlit_folium import st_folium
    st_folium(folium_map, width="100%", height=540, returned_objects=[])

# Legend
st.markdown("**Change Classification Legend:**")
legend_html = "  ".join([
    f'<span class="class-badge" style="background:{color};">{name}</span>'
    for name, color in CLASS_COLORS.items()
])
st.markdown(legend_html, unsafe_allow_html=True)


st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# REGION INSPECTOR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔍 Change Region Inspector")

if filtered.empty:
    st.info("No regions available for inspection. Run pipeline or adjust filters.")
else:
    region_ids = filtered["id"].tolist()
    selected_id = st.selectbox(
        "Select a change region to inspect",
        options=region_ids,
        format_func=lambda x: f"Region #{x}",
    )

    if selected_id:
        row = filtered[filtered["id"] == selected_id].iloc[0]
        feat_row = features[features["id"] == selected_id].iloc[0] if not features.empty and selected_id in features["id"].values else None

        label = row["predicted_label"]
        conf = row["confidence"]
        color = CLASS_COLORS.get(label, "#8D99AE")

        if conf >= 0.8:
            conf_badge = "🟢 High Confidence"
        elif conf >= 0.6:
            conf_badge = "🟡 Moderate Confidence"
        else:
            conf_badge = "🔴 Manual Review Suggested"

        st.markdown(f"""
        ### Region #{int(row['id'])} &nbsp;
        <span class="class-badge" style="background:{color}; font-size:1rem; padding:4px 14px;">{label}</span>
        &nbsp; ML Confidence: **{conf:.1%}** ({conf_badge})
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 📍 Spatial Attributes")
            st.markdown(f"- **Latitude:** `{row['latitude']:.6f}`")
            st.markdown(f"- **Longitude:** `{row['longitude']:.6f}`")
            st.markdown(f"- **Area:** `{row['area_m2']:,.0f} m²` (`{row['area_m2']/10000:.4f} ha`)")

        with col2:
            st.markdown("#### 📡 Spectral Signatures")
            st.markdown(f"- **CVA Mean Magnitude:** `{row['cva_mean']:.4f}`")
            ndvi_val = row.get("delta_ndvi", 0)
            if not pd.isna(ndvi_val):
                ndvi_icon = "🔴" if ndvi_val < -0.1 else "🟡" if ndvi_val < 0 else "🟢"
                st.markdown(f"- **ΔNDVI:** {ndvi_icon} `{ndvi_val:.4f}`")
            else:
                st.markdown("- **ΔNDVI:** `N/A`")

        with col3:
            st.markdown("#### 📐 Geometric Geometry")
            if feat_row is not None:
                st.markdown(f"- **BBox Width:** `{feat_row.get('bbox_width_m', 0):.0f} m`")
                st.markdown(f"- **BBox Height:** `{feat_row.get('bbox_height_m', 0):.0f} m`")
                st.markdown(f"- **Compactness Ratio:** `{feat_row.get('compactness', 0):.3f}`")
            else:
                st.markdown("- **Geometry features:** Derived bounding box")

        if feat_row is not None:
            st.markdown("#### 🌈 Band Deltas (Spectral Reflection Shift)")
            band_df = pd.DataFrame({
                "Spectral Band": ["ΔB02 (Blue)", "ΔB03 (Green)", "ΔB04 (Red)", "ΔB08 (NIR)"],
                "Delta Reflectance": [
                    float(feat_row.get("delta_b02", 0)),
                    float(feat_row.get("delta_b03", 0)),
                    float(feat_row.get("delta_b04", 0)),
                    float(feat_row.get("delta_b08", 0)),
                ],
            })
            st.dataframe(band_df, use_container_width=True, hide_index=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS & ML INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Analytics & ML Insights")

if filtered.empty:
    st.info("No data available for analytics.")
else:
    tab1, tab2, tab3, tab4 = st.tabs([
        "Class Distribution", "Confidence Distribution", "Feature Importance", "Model Evaluation"
    ])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Regions by Change Class**")
            class_counts = filtered["predicted_label"].value_counts()
            colors = [CLASS_COLORS.get(c, "#8D99AE") for c in class_counts.index]

            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(6, 3.8))
            ax.barh(class_counts.index, class_counts.values, color=colors)
            ax.set_xlabel("Polygon Count", color="#94A3B8")
            ax.set_title("Detected Change Types", color="white", fontsize=11)
            ax.tick_params(colors="#94A3B8")
            ax.spines["bottom"].set_color("#2E384D")
            ax.spines["left"].set_color("#2E384D")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.patch.set_facecolor("#0E1117")
            ax.set_facecolor("#0E1117")
            st.pyplot(fig)
            plt.close(fig)

        with col2:
            st.markdown("**Area Impacted by Class (hectares)**")
            class_areas = filtered.groupby("predicted_label")["area_m2"].sum() / 10000
            class_areas = class_areas.sort_values(ascending=True)
            colors_a = [CLASS_COLORS.get(c, "#8D99AE") for c in class_areas.index]

            fig2, ax2 = plt.subplots(figsize=(6, 3.8))
            ax2.barh(class_areas.index, class_areas.values, color=colors_a)
            ax2.set_xlabel("Hectares", color="#94A3B8")
            ax2.set_title("Total Area by Change Type", color="white", fontsize=11)
            ax2.tick_params(colors="#94A3B8")
            ax2.spines["bottom"].set_color("#2E384D")
            ax2.spines["left"].set_color("#2E384D")
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            fig2.patch.set_facecolor("#0E1117")
            ax2.set_facecolor("#0E1117")
            st.pyplot(fig2)
            plt.close(fig2)

    with tab2:
        fig3, ax3 = plt.subplots(figsize=(8, 3))
        ax3.hist(filtered["confidence"], bins=20, color="#00D2FF", edgecolor="#1E232F", alpha=0.85)
        ax3.set_xlabel("Prediction Confidence", color="#94A3B8")
        ax3.set_ylabel("Polygon Count", color="#94A3B8")
        ax3.set_title("Random Forest Prediction Confidence Distribution", color="white", fontsize=11)
        ax3.tick_params(colors="#94A3B8")
        ax3.spines["bottom"].set_color("#2E384D")
        ax3.spines["left"].set_color("#2E384D")
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)
        fig3.patch.set_facecolor("#0E1117")
        ax3.set_facecolor("#0E1117")
        st.pyplot(fig3)
        plt.close(fig3)

        st.markdown(f"**Mean:** `{filtered['confidence'].mean():.3f}`  |  "
                     f"**Median:** `{filtered['confidence'].median():.3f}`  |  "
                     f"**Min:** `{filtered['confidence'].min():.3f}`  |  "
                     f"**Max:** `{filtered['confidence'].max():.3f}`")

    with tab3:
        if not importances.empty:
            fig4, ax4 = plt.subplots(figsize=(8, 4))
            ax4.barh(
                importances["feature"],
                importances["importance"],
                color="#7928CA",
            )
            ax4.set_xlabel("Feature Importance Weight", color="#94A3B8")
            ax4.set_title("Random Forest Feature Gini Importances", color="white", fontsize=11)
            ax4.tick_params(colors="#94A3B8")
            ax4.invert_yaxis()
            ax4.spines["bottom"].set_color("#2E384D")
            ax4.spines["left"].set_color("#2E384D")
            ax4.spines["top"].set_visible(False)
            ax4.spines["right"].set_visible(False)
            fig4.patch.set_facecolor("#0E1117")
            ax4.set_facecolor("#0E1117")
            st.pyplot(fig4)
            plt.close(fig4)
        else:
            st.info("Feature importance data not available. Train a model via `python src/models/classifier.py`.")

    with tab4:
        if metadata:
            metrics = metadata.get("metrics", {})
            accuracy = metrics.get("accuracy", 0)
            n_train = metrics.get("n_train", 0)
            n_val = metrics.get("n_val", 0)
            n_classes = metrics.get("n_classes", 0)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Validation Accuracy", f"{accuracy:.2%}")
            m2.metric("Training Samples", n_train)
            m3.metric("Validation Samples", n_val)
            m4.metric("Classes Detected", n_classes)

            report = metrics.get("classification_report", {})
            if report:
                st.markdown("**Classification Report**")
                report_rows = []
                for cls_name, vals in report.items():
                    if isinstance(vals, dict) and "precision" in vals:
                        report_rows.append({
                            "Class": cls_name,
                            "Precision": f"{vals['precision']:.3f}",
                            "Recall": f"{vals['recall']:.3f}",
                            "F1-Score": f"{vals['f1-score']:.3f}",
                            "Support": int(vals.get("support", 0)),
                        })
                if report_rows:
                    st.dataframe(pd.DataFrame(report_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Model metadata not found. Train a model first via `python src/models/classifier.py`.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT & DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📥 Export GIS Layers & Data")

dl_col1, dl_col2, dl_col3 = st.columns(3)

with dl_col1:
    if not filtered.empty:
        csv_bytes = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📄 Download Predictions CSV",
            data=csv_bytes,
            file_name="cipher_x_predictions.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.button("📄 Download Predictions CSV", disabled=True, use_container_width=True)

with dl_col2:
    geojson_path = Path("outputs/polygons/change_results.geojson")
    if geojson_path.exists():
        with open(geojson_path, "r") as f:
            geojson_bytes = f.read().encode("utf-8")
        st.download_button(
            "🗺️ Download GeoJSON Polygons",
            data=geojson_bytes,
            file_name="change_results.geojson",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.button("🗺️ Download GeoJSON Polygons", disabled=True, use_container_width=True)

with dl_col3:
    if metadata:
        meta_bytes = json.dumps(metadata, indent=2, default=str).encode("utf-8")
        st.download_button(
            "📊 Download Model Metadata JSON",
            data=meta_bytes,
            file_name="rf_metadata.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.button("📊 Download Model Metadata JSON", disabled=True, use_container_width=True)

st.divider()

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center; color:#94A3B8; font-size:0.8rem;'>"
    "CIPHER-X | SIH 2026 Space-Tech MVP | "
    "Sentinel-2 Temporal Change Detection + CVA + Random Forest Classifier | "
    "Person 1: Preprocessing & CVA | Person 2: Vectors & Features | "
    "Person 3: ML Classification | Person 4: GIS Dashboard & Auto Extraction"
    "</div>",
    unsafe_allow_html=True,
)
