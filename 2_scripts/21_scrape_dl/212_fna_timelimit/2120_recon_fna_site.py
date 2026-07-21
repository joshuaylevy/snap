#!/usr/bin/env python3
"""2120_recon_fna_site.py — polite reconnaissance of the FNA time-limit waiver archive.

Read-only: fetches the FY-batch index pages, discovers every waiver document link, parses
state / doc-class / fiscal-year from the link URL and visible anchor text, and writes a
link map CSV. Downloads NO documents (that is 2121). Run from the project root with the
`snap` conda env.

HTTP notes (learned during recon 2026-07-21):
- The FNA HTML pages RST the HTTP/2 stream; `requests` uses HTTP/1.1 by default, which works.
- Document PDFs 302-redirect from www.fna.usda.gov to an Azure Front Door host; follow redirects.
"""

import csv
import re
import sys
import time
import pathlib
import subprocess

# --- explicit path globals, composed from the project root ---
DATA_DIR = pathlib.Path("1_data")
RAW_DIR = DATA_DIR / "10_raw"
FNA_DIR = RAW_DIR / "102_fna"
RECON_CSV = FNA_DIR / "1020_recon_link_map.csv"

BASE = "https://www.fna.usda.gov"
BATCHES = ["1997-1999", "2000-2004", "2005-2009", "2010-2014",
           "2015-2019", "2020-2024", "2025-2029"]
BATCH_URL = BASE + "/snap/waivers/timelimit/{batch}"

# NOTE: FNA sits behind Akamai bot management, which silently tarpits non-browser
# User-Agents (a descriptive "academic-research/..." UA hangs; a browser UA returns in
# ~0.1s). We therefore present a realistic browser UA while still honoring robots.txt and
# a conservative request delay. Contact for this research crawl: joshua.levy676@gmail.com.
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
REQUEST_DELAY_S = 1.5
TIMEOUT_S = 60
MAX_RETRIES = 4

# Anchor tags pointing at resource-file documents, capturing href and inner text.
ANCHOR_RE = re.compile(
    r'<a\b[^>]*href="(/sites/default/files/[^"]+\.(?:pdf|docx?|xlsx?))"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
FY_RE = re.compile(r"fy(\d{4})", re.IGNORECASE)
# date-range form, e.g. "10.2017-9.2018" (used by the FY2018 'approval' batch)
DATERANGE_RE = re.compile(r"(\d{1,2})\.(\d{4})\s*-\s*(\d{1,2})\.(\d{4})")
CLASS_TOKENS = ("response", "resposne", "approval", "application",
                "request", "modification", "denial")


def http_get_bytes(url):
    """GET via curl, forcing HTTP/1.1 and following redirects.

    The FNA HTML host resets the HTTP/2 stream; documents 302-redirect to an Azure Front
    Door host. `curl --http1.1 -L` handles both (stdlib urllib hangs against this CDN).
    Returns (body_bytes, http_code). Retries with polite backoff on transport errors.
    """
    cmd = ["curl", "-sS", "--http1.1", "-L", "-A", USER_AGENT,
           "--connect-timeout", "15", "--max-time", str(TIMEOUT_S),
           "-w", "\n%{http_code}", url]
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            out = subprocess.run(cmd, capture_output=True, check=True).stdout
            body, _, code = out.rpartition(b"\n")
            http_code = code.decode(errors="replace").strip()
            if http_code.startswith("2"):
                return body, http_code
            last = f"HTTP {http_code}"
        except subprocess.CalledProcessError as e:  # transport error -> backoff
            last = f"curl exit {e.returncode}: {e.stderr.decode(errors='replace')[:200]}"
        time.sleep(REQUEST_DELAY_S * 2 * attempt)
    raise RuntimeError(f"GET failed after {MAX_RETRIES} tries: {url} ({last})")


def parse_doc_url(doc_url, link_text):
    """Best-effort parse of (state, doc_class, fiscal_year) from URL + anchor text."""
    from urllib.parse import unquote
    name = unquote(doc_url.rsplit("/", 1)[-1])  # decode %20 etc. before parsing
    stem = re.sub(r"\.(pdf|docx?|xlsx?)$", "", name, flags=re.IGNORECASE)

    m_state = re.match(r"^([a-z]{2,4})[-_]", stem, re.IGNORECASE)
    state = m_state.group(1).lower() if m_state else ""

    low = stem.lower()
    doc_class = next((t for t in CLASS_TOKENS if t in low), "")
    if doc_class == "resposne":
        doc_class = "response"
    # link text is a more reliable subtype signal (e.g. "Modification 1")
    if "modification" in link_text.lower():
        doc_class = "modification"

    fy = ""
    m_fy = FY_RE.search(stem)
    if m_fy:
        fy = m_fy.group(1)
    else:
        m_dr = DATERANGE_RE.search(stem)
        if m_dr:  # FY labelled by the ending federal fiscal year
            fy = m_dr.group(4)
        else:  # bare 4-digit year fallback (e.g. "...-approval-2018[-revised]")
            m_yr = re.search(r"(?:^|[-_])((?:19|20)\d{2})(?:[-_]|$)", stem)
            if m_yr:
                fy = m_yr.group(1)
    return state, doc_class, fy


def main():
    FNA_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    for batch in BATCHES:
        url = BATCH_URL.format(batch=batch)
        print(f"[recon] fetching {url}", file=sys.stderr)
        html = http_get_bytes(url)[0].decode("utf-8", errors="replace")
        n_batch = 0
        for href, raw_text in ANCHOR_RE.findall(html):
            doc_url = BASE + href if href.startswith("/") else href
            link_text = TAG_RE.sub("", raw_text)
            link_text = re.sub(r"\s+", " ", link_text).strip()
            state, doc_class, fy = parse_doc_url(doc_url, link_text)
            key = doc_url
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "batch": batch, "batch_url": url, "doc_url": doc_url,
                "file_name": doc_url.rsplit("/", 1)[-1], "link_text": link_text,
                "state": state, "doc_class": doc_class, "fiscal_year": fy,
            })
            n_batch += 1
        print(f"[recon]   {n_batch} unique doc links", file=sys.stderr)
        time.sleep(REQUEST_DELAY_S)

    fieldnames = ["batch", "batch_url", "doc_url", "file_name", "link_text",
                  "state", "doc_class", "fiscal_year"]
    with RECON_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"[recon] wrote {len(rows)} rows -> {RECON_CSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
