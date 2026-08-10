#!/usr/bin/env python3
"""2130_download_geo_reference.py — polite, idempotent download of geographic reference files.

Fetches the raw inputs for the state geography context build (2131): Census county
adjacency files (2010 + 2025 vintages), Census ANSI/FIPS code lists (counties, places,
county subdivisions, AIANNH areas), and the BLS LAUS area registry. Everything lands in
1_data/10_raw/103_geo/ (gitignored; regenerable) and is recorded in a manifest with
sha256 hashes. Resumable: a file already on disk whose sha256 matches the manifest is
skipped. Run from the project root, `snap` env.

Census files are fetched with a browser UA (www2.census.gov serves static files).
BLS blocks generic clients on download.bls.gov: those fetches send an honest
research-contact User-Agent instead. If BLS still refuses, the script prints
manual-download instructions and continues — hand-placed files are hashed into the
manifest on the next run.

Usage:
    python 2_scripts/21_scrape_dl/213_geo/2130_download_geo_reference.py
    python .../2130_download_geo_reference.py --only bls_laus      # retry one source
    python .../2130_download_geo_reference.py --force              # refetch everything
"""

import argparse
import csv
import hashlib
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone

# --- explicit path globals, composed from the project root ---
DATA_DIR = pathlib.Path("1_data")
RAW_DIR = DATA_DIR / "10_raw"
GEO_DIR = RAW_DIR / "103_geo"
MANIFEST_CSV = GEO_DIR / "1030_geo_download_manifest.csv"

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
# download.bls.gov 403s generic fetchers; BLS asks automated clients to identify
# themselves with a contact address.
BLS_UA = "snap-abawd-research/1.0 (joshua.levy676@gmail.com)"

REQUEST_DELAY_S = 1.5
TIMEOUT_S = 120
MAX_RETRIES = 4

# (source_tag, url, dest filename, user_agent)
FETCHES = [
    ("census_adjacency_2010",
     "https://www2.census.gov/geo/docs/reference/county_adjacency.txt",
     "county_adjacency_2010.txt", BROWSER_UA),
    ("census_adjacency_2025",
     "https://www2.census.gov/geo/docs/reference/county_adjacency/county_adjacency2025.txt",
     "county_adjacency_2025.txt", BROWSER_UA),
    ("census_ansi_county_2010",
     "https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt",
     "national_county_2010.txt", BROWSER_UA),
    ("census_ansi_county_2020",
     "https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt",
     "national_county_2020.txt", BROWSER_UA),
    ("census_place_by_county_2020",
     "https://www2.census.gov/geo/docs/reference/codes2020/national_place_by_county2020.txt",
     "national_place_by_county_2020.txt", BROWSER_UA),
    ("census_cousub_2020",
     "https://www2.census.gov/geo/docs/reference/codes2020/national_cousub2020.txt",
     "national_cousub_2020.txt", BROWSER_UA),
    ("census_aiannh_2020",
     "https://www2.census.gov/geo/docs/reference/codes2020/national_aiannh2020.txt",
     "national_aiannh_2020.txt", BROWSER_UA),
    ("bls_laus_area",
     "https://download.bls.gov/pub/time.series/la/la.area",
     "la.area", BLS_UA),
    ("bls_laus_area_type",
     "https://download.bls.gov/pub/time.series/la/la.area_type",
     "la.area_type", BLS_UA),
]

MANIFEST_FIELDS = ["source_tag", "url", "local_path", "http_code", "sha256",
                   "n_bytes", "downloaded_at", "status"]


def curl_download(url, dest, ua):
    """Download url -> dest via curl. Returns (http_code, n_bytes); retries w/ backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        cmd = ["curl", "-sS", "--http1.1", "-L", "-A", ua,
               "--connect-timeout", "20", "--max-time", str(TIMEOUT_S),
               "-o", str(dest), "-w", "%{http_code}", url]
        try:
            code = subprocess.run(cmd, capture_output=True, check=True
                                  ).stdout.decode(errors="replace").strip()
            if code.startswith("2") and dest.exists() and dest.stat().st_size > 0:
                return code, dest.stat().st_size
        except subprocess.CalledProcessError as e:
            code = f"curl_exit_{e.returncode}"
        time.sleep(REQUEST_DELAY_S * 2 * attempt)
    return code if code else "ERR", 0


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest():
    if not MANIFEST_CSV.exists():
        return {}
    with MANIFEST_CSV.open(newline="") as fh:
        return {r["source_tag"]: r for r in csv.DictReader(fh)}


def write_manifest(by_tag):
    rows = sorted(by_tag.values(), key=lambda r: r["source_tag"])
    with MANIFEST_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(rows)


def record(manifest, tag, url, dest, code, ok):
    manifest[tag] = {
        "source_tag": tag, "url": url, "local_path": str(dest),
        "http_code": code, "sha256": sha256_file(dest) if ok else "",
        "n_bytes": dest.stat().st_size if dest.exists() else 0,
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "ok" if ok else "failed",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None,
                    help="subset of source tags, e.g. bls_laus_area census_aiannh_2020")
    ap.add_argument("--force", action="store_true", help="refetch even if hash matches")
    args = ap.parse_args()

    GEO_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    fetches = FETCHES
    if args.only:
        wanted = set(args.only)
        unknown = wanted - {t for t, *_ in FETCHES}
        if unknown:
            sys.exit(f"unknown source tags: {sorted(unknown)}")
        fetches = [f for f in FETCHES if f[0] in wanted]

    n_new = n_skip = n_fail = 0
    for tag, url, fname, ua in fetches:
        dest = GEO_DIR / fname
        prev = manifest.get(tag)

        # hand-placed file (e.g. after a BLS manual download): hash it into the manifest
        if dest.exists() and (not prev or prev.get("status") != "ok") and not args.force:
            record(manifest, tag, url, dest, "manual", ok=True)
            print(f"[geo] {tag}: found file on disk, recorded as manual placement")
            n_new += 1
            continue

        if (not args.force and prev and prev.get("status") == "ok" and dest.exists()
                and prev.get("sha256") and sha256_file(dest) == prev["sha256"]):
            n_skip += 1
            continue

        code, n_bytes = curl_download(url, dest, ua)
        ok = code.startswith("2") and n_bytes > 0
        record(manifest, tag, url, dest, code, ok)
        if ok:
            n_new += 1
            print(f"[geo] fetched {tag} ({n_bytes:,} bytes)")
        else:
            n_fail += 1
            print(f"[geo] FAILED {tag} (code={code})", file=sys.stderr)
            if ua is BLS_UA:
                print(f"[geo]   BLS refused the fetch. Manual fallback: open\n"
                      f"[geo]     {url}\n"
                      f"[geo]   in a browser and save the file to\n"
                      f"[geo]     {dest}\n"
                      f"[geo]   then re-run this script (it will hash the file in).",
                      file=sys.stderr)
        time.sleep(REQUEST_DELAY_S)

    write_manifest(manifest)
    print(f"[geo] done: new={n_new} skipped={n_skip} failed={n_fail} "
          f"-> {MANIFEST_CSV}", file=sys.stderr)
    if n_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
