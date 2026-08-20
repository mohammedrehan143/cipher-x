"""
CIPHER-X — Full Pipeline Runner
Runs all 4 stages in sequence with one command.

Usage:
    python run_all.py                                              # run with existing data
    python run_all.py --download --aoi "77.0,8.0,77.1,8.1"        # auto-download then run
        --before "2024-01-01,2024-01-31" --after "2024-06-01,2024-06-30"
    python run_all.py --skip-dashboard
"""

import argparse
import subprocess
import sys
from pathlib import Path


STAGES = [
    ("Person 1", "Preprocessing + CVA", ["python", "run_pipeline.py"]),
    ("Person 2", "Vectorization + Features", ["python", "run_vectorize.py"]),
    ("Person 3a", "Auto-Labels", ["python", "src/models/labeller.py"]),
    ("Person 3b", "Train Classifier", ["python", "src/models/classifier.py"]),
    ("Person 3c", "ML Inference", ["python", "run_classify.py"]),
]


def run_stage(person, name, cmd, extra_args=None):
    full_cmd = cmd + (extra_args or [])
    print(f"\n{'='*60}")
    print(f"  {person}: {name}")
    print(f"  > {' '.join(full_cmd)}")
    print(f"{'='*60}\n")

    result = subprocess.run(full_cmd)
    if result.returncode != 0:
        print(f"\n[ERROR] {person} ({name}) failed with exit code {result.returncode}")
        print("Fix the error above and re-run, or skip with --skip-stages")
        return False
    return True


def download_data(args):
    """Auto-download Sentinel-2 data from Copernicus."""
    from dotenv import load_dotenv
    load_dotenv()

    from src.preprocessing.downloader import download_sentinel2

    before_start, before_end = args.before_date.split(",")
    after_start, after_end = args.after_date.split(",")

    results = download_sentinel2(
        aoi=args.aoi,
        before_date=(before_start.strip(), before_end.strip()),
        after_date=(after_start.strip(), after_end.strip()),
        before_dir=args.before,
        after_dir=args.after,
        max_cloud=args.max_cloud,
        prefer_tile=args.tile,
    )

    # Verify bands were extracted
    before_dir = Path(args.before)
    after_dir = Path(args.after)

    for label, d in [("BEFORE", before_dir), ("AFTER", after_dir)]:
        tif_count = len(list(d.glob("*.tif")))
        jp2_count = len(list(d.glob("*.jp2")))
        total = tif_count + jp2_count
        if total < 5:
            print(f"[ERROR] {label} only has {total} band files (need 5). Download may have failed.")
            sys.exit(1)
        print(f"[OK] {label}: {total} band files ready")


def main():
    parser = argparse.ArgumentParser(description="CIPHER-X Full Pipeline")

    # Data paths
    parser.add_argument("--before", type=str, default="data/sentinel/before")
    parser.add_argument("--after", type=str, default="data/sentinel/after")

    # Download options
    parser.add_argument("--download", action="store_true",
                        help="Auto-download Sentinel-2 data before running pipeline")
    parser.add_argument("--aoi", type=str, default=None,
                        help="AOI bounding box: lon1,lat1,lon2,lat2 (requires --download)")
    parser.add_argument("--before-date", type=str, default=None,
                        help="Before date range: YYYY-MM-DD,YYYY-MM-DD (requires --download)")
    parser.add_argument("--after-date", type=str, default=None,
                        help="After date range: YYYY-MM-DD,YYYY-MM-DD (requires --download)")
    parser.add_argument("--max-cloud", type=int, default=20,
                        help="Max cloud cover %% for download (default: 20)")
    parser.add_argument("--tile", type=str, default=None,
                        help="Prefer this Sentinel-2 tile code (e.g., T43PFP)")

    # Pipeline options
    parser.add_argument("--skip-dashboard", action="store_true")
    parser.add_argument("--skip-stages", type=str, nargs="*", default=[],
                        help="Skip stages by number (1-5)")

    args = parser.parse_args()
    skip = set(int(s) for s in args.skip_stages)

    print("=" * 60)
    print("  CIPHER-X — Full Pipeline")
    print("=" * 60)

    # Step 0: Auto-download if requested
    if args.download:
        if not args.aoi or not args.before_date or not args.after_date:
            print("[ERROR] --download requires --aoi, --before-date, and --after-date")
            print("  Example: python run_all.py --download --aoi '77.0,8.0,77.1,8.1'")
            print("           --before '2024-01-01,2024-01-31' --after '2024-06-01,2024-06-30'")
            sys.exit(1)
        download_data(args)
    else:
        # Check if data exists
        before_dir = Path(args.before)
        after_dir = Path(args.after)

        if not before_dir.exists() or not any(before_dir.iterdir()):
            print(f"\n[ERROR] No data in {before_dir}/")
            print("Options:")
            print("  1. Drop band files manually into the folder")
            print("  2. Use --download flag with --aoi and --before-date/--after-date")
            sys.exit(1)

        if not after_dir.exists() or not any(after_dir.iterdir()):
            print(f"\n[ERROR] No data in {after_dir}/")
            print("Options:")
            print("  1. Drop band files manually into the folder")
            print("  2. Use --download flag with --aoi and --before-date/--after-date")
            sys.exit(1)

    print(f"\n  BEFORE: {args.before}")
    print(f"  AFTER:  {args.after}")

    # Build extra args for run_pipeline.py
    pipeline_args = ["--before", args.before, "--after", args.after]

    # Run stages
    for i, (person, name, cmd) in enumerate(STAGES, 1):
        if i in skip:
            print(f"\n[{i}/5] Skipping {person}: {name}")
            continue

        # Pass --before/--after only to run_pipeline.py
        extra = pipeline_args if "run_pipeline" in " ".join(cmd) else None

        ok = run_stage(person, name, cmd, extra)
        if not ok:
            sys.exit(1)

    # Launch dashboard
    if not args.skip_dashboard:
        print(f"\n{'='*60}")
        print("  Person 4: Streamlit Dashboard")
        print(f"{'='*60}")
        print("\nLaunching dashboard at http://localhost:8501")
        print("Press Ctrl+C to stop.\n")
        subprocess.run(["streamlit", "run", "app/main.py",
                        "--server.address", "localhost",
                        "--server.port", "8501"])
    else:
        print("\nDashboard skipped. Run manually: streamlit run app/main.py")


if __name__ == "__main__":
    main()
