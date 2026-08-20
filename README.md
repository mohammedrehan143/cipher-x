# CIPHER-X

Satellite-based change detection system for the SIH 2026 Space-Tech MVP.

## MVP Pipeline

Sentinel-2 BEFORE/AFTER
? Preprocessing
? Change Vector Analysis (CVA)
? Change Mask
? Polygons / Features
? Random Forest
? GeoJSON / GIS
? Streamlit Dashboard

## Project Structure

CIPHER-X/
+-- app/
+-- data/
¦   +-- sentinel/
¦   ¦   +-- before/
¦   ¦   +-- after/
¦   +-- aoi/
¦   +-- processed/
+-- models/
+-- notebooks/
+-- outputs/
¦   +-- maps/
¦   +-- polygons/
¦   +-- predictions/
+-- src/
¦   +-- preprocessing/
¦   +-- cva/
¦   +-- vectorization/
¦   +-- features/
¦   +-- models/
+-- .gitignore
+-- LICENSE
+-- README.md
+-- requirements.txt

## Setup

pip install -r requirements.txt

## Scope

The current MVP uses Sentinel-2 imagery and a classical computer-vision / machine-learning pipeline.

LISS-4 processing and Siamese CNN are postponed to a future/optional stage.

## License

See LICENSE.
