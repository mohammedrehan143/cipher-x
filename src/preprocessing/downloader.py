"""
Sentinel-2 Auto-Downloader
Uses Copernicus Data Space Ecosystem (CDSE) OData API to search and download S2 L2A data.

Usage:
    from src.preprocessing.downloader import download_sentinel2

    download_sentinel2(
        aoi="POLYGON((77.0 8.0, 77.1 8.0, 77.1 8.1, 77.0 8.1, 77.0 8.0))",
        before_date=("2024-01-01", "2024-01-31"),
        after_date=("2024-06-01", "2024-06-30"),
        before_dir="data/sentinel/before",
        after_dir="data/sentinel/after",
        max_cloud=20,
    )

CLI:
    python -m src.preprocessing.downloader --aoi "77.0,8.0,77.1,8.1" \\
        --before "2024-01-01,2024-01-31" \\
        --after "2024-06-01,2024-06-30"
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

BAND_PATTERNS = {
    "B02": ["_B02_10m.jp2", "_B02_10m.tif"],
    "B03": ["_B03_10m.jp2", "_B03_10m.tif"],
    "B04": ["_B04_10m.jp2", "_B04_10m.tif"],
    "B08": ["_B08_10m.jp2", "_B08_10m.tif"],
    "SCL": ["_SCL_20m.jp2", "_SCL_20m.tif"],
}

CDSE_AUTH_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"

BANDS_NEEDED = ["B02", "B03", "B04", "B08", "SCL"]


def _get_token(username: str, password: str) -> str:
    """Authenticate with CDSE and get access token."""
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "client_id": "cdse-public",
    }
    resp = requests.post(CDSE_AUTH_URL, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _aoi_bbox_to_wkt(bbox_str: str) -> str:
    """Convert 'lon1,lat1,lon2,lat2' to WKT POLYGON."""
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"AOI must be 'lon1,lat1,lon2,lat2', got: {bbox_str}")
    lon1, lat1, lon2, lat2 = parts
    return f"POLYGON(({lon1} {lat1},{lon2} {lat1},{lon2} {lat2},{lon1} {lat2},{lon1} {lat1}))"


def _date_range_to_filter(start: str, end: str) -> str:
    """Build OData date filter string."""
    return f"ContentDate/Start ge {start}T00:00:00.000Z and ContentDate/Start le {end}T23:59:59.999Z"


def search_products(
    aoi_wkt: str,
    date_start: str,
    date_end: str,
    max_cloud: int = 20,
    token: Optional[str] = None,
) -> list:
    """
    Search CDSE catalog for Sentinel-2 L2A products.

    Args:
        aoi_wkt: WKT polygon string
        date_start: YYYY-MM-DD
        date_end: YYYY-MM-DD
        max_cloud: maximum cloud cover percentage
        token: auth token (optional, for authenticated requests)

    Returns:
        List of product dicts sorted by cloud cover (ascending)
    """
    aoi_encoded = quote(aoi_wkt)
    date_filter = _date_range_to_filter(date_start, date_end)

    filter_str = (
        f"Collection/Name eq 'SENTINEL-2' "
        f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' "
        f"and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A') "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{aoi_encoded}') "
        f"and {date_filter} "
        f"and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' "
        f"and att/OData.CSC.DoubleAttribute/Value le {max_cloud:.1f}) "
        f"contains(tolower(Name),'productdiurnal') eq false"
    )

    params = {
        "$filter": filter_str,
        "$orderby": "Attributes/OData.CSC.DoubleAttribute/Value asc",
        "$top": 5,
    }

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"       Querying CDSE catalog...")
    resp = requests.get(CDSE_CATALOG_URL, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    products = data.get("value", [])
    print(f"       Found {len(products)} products")
    return products


def _find_best_product(products: list, prefer_tile: Optional[str] = None) -> Optional[dict]:
    """Pick the product with lowest cloud cover. Optionally prefer a specific tile."""
    if not products:
        return None

    if prefer_tile:
        tile_matches = [p for p in products if prefer_tile in p.get("Name", "")]
        if tile_matches:
            return tile_matches[0]

    return products[0]


def download_product(product: dict, output_dir: str, token: str) -> Path:
    """
    Download a product ZIP from CDSE.

    Returns:
        Path to downloaded ZIP file
    """
    product_id = product["Id"]
    product_name = product["Name"]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / f"{product_name}.zip"
    if zip_path.exists():
        print(f"       Already downloaded: {zip_path.name}")
        return zip_path

    url = CDSE_DOWNLOAD_URL.format(product_id=product_id)
    headers = {"Authorization": f"Bearer {token}"}

    print(f"       Downloading {product_name}...")
    print(f"         This may take 1-5 minutes depending on scene size...")

    resp = requests.get(url, headers=headers, stream=True, timeout=300)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192 * 16):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded / total * 100
                mb = downloaded / 1024 / 1024
                print(f"\r         {mb:.1f} MB / {total/1024/1024:.1f} MB ({pct:.0f}%)", end="", flush=True)

    print()
    return zip_path


def extract_bands(zip_path: Path, target_dir: str) -> dict:
    """
    Extract required bands from a Sentinel-2 ZIP file.

    Returns:
        Dict of {band_name: extracted_path} for each band found
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    extracted = {}
    print(f"       Extracting bands to {target_dir}/")

    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            for band, patterns in BAND_PATTERNS.items():
                if band in extracted:
                    continue
                for pattern in patterns:
                    if name.endswith(pattern) and "/IMG_DATA/" in name:
                        # Extract just the file (flatten path)
                        data = zf.read(name)
                        out_name = Path(name).name
                        out_path = target_dir / out_name
                        with open(out_path, "wb") as f:
                            f.write(data)
                        extracted[band] = out_path
                        print(f"         {band}: {out_name}")
                        break

    missing = [b for b in BANDS_NEEDED if b not in extracted]
    if missing:
        print(f"       [WARNING] Missing bands: {missing}")

    return extracted


