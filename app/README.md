# App — Streamlit Interactive GIS Dashboard

> **Scope:** Person 4 — Interactive GIS Visualizer & Full System Integration.

This module provides the presentation-grade web dashboard for the CIPHER-X system:

- `app/main.py` — Streamlit application entry point
- `app/data_loader.py` — Cached data ingestion and zero-crash fallback engine
- `app/map_view.py` — Interactive Leaflet/Folium GIS map with color-coded polygons
- `app/aoi_inspector.py` — Detailed polygon inspector with spectral and ML telemetry
- Temporal Before/After satellite comparison and CVA heatmap visualizer
- Macro statistics, class distributions, and ML feature importance analytics

## How to Run

```bash
streamlit run app/main.py
```

Opens in your browser at `http://localhost:8501`.
