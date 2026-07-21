#!/usr/bin/env python3
"""2121_download_fna_waiver_docs.py — deterministic, resumable download of FNA waiver docs.

Reads the recon link map (2120), downloads each document into a per-FY-batch folder, hashes
the content (sha256), and records everything in a manifest. Resumable: a document already on
disk whose sha256 matches the manifest is skipped without re-fetching. Rate-limited and polite
(browser UA, request delay, exponential backoff). Run from the project root, `snap` env.

Usage:
    python 2_scripts/21_scrape_dl/212_fna_timelimit/2121_download_fna_waiver_docs.py
    python .../2121_download_fna_waiver_docs.py --batches 1997-1999 2015-2019   # subset
    python .../2121_download_fna_waiver_docs.py --limit 20                       # pilot
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
FNA_DIR = RAW_DIR / "102_fna"
RECON_CSV = FNA_DIR / "1020_recon_link_map.csv"
DOCS_DIR = FNA_DIR / "1020_timelimit_waiver_docs"
MANIFEST_CSV = FNA_DIR / "1020_download_manifest.csv"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
REQUEST_DELAY_S = 1.5          # polite spacing between fetches
TIMEOUT_S = 90
MAX_RETRIES = 4

MANIFEST_FIELDS = ["doc_url", "batch", "batch_url", "file_name", "link_text",
                   "state", "doc_class", "fiscal_year", "local_path",
                   "http_code", "sha256", "n_bytes", "downloaded_at", "status"]


def batch_folder(batch):
    """'1997-1999' -> 'FY1997-1999' (per-FY-batch subfolder name)."""
    return "FY" + batch


def curl_download(url, dest):
    """Download url -> dest via curl (HTTP/1.1, follow 302 to Azure Front Door).

    Returns (http_code, n_bytes). Retries with polite exponential backoff.
    """
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        cmd = ["curl", "-sS", "--http1.1", "-L", "-A", USER_AGENT,
               "--connect-timeout", "20", "--max-time", str(TIMEOUT_S),
               "-o", str(dest), "-w", "%{http_code}", url]
        try:
            code = subprocess.run(cmd, capture_output=True, check=True
                                  ).stdout.decode(errors="replace").strip()
            if code.startswith("2") and dest.exists() and dest.stat().st_size > 0:
                return code, dest.stat().st_size
            last = f"HTTP {code}, size={dest.stat().st_size if dest.exists() else 0}"
        except subprocess.CalledProcessError as e:
            last = f"curl exit {e.returncode}: {e.stderr.decode(errors='replace')[:200]}"
        time.sleep(REQUEST_DELAY_S * 2 * attempt)
    return "ERR", 0  # caller records failure; last reason surfaced via stderr
    # (last kept for debugging)


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
        return {r["doc_url"]: r for r in csv.DictReader(fh)}


def write_manifest(by_url):
    rows = sorted(by_url.values(), key=lambda r: (r["batch"], r["file_name"]))
    with MANIFEST_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="*", default=None,
                    help="subset of FY-batch labels, e.g. 1997-1999 2015-2019")
    ap.add_argument("--limit", type=int, default=None,
                    help="pilot: stop after N new downloads")
    args = ap.parse_args()

    if not RECON_CSV.exists():
        sys.exit(f"missing {RECON_CSV}; run 2120_recon_fna_site.py first")
    with RECON_CSV.open(newline="") as fh:
        docs = list(csv.DictReader(fh))
    if args.batches:
        wanted = set(args.batches)
        docs = [d for d in docs if d["batch"] in wanted]

    manifest = load_manifest()
    n_new = n_skip = n_fail = 0
    for i, d in enumerate(docs, 1):
        url = d["doc_url"]
        folder = DOCS_DIR / batch_folder(d["batch"])
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / d["file_name"]

        prev = manifest.get(url)
        if (prev and prev.get("status") == "ok" and dest.exists()
                and prev.get("sha256") and sha256_file(dest) == prev["sha256"]):
            n_skip += 1
            continue

        code, n_bytes = curl_download(url, dest)
        ok = code.startswith("2") and n_bytes > 0
        sha = sha256_file(dest) if ok else ""
        manifest[url] = {
            "doc_url": url, "batch": d["batch"], "batch_url": d["batch_url"],
            "file_name": d["file_name"], "link_text": d["link_text"],
            "state": d["state"], "doc_class": d["doc_class"],
            "fiscal_year": d["fiscal_year"],
            "local_path": str(dest), "http_code": code, "sha256": sha,
            "n_bytes": n_bytes,
            "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "ok" if ok else "failed",
        }
        if ok:
            n_new += 1
        else:
            n_fail += 1
            print(f"[dl] FAILED {url} (code={code})", file=sys.stderr)

        if n_new % 25 == 0 and n_new:
            write_manifest(manifest)  # periodic checkpoint
        if n_new and i % 20 == 0:
            print(f"[dl] {i}/{len(docs)} processed "
                  f"(new={n_new} skip={n_skip} fail={n_fail})", file=sys.stderr)
        if args.limit and n_new >= args.limit:
            print(f"[dl] --limit {args.limit} reached", file=sys.stderr)
            break
        time.sleep(REQUEST_DELAY_S)

    write_manifest(manifest)
    print(f"[dl] done: new={n_new} skipped={n_skip} failed={n_fail} "
          f"total_manifest={len(manifest)} -> {MANIFEST_CSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
