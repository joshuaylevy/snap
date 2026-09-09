#!/usr/bin/env python3
"""2610_download_us_atlas.py — pinned, idempotent download of the US county topology.

Fetches the us-atlas TopoJSON (counties + states, pre-projected AlbersUSA plane) that
the waiver-map artifact inlines. One pinned version, one file, sha256-verified: on the
first run EXPECTED_SHA256 is None and the script prints the observed hash to hardcode
here; thereafter any mismatch is a hard failure (supply-chain / silent-revision guard).
Lands in 1_data/10_raw/103_geo/1031_us_atlas/ (gitignored; regenerable) with a manifest,
same etiquette as 2130 (browser UA, delay, retries).

Usage:
    python 2_scripts/26_present/261_waiver_map/2610_download_us_atlas.py
    python 2_scripts/26_present/261_waiver_map/2610_download_us_atlas.py --force
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
US_ATLAS_DIR = GEO_DIR / "1031_us_atlas"
MANIFEST_CSV = US_ATLAS_DIR / "10310_us_atlas_manifest.csv"

US_ATLAS_VERSION = "3.0.1"
US_ATLAS_URL = f"https://cdn.jsdelivr.net/npm/us-atlas@{US_ATLAS_VERSION}/counties-10m.json"
DEST = US_ATLAS_DIR / "counties-10m.json"

# Pinned content hash of us-atlas@3.0.1 counties-10m.json. None = bootstrap mode:
# fetch, print the observed hash, and exit nonzero with instructions to pin it.
EXPECTED_SHA256 = "145aaf5d1433352a6a1d8e86b5f149c7c653f9171baf14aaf75ee66575def1b0"

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
REQUEST_DELAY_S = 1.5
TIMEOUT_S = 120
MAX_RETRIES = 4

MANIFEST_FIELDS = ["source_tag", "url", "version", "local_path", "http_code", "sha256",
                   "n_bytes", "downloaded_at", "status"]


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def curl_download(url, dest, ua):
    """Download url -> dest via curl. Returns (http_code, n_bytes); retries w/ backoff."""
    code = "ERR"
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
    return code, 0


def write_manifest(row):
    with MANIFEST_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="refetch even if hash matches")
    args = ap.parse_args()

    US_ATLAS_DIR.mkdir(parents=True, exist_ok=True)

    if (not args.force and DEST.exists() and EXPECTED_SHA256
            and sha256_file(DEST) == EXPECTED_SHA256):
        print(f"[us-atlas] {DEST} already present, sha256 matches pin — nothing to do")
        return

    code, n_bytes = curl_download(US_ATLAS_URL, DEST, BROWSER_UA)
    ok = code.startswith("2") and n_bytes > 0
    observed = sha256_file(DEST) if ok else ""
    write_manifest({
        "source_tag": "us_atlas_counties_10m", "url": US_ATLAS_URL,
        "version": US_ATLAS_VERSION, "local_path": str(DEST),
        "http_code": code, "sha256": observed, "n_bytes": n_bytes,
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "ok" if ok else "failed",
    })
    if not ok:
        sys.exit(f"[us-atlas] FAILED (code={code})")
    print(f"[us-atlas] fetched {n_bytes:,} bytes, sha256={observed}")

    if EXPECTED_SHA256 is None:
        sys.exit("[us-atlas] no pin set: paste the hash above into EXPECTED_SHA256 "
                 "in this script, then re-run to verify")
    if observed != EXPECTED_SHA256:
        sys.exit(f"[us-atlas] sha256 MISMATCH — expected {EXPECTED_SHA256}. Upstream "
                 "content changed for a pinned version; investigate before trusting it.")
    print("[us-atlas] sha256 matches pin")


if __name__ == "__main__":
    main()
