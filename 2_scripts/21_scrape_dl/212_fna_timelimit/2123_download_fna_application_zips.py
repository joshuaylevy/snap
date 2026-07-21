#!/usr/bin/env python3
"""2123_download_fna_application_zips.py — fetch + extract the FNA "State Requests and Data" zips.

The FNA time-limit waiver pages link, alongside the per-state FNS/FNA *response* PDFs, a set of
per-FY `FY####-ABAWD-State-Requests-and-Data.zip` bundles. These hold the STATE APPLICATIONS
(requests) and supporting data (unemployment spreadsheets, LSA lists, cover memos, maps),
organized in per-state subfolders. This script discovers, downloads (deterministic, resumable,
rate-limited), verifies (sha256), and extracts them into a per-FY tree, and records a manifest
of both the zips and every extracted file (content-hashed). Run from project root, `snap` env.

Usage:
    python 2_scripts/21_scrape_dl/212_fna_timelimit/2123_download_fna_application_zips.py
    python .../2123_download_fna_application_zips.py --fys 2013 2019     # subset by FY
"""

import argparse
import csv
import hashlib
import pathlib
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone

# --- explicit path globals, composed from the project root ---
DATA_DIR = pathlib.Path("1_data")
RAW_DIR = DATA_DIR / "10_raw"
FNA_DIR = RAW_DIR / "102_fna"
APP_DIR = FNA_DIR / "1023_application_docs"          # extracted, per-FY
ZIP_STAGE = APP_DIR / "_zips"                         # downloaded .zip bundles (staging)
ZIP_MANIFEST = FNA_DIR / "1023_application_zip_manifest.csv"
FILE_MANIFEST = FNA_DIR / "1023_application_file_inventory.csv"

BASE = "https://www.fna.usda.gov"
BATCHES = ["1997-1999", "2000-2004", "2005-2009", "2010-2014",
           "2015-2019", "2020-2024", "2025-2029"]
BATCH_URL = BASE + "/snap/waivers/timelimit/{batch}"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
REQUEST_DELAY_S = 1.5
TIMEOUT_S = 300  # zips are up to ~100 MB
MAX_RETRIES = 4

ZIP_HREF_RE = re.compile(
    r'href="(/sites/default/files/resource-files/[^"]*\.zip)"', re.IGNORECASE)
FY_IN_ZIP_RE = re.compile(r"FY(\d{4})", re.IGNORECASE)

ZIP_FIELDS = ["zip_url", "file_name", "fiscal_year", "state_range", "local_zip_path",
              "http_code", "sha256", "n_bytes", "n_extracted", "downloaded_at", "status"]
FILE_FIELDS = ["document_id", "fiscal_year", "zip_file_name", "state_dir",
               "rel_path", "local_path", "n_bytes", "ext"]


def curl(url, dest=None):
    """curl GET (HTTP/1.1, follow 302). If dest given, save there and return (code, bytes);
    else return (code, body_bytes). Retries with polite backoff."""
    base = ["curl", "-sS", "--http1.1", "-L", "-A", USER_AGENT,
            "--connect-timeout", "20", "--max-time", str(TIMEOUT_S)]
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if dest is not None:
                cmd = base + ["-o", str(dest), "-w", "%{http_code}", url]
                code = subprocess.run(cmd, capture_output=True, check=True
                                      ).stdout.decode(errors="replace").strip()
                if code.startswith("2") and dest.exists() and dest.stat().st_size > 0:
                    return code, dest.stat().st_size
                last = f"HTTP {code}"
            else:
                cmd = base + ["-w", "\n%{http_code}", url]
                out = subprocess.run(cmd, capture_output=True, check=True).stdout
                body, _, code = out.rpartition(b"\n")
                if code.decode().strip().startswith("2"):
                    return code.decode().strip(), body
                last = f"HTTP {code.decode().strip()}"
        except subprocess.CalledProcessError as e:
            last = f"curl exit {e.returncode}"
        time.sleep(REQUEST_DELAY_S * 2 * attempt)
    return "ERR", (0 if dest is not None else b"")


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_zip_urls():
    urls = {}
    for batch in BATCHES:
        print(f"[zip] recon {batch}", file=sys.stderr)
        _, html = curl(BATCH_URL.format(batch=batch))
        html = html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html
        for href in ZIP_HREF_RE.findall(html):
            urls[BASE + href] = href.rsplit("/", 1)[-1]
        time.sleep(REQUEST_DELAY_S)
    return urls  # {url: file_name}