def download_sentinel2(
    aoi: str,
    before_date: tuple,
    after_date: tuple,
    before_dir: str = "data/sentinel/before",
    after_dir: str = "data/sentinel/after",
    max_cloud: int = 20,
    username: Optional[str] = None,
    password: Optional[str] = None,
    prefer_tile: Optional[str] = None,
) -> dict:
    """
    Full auto-download pipeline for Sentinel-2 data.

    Args:
        aoi: bounding box as "lon1,lat1,lon2,lat2" or WKT POLYGON
        before_date: (start, end) as ("YYYY-MM-DD", "YYYY-MM-DD")
        after_date: (start, end) as ("YYYY-MM-DD", "YYYY-MM-DD")
        before_dir: output directory for BEFORE bands
        after_dir: output directory for AFTER bands
        max_cloud: maximum cloud cover percentage
        username: CDSE username (or env var COPERNICUS_USERNAME)
        password: CDSE password (or env var COPERNICUS_PASSWORD)
        prefer_tile: optional tile code to prefer (e.g., "T43PFP")

    Returns:
        Dict with download status
    """
    # Load credentials
    username = username or os.getenv("COPERNICUS_USERNAME")
    password = password or os.getenv("COPERNICUS_PASSWORD")

    if not username or not password:
        print("[ERROR] CDSE credentials not found.")
        print("  Set COPERNICUS_USERNAME and COPERNICUS_PASSWORD in .env")
        print("  Or pass username= and password= to this function.")
        sys.exit(1)

    # Convert AOI to WKT if needed
    if aoi.startswith("POLYGON"):
        aoi_wkt = aoi
    else:
        aoi_wkt = _aoi_bbox_to_wkt(aoi)

    # Authenticate
    print("[DOWNLOAD] Authenticating with Copernicus Data Space...")
    token = _get_token(username, password)
    print("       Auth OK.")

    results = {"before": None, "after": None}

    for label, date_range, target_dir in [
        ("BEFORE", before_date, before_dir),
        ("AFTER", after_date, after_dir),
    ]:
        print(f"\n[DOWNLOAD] Searching {label} scene ({date_range[0]} to {date_range[1]})...")

        products = search_products(
            aoi_wkt, date_range[0], date_range[1], max_cloud, token
        )

        if not products:
            print(f"       [ERROR] No {label} products found. Try wider date range or higher cloud limit.")
            continue

        # Show top 3
        for i, p in enumerate(products[:3]):
            cloud = next(
                (a["Value"] for a in p.get("Attributes", [])
                 if a.get("Name") == "cloudCover"),
                "?",
            )
            print(f"       {i+1}. {p['Name'][:60]}... cloud={cloud}%")

        best = _find_best_product(products, prefer_tile)
        if not best:
            print(f"       [ERROR] No suitable {label} product found.")
            continue

        cloud_val = next(
            (a["Value"] for a in best.get("Attributes", [])
             if a.get("Name") == "cloudCover"),
            "?",
        )
        print(f"       Selected: {best['Name'][:60]}... cloud={cloud_val}%")

        # Download
        cache_dir = Path("data/sentinel/.cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        zip_path = download_product(best, str(cache_dir), token)

        # Extract bands
        print(f"       Extracting bands for {label}...")
        extracted = extract_bands(zip_path, target_dir)

        results[label.lower()] = extracted
        found = len(extracted)
        print(f"       {label}: {found}/{len(BANDS_NEEDED)} bands extracted")

    # Summary
    print(f"\n[DOWNLOAD] Summary:")
    for label, extracted in results.items():
        if extracted:
            print(f"  {label.upper()}: {len(extracted)} bands in {before_dir if label == 'before' else after_dir}/")
        else:
            print(f"  {label.upper()}: FAILED")

    return results


def main():
    parser = argparse.ArgumentParser(description="Download Sentinel-2 data from Copernicus")
    parser.add_argument("--aoi", required=True, help="AOI as 'lon1,lat1,lon2,lat2' or WKT POLYGON")
    parser.add_argument("--before", required=True, help="Before date range: YYYY-MM-DD,YYYY-MM-DD")
    parser.add_argument("--after", required=True, help="After date range: YYYY-MM-DD,YYYY-MM-DD")
    parser.add_argument("--max-cloud", type=int, default=20, help="Max cloud cover %% (default: 20)")
    parser.add_argument("--before-dir", default="data/sentinel/before")
    parser.add_argument("--after-dir", default="data/sentinel/after")
    parser.add_argument("--tile", default=None, help="Prefer this tile code (e.g., T43PFP)")
    args = parser.parse_args()

    before_start, before_end = args.before.split(",")
    after_start, after_end = args.after.split(",")

    download_sentinel2(
        aoi=args.aoi,
        before_date=(before_start.strip(), before_end.strip()),
        after_date=(after_start.strip(), after_end.strip()),
        before_dir=args.before_dir,
        after_dir=args.after_dir,
        max_cloud=args.max_cloud,
        prefer_tile=args.tile,
    )


if __name__ == "__main__":
    main()
