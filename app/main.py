"""
CIPHER-X — Streamlit Interactive GIS Dashboard
Space-Tech Change Detection Command Center

Usage:
    streamlit run app/main.py
"""

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import pydeck as pdk

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
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CIPHER-X | Satellite Change Detection",
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
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600; color: #fff;
    }
    .pipeline-ok { color: #22C55E; }
    .pipeline-miss { color: #EF4444; }
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
# PHASE 2 — Header & Sidebar
# ══════════════════════════════════════════════════════════════════════════════

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛰️ CIPHER-X Control")

    st.markdown("### Pipeline Status")
    for stage, ok in pipeline.items():
        icon = "✅" if ok else "❌"
        st.markdown(f"{icon} {stage}")

    st.divider()

    # Filters
    if not predictions.empty:
        st.markdown("### Filters")

        class_options = sorted(predictions["predicted_label"].unique().tolist())
        selected_classes = st.multiselect(
            "Change Class",
            options=class_options,
            default=class_options,
        )

        conf_min, conf_max = st.slider(
            "Confidence Range",
            0.0, 1.0,
            (float(predictions["confidence"].min()), float(predictions["confidence"].max())),
            step=0.05,
        )

        area_min, area_max = st.slider(
            "Area (m²)",
            0.0,
            float(predictions["area_m2"].max()),
            (0.0, float(predictions["area_m2"].max())),
            step=100.0,
        )
    else:
        selected_classes = []
        conf_min, conf_max = 0.0, 1.0
        area_min, area_max = 0.0, 1.0

    st.divider()
    st.markdown("### Export")
    st.markdown("[SIH 2026 Space-Tech MVP](https://sih.gov.in)")

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
st.markdown("# 🛰️ CIPHER-X — Satellite Change Detection")
st.markdown(
    "**Space-Tech Command Center** — "
    "Detection and classification of significant land-use changes "
    "using Sentinel-2 temporal imagery and machine learning."
)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 continued — KPI Metrics Row
# ══════════════════════════════════════════════════════════════════════════════
if not predictions.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Regions", kpi["total_polygons"])
    c2.metric("Total Changed Area", f"{kpi['total_area_ha']:.2f} ha")
    c3.metric("Mean Confidence", f"{kpi['mean_confidence']:.1%}")
    c4.metric("Low Confidence", kpi["low_confidence_count"])

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Interactive GIS Map
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🗺️ Change Detection Map")

if filtered.empty:
    st.info("No polygons match the current filters. Adjust filters in the sidebar.")
else:
    # Build GeoJSON features for the map
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
        if pd.isna(w_m):
            w_m = 200
        if pd.isna(h_m):
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

        feature = {
            "type": "Feature",
            "properties": {
                "id": int(rid),
                "predicted_label": label,
                "confidence": float(conf),
                "area_m2": float(area),
                "fill_color": CLASS_COLORS.get(label, "#8D99AE"),
            },
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        }
        geojson_features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "features": geojson_features,
    }

    # Center map on filtered data centroid
    center_lat = float(filtered["latitude"].mean())
    center_lon = float(filtered["longitude"].mean())

    polygon_layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson_data,
        get_fill_color="[properties.fill_color[0], properties.fill_color[1], properties.fill_color[2], 120]",
        get_line_color="[255, 255, 255, 200]",
        get_line_width=2,
        pickable=True,
        auto_highlight=True,
        filled=True,
        stroked=True,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered[["latitude", "longitude", "id", "predicted_label", "confidence", "area_m2"]].to_dict("records"),
        get_position=["longitude", "latitude"],
        get_radius=50,
        get_fill_color=[0, 210, 255, 200],
        pickable=True,
    )

    deck = pdk.Deck(
        layers=[polygon_layer, scatter_layer],
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=10,
            pitch=0,
        ),
        tooltip={
            "html": (
                "<b>Region #{id}</b><br>"
                "{predicted_label}<br>"
                "Confidence: {confidence:.1%}<br>"
                "Area: {area_m2:,.0f} m²"
            ),
            "style": {
                "backgroundColor": "#1E232F",
                "color": "#FFFFFF",
                "fontSize": "13px",
                "padding": "8px",
            },
        },
    )

    st.pydeck_chart(deck, use_container_width=True, height=500)

    # Legend
    st.markdown("**Legend:**")
    legend_html = "  ".join([
        f'<span class="class-badge" style="background:{color};">{name}</span>'
        for name, color in CLASS_COLORS.items()
        if name in class_options
    ])
    st.markdown(legend_html, unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — Region Inspector
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔍 Region Inspector")

if filtered.empty:
    st.info("No regions available for inspection.")
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

        # Confidence badge
        if conf >= 0.8:
            conf_badge = "🟢 High"
        elif conf >= 0.6:
            conf_badge = "🟡 Medium"
        else:
            conf_badge = "🔴 Review"

        st.markdown(f"""
        **Region #{int(row['id'])}** &nbsp;
        <span class="class-badge" style="background:{color};">{label}</span>
        &nbsp; Confidence: **{conf:.1%}** {conf_badge}
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 📍 Geographic")
            st.markdown(f"- **Latitude:** {row['latitude']:.6f}")
            st.markdown(f"- **Longitude:** {row['longitude']:.6f}")
            st.markdown(f"- **Area:** {row['area_m2']:,.0f} m² ({row['area_m2']/10000:.4f} ha)")

        with col2:
            st.markdown("#### 📡 Spectral")
            st.markdown(f"- **CVA Mean:** {row['cva_mean']:.4f}")
            ndvi_val = row.get("delta_ndvi", 0)
            if not pd.isna(ndvi_val):
                ndvi_color = "🔴" if ndvi_val < -0.1 else "🟡" if ndvi_val < 0 else "🟢"
                st.markdown(f"- **ΔNDVI:** {ndvi_color} {ndvi_val:.4f}")
            else:
                st.markdown("- **ΔNDVI:** N/A")

        with col3:
            st.markdown("#### 📐 Shape")
            if feat_row is not None:
                st.markdown(f"- **Width:** {feat_row.get('bbox_width_m', 0):.0f} m")
                st.markdown(f"- **Height:** {feat_row.get('bbox_height_m', 0):.0f} m")
                st.markdown(f"- **Compactness:** {feat_row.get('compactness', 0):.3f}")
            else:
                st.markdown("- Shape features: N/A (change_features.csv not loaded)")

        # Band deltas table
        if feat_row is not None:
            st.markdown("#### 🌈 Band Deltas")
            band_data = {
                "Band": ["ΔB02 (Blue)", "ΔB03 (Green)", "ΔB04 (Red)", "ΔB08 (NIR)"],
                "Value": [
                    feat_row.get("delta_b02", 0),
                    feat_row.get("delta_b03", 0),
                    feat_row.get("delta_b04", 0),
                    feat_row.get("delta_b08", 0),
                ],
            }
            band_df = pd.DataFrame(band_data)
            st.dataframe(band_df, use_container_width=True, hide_index=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — Before/After & CVA Visualization
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📡 Satellite & CVA Visualization")

has_rasters = Path("outputs/maps/change_magnitude.tif").exists()

if has_rasters:
    import rasterio
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    col_before, col_after = st.columns(2)

    with col_before:
        st.markdown("**Before Scene (Simulated RGB)**")
        st.info("Load real Sentinel-2 data via `python run_pipeline.py` for true before/after imagery.")

    with col_after:
        st.markdown("**CVA Change Magnitude**")
        with rasterio.open("outputs/maps/change_magnitude.tif") as src:
            mag = src.read(1)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.imshow(mag, cmap="viridis")
        ax.set_title("Change Magnitude", color="white", fontsize=10)
        ax.axis("off")
        fig.patch.set_facecolor("#0E1117")
        st.pyplot(fig)
        plt.close(fig)
else:
    st.info(
        "Raster files not generated yet. "
        "Run `python run_pipeline.py` to create change magnitude maps."
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 6 — Analytics, Feature Importance & Metrics
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Analytics & ML Insights")

if filtered.empty:
    st.info("No data available for analytics.")
else:
    tab1, tab2, tab3, tab4 = st.tabs([
        "Class Distribution", "Confidence", "Feature Importance", "Model Metrics"
    ])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Regions by Class**")
            class_counts = filtered["predicted_label"].value_counts()
            colors = [CLASS_COLORS.get(c, "#8D99AE") for c in class_counts.index]

            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(6, 4))
            bars = ax.barh(class_counts.index, class_counts.values, color=colors)
            ax.set_xlabel("Count", color="#94A3B8")
            ax.set_title("Change Type Distribution", color="white", fontsize=11)
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
            st.markdown("**Area by Class (hectares)**")
            class_areas = filtered.groupby("predicted_label")["area_m2"].sum() / 10000
            class_areas = class_areas.sort_values(ascending=True)
            colors_a = [CLASS_COLORS.get(c, "#8D99AE") for c in class_areas.index]

            fig2, ax2 = plt.subplots(figsize=(6, 4))
            ax2.barh(class_areas.index, class_areas.values, color=colors_a)
            ax2.set_xlabel("Hectares", color="#94A3B8")
            ax2.set_title("Changed Area by Type", color="white", fontsize=11)
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
        ax3.hist(filtered["confidence"], bins=20, color="#00D2FF", edgecolor="#1E232F", alpha=0.8)
        ax3.set_xlabel("Confidence", color="#94A3B8")
        ax3.set_ylabel("Count", color="#94A3B8")
        ax3.set_title("Prediction Confidence Distribution", color="white", fontsize=11)
        ax3.tick_params(colors="#94A3B8")
        ax3.spines["bottom"].set_color("#2E384D")
        ax3.spines["left"].set_color("#2E384D")
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)
        fig3.patch.set_facecolor("#0E1117")
        ax3.set_facecolor("#0E1117")
        st.pyplot(fig3)
        plt.close(fig3)

        st.markdown(f"**Mean:** {filtered['confidence'].mean():.3f}  |  "
                     f"**Median:** {filtered['confidence'].median():.3f}  |  "
                     f"**Min:** {filtered['confidence'].min():.3f}  |  "
                     f"**Max:** {filtered['confidence'].max():.3f}")

    with tab3:
        if not importances.empty:
            fig4, ax4 = plt.subplots(figsize=(8, 4))
            ax4.barh(
                importances["feature"],
                importances["importance"],
                color="#7928CA",
            )
            ax4.set_xlabel("Importance", color="#94A3B8")
            ax4.set_title("Random Forest Feature Importance", color="white", fontsize=11)
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
            st.info("Feature importance data not available. Train a model first.")

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

            # Confusion matrix
            cm = metrics.get("confusion_matrix", [])
            if cm:
                st.markdown("**Confusion Matrix**")
                cm_df = pd.DataFrame(
                    cm,
                    index=[CLASS_NAMES.get(str(i), f"Class {i}") for i in range(len(cm))],
                    columns=[CLASS_NAMES.get(str(i), f"Class {i}") for i in range(len(cm[0]) if cm else 0)],
                )
                st.dataframe(cm_df, use_container_width=True)

            # Classification report
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
# PHASE 7 — Export & Download
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📥 Export")

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
            "🗺️ Download GeoJSON",
            data=geojson_bytes,
            file_name="change_results.geojson",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.button("🗺️ Download GeoJSON", disabled=True, use_container_width=True)

with dl_col3:
    if metadata:
        meta_bytes = json.dumps(metadata, indent=2, default=str).encode("utf-8")
        st.download_button(
            "📊 Download Model Metadata",
            data=meta_bytes,
            file_name="rf_metadata.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.button("📊 Download Model Metadata", disabled=True, use_container_width=True)

st.divider()

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center; color:#94A3B8; font-size:0.8rem;'>"
    "CIPHER-X | SIH 2026 Space-Tech MVP | "
    "Sentinel-2 + CVA + Random Forest | "
    "Person 1: Preprocessing & CVA | Person 2: Vectors & Features | "
    "Person 3: ML Classification | Person 4: Dashboard & Integration"
    "</div>",
    unsafe_allow_html=True,
)