def parse_zip_name(file_name):
    m = FY_IN_ZIP_RE.search(file_name)
    fy = m.group(1) if m else ""
    # state-range suffix after "...-Data" (e.g. "AK-to-MI", "MN-to-WV", "OR-WI-7-2026")
    m2 = re.search(r"Requests-and-Data-(.+?)\.zip$", file_name, re.IGNORECASE)
    state_range = m2.group(1) if m2 else "all"
    return fy, state_range


def load_csv(path):
    return {r[list(r)[0]]: r for r in csv.DictReader(path.open(newline=""))} if path.exists() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fys", nargs="*", default=None, help="subset of fiscal years, e.g. 2013 2019")
    args = ap.parse_args()

    ZIP_STAGE.mkdir(parents=True, exist_ok=True)
    zip_urls = discover_zip_urls()
    if args.fys:
        want = set(args.fys)
        zip_urls = {u: n for u, n in zip_urls.items() if parse_zip_name(n)[0] in want}
    print(f"[zip] {len(zip_urls)} zip bundles to process", file=sys.stderr)

    zman = load_csv(ZIP_MANIFEST)
    file_rows = []
    for url, file_name in sorted(zip_urls.items(), key=lambda kv: kv[1]):
        fy, state_range = parse_zip_name(file_name)
        zpath = ZIP_STAGE / file_name

        prev = zman.get(url)
        need_dl = not (prev and prev.get("status") == "ok" and zpath.exists()
                       and prev.get("sha256") and sha256_file(zpath) == prev["sha256"])
        if need_dl:
            print(f"[zip] downloading {file_name}", file=sys.stderr)
            code, n_bytes = curl(url, zpath)
            ok = code.startswith("2") and n_bytes > 0 and zipfile.is_zipfile(zpath)
            sha = sha256_file(zpath) if ok else ""
        else:
            code, n_bytes, ok, sha = "200", int(prev["n_bytes"]), True, prev["sha256"]

        n_extracted = 0
        if ok:
            fy_dir = APP_DIR / f"FY{fy}"
            fy_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zpath) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    # extract preserving internal ".../{STATE}/file" structure under FY dir
                    target = fy_dir / info.filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists() or target.stat().st_size != info.file_size:
                        with zf.open(info) as src, target.open("wb") as dst:
                            dst.write(src.read())
                    n_extracted += 1
                    parts = pathlib.PurePosixPath(info.filename).parts
                    state_dir = parts[1] if len(parts) >= 3 else ""
                    file_rows.append({
                        "document_id": sha256_file(target),
                        "fiscal_year": fy, "zip_file_name": file_name,
                        "state_dir": state_dir, "rel_path": info.filename,
                        "local_path": str(target), "n_bytes": info.file_size,
                        "ext": target.suffix.lower().lstrip("."),
                    })
            print(f"[zip]   extracted {n_extracted} files -> {fy_dir}", file=sys.stderr)

        zman[url] = {
            "zip_url": url, "file_name": file_name, "fiscal_year": fy,
            "state_range": state_range, "local_zip_path": str(zpath),
            "http_code": code, "sha256": sha, "n_bytes": n_bytes,
            "n_extracted": n_extracted,
            "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "ok" if ok else "failed",
        }
        if not ok:
            print(f"[zip] FAILED {file_name} (code={code})", file=sys.stderr)
        with ZIP_MANIFEST.open("w", newline="") as fh:  # checkpoint each zip
            w = csv.DictWriter(fh, fieldnames=ZIP_FIELDS)
            w.writeheader()
            w.writerows(sorted(zman.values(), key=lambda r: r["file_name"]))
        time.sleep(REQUEST_DELAY_S)

    # Merge with any existing inventory so a --fys subset run does not clobber other FYs:
    # drop prior rows for the zips processed this run, then add this run's rows.
    processed_zips = {r["file_name"] for r in
                      (zman[u] for u in zip_urls)}
    merged = {}
    if FILE_MANIFEST.exists():
        for r in csv.DictReader(FILE_MANIFEST.open(newline="")):
            if r["zip_file_name"] not in processed_zips:
                merged[(r["zip_file_name"], r["rel_path"])] = r
    for r in file_rows:
        merged[(r["zip_file_name"], r["rel_path"])] = r
    with FILE_MANIFEST.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FILE_FIELDS)
        w.writeheader()
        w.writerows(sorted(merged.values(), key=lambda r: (r["fiscal_year"], r["rel_path"])))
    ok_n = sum(1 for r in zman.values() if r["status"] == "ok")
    print(f"[zip] done: {ok_n}/{len(zman)} zips ok; {len(file_rows)} files extracted "
          f"-> {FILE_MANIFEST}", file=sys.stderr)


if __name__ == "__main__":
    main()
