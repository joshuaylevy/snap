#!/usr/bin/env python3
"""
2226 — The FNA extraction PROGRESS TABLE (a.k.a. the tier table).

One markdown table, one row per state, answering "where does the extraction stand and
what is it worth extracting next". Columns:

    Code | Tier | Doc years | Docs | Units | Geo warts | Run | Last run
         | Gold: name | Gold: action | Gold: criterion

NOTHING in the table is hand-typed except the curated judgments in the registry
(`2226a_state_tier_registry.csv`): the tier, the unit vocabulary, and the geo-wart
sentence TEMPLATE. Every number is recomputed at render time from the pipeline's own
artifacts, so a stale count is not possible:

    Docs, Doc years  <- 1020_download_manifest.csv     (the scraped corpus)
    Units, laus/towns/reservations/legacy
                     <- 1110_build_report.csv          (the geography reference build)
    scanned (image-only docs)
                     <- 1021_doc_text_profile.csv      (cached pdftotext sweep; rebuilt
                                                        with --refresh-text-profile)
    Run, Last run    <- the extraction JSON tree + 10220_extraction_results.csv
    Gold: *          <- a live subprocess call to 2225 per gold state

Geo-wart templates interpolate {units} {laus} {towns} {resv} {legacy} {docs} {scanned}
{fy_min} {fy_max}, so a count inside a sentence tracks its source too. Prose-only warts
(bundling behaviour, sub-county filing practice) are judgments from reading the actual
"Requested Area(s)" paragraphs and must be edited by hand in the registry.

Run from the project root, `snap` env:
    python 2_scripts/22_extract/222_fna_waivers/2226_progress_table.py
    python 2_scripts/22_extract/222_fna_waivers/2226_progress_table.py --no-gold
    python 2_scripts/22_extract/222_fna_waivers/2226_progress_table.py --refresh-text-profile
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import pathlib
import re
import subprocess
import sys

# ---------------------------------------------------------------- path globals
# Composed from the project root down; the script is always run FROM the root.
DATA = pathlib.Path("1_data")
RAW = DATA / "10_raw"
CLEAN = DATA / "11_clean"
FNA = RAW / "102_fna"
DOCS_DIR = FNA / "1020_timelimit_waiver_docs"
DOWNLOAD_MANIFEST = FNA / "1020_download_manifest.csv"
TEXT_PROFILE = FNA / "1021_doc_text_profile.csv"
EXTRACTIONS = FNA / "1022_extractions"
LEDGER = EXTRACTIONS / "10220_extraction_results.csv"
GEO_CONTEXT = CLEAN / "111_geo_context"
GEO_BUILD_REPORT = GEO_CONTEXT / "1110_build_report.csv"

SCRIPTS = pathlib.Path("2_scripts")
FNA_EXTRACT = SCRIPTS / "22_extract" / "222_fna_waivers"
REGISTRY = FNA_EXTRACT / "2226a_state_tier_registry.csv"
VALIDATOR = FNA_EXTRACT / "2225_validate_vs_hand_collected.py"

# ---------------------------------------------------------------- conventions
# Arm directory -> short label shown next to the last-run date. A gold score is
# uninterpretable without knowing which spec produced it, so the arm rides along.
ARM_LABEL = {
    "claude": "v1_0", "claude_run2": "run2", "claude_v1_2_sonnet": "v1_2",
    "claude_v1_3_geo": "v1_3", "claude_v1_4_fedsusp": "v1_4",
    "claude_v1_5_adjud": "v1_5",
}
# The corpus files a handful of jurisdictions under their own label; fold them onto
# the state code the registry and geography reference use.
STATE_FOLD = {"GUAM": "GU", "NYC": "NY"}
# A run that is incomplete AND quiet for longer than this is stalled, not in flight.
IN_FLIGHT_SECONDS = 30 * 60

MARK_DONE, MARK_LIVE, MARK_PARTIAL, MARK_NONE = "✅", "🔄", "⚠️", "❌"
BLANK = "—"


def _fold(code: str) -> str:
    c = (code or "").strip().upper()
    return STATE_FOLD.get(c, c)


# ---------------------------------------------------------------- curated input
def read_registry() -> dict[str, dict]:
    if not REGISTRY.exists():
        sys.exit(f"missing tier registry: {REGISTRY}")
    return {r["state_code"]: r for r in csv.DictReader(REGISTRY.open())}


# ---------------------------------------------------------------- derived input
def read_corpus() -> dict[str, dict]:
    """Doc counts and fiscal-year span, per state, from the download manifest."""
    if not DOWNLOAD_MANIFEST.exists():
        sys.exit(f"missing download manifest: {DOWNLOAD_MANIFEST}\n"
                 f"  run `make fna_download` first.")
    out = collections.defaultdict(lambda: {"docs": 0, "fys": [], "paths": []})
    for r in csv.DictReader(DOWNLOAD_MANIFEST.open()):
        st = _fold(r["state"])
        out[st]["docs"] += 1
        out[st]["paths"].append(r["local_path"])
        try:
            out[st]["fys"].append(int(float(r["fiscal_year"])))
        except (TypeError, ValueError):
            pass
    return out


def read_geography() -> dict[str, dict]:
    """Unit counts from the geography reference build report."""
    if not GEO_BUILD_REPORT.exists():
        sys.exit(f"missing geography build report: {GEO_BUILD_REPORT}\n"
                 f"  run `make geo_context` first.")
    out = {}
    for r in csv.DictReader(GEO_BUILD_REPORT.open()):
        out[_fold(r["state"])] = {
            "units": int(r["n_current_units"]), "laus": int(r["n_laus_cities"]),
            "towns": int(r["n_ne_towns"]), "resv": int(r["n_reservations"]),
            "legacy": int(r["n_legacy_rows"]),
        }
    return out


def build_text_profile() -> None:
    """Sweep the corpus with pdftotext and cache (path, pages, textchars).

    Only `textchars == 0` (image-only, i.e. needs OCR) is used by the table, but pages
    is cheap to keep and is the other half of the reading-cost measure.
    """
    pdfs = sorted(DOCS_DIR.rglob("*.pdf"))
    if not pdfs:
        sys.exit(f"no PDFs under {DOCS_DIR}; run `make fna_download` first.")
    TEXT_PROFILE.parent.mkdir(parents=True, exist_ok=True)
    with TEXT_PROFILE.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "pages", "textchars"])
        for i, p in enumerate(pdfs, 1):
            try:
                txt = subprocess.run(["pdftotext", str(p), "-"], capture_output=True,
                                     timeout=120).stdout.decode("utf-8", "replace")
                pages = txt.count("\f") or 1
            except (OSError, subprocess.SubprocessError):
                txt, pages = "", 0
            w.writerow([str(p), pages, len(txt.strip())])
            if i % 100 == 0:
                print(f"  ... {i}/{len(pdfs)} PDFs profiled", file=sys.stderr)
    print(f"wrote {TEXT_PROFILE} ({len(pdfs)} PDFs)", file=sys.stderr)


def read_text_profile(corpus: dict[str, dict]) -> dict[str, int]:
    """Image-only doc count per state. Joined to the manifest on local_path, so the
    state attribution is the manifest's, not a filename guess."""
    if not TEXT_PROFILE.exists():
        build_text_profile()
    chars = {}
    for r in csv.DictReader(TEXT_PROFILE.open()):
        chars[r["path"]] = int(r["textchars"])
    scanned = collections.Counter()
    for st, c in corpus.items():
        for p in c["paths"]:
            if chars.get(p, -1) == 0:
                scanned[st] += 1
    return scanned


# ---------------------------------------------------------------- run state
def read_runs() -> dict[str, dict]:
    """Per state: the most recent arm, how many of its documents are written, and when.

    Timestamps prefer the ledger's `extracted_at` (authoritative, written at collate
    time) and fall back to file mtime, marked `~`, for arms never collated. That
    distinction matters: mtime is exactly what lets a half-finished run look finished.
    """
    ledger_ts: dict[tuple[str, str], str] = {}
    if LEDGER.exists():
        for r in csv.DictReader(LEDGER.open()):
            path = pathlib.PurePath(r.get("response_json_path", ""))
            arm = path.parts[4] if len(path.parts) > 4 else ""
            key = (_fold(r["state_code"]), arm)
            ts = (r.get("extracted_at") or "")[:10]
            if ts and ts > ledger_ts.get(key, ""):
                ledger_ts[key] = ts

    runs: dict[str, dict] = collections.defaultdict(dict)
    if EXTRACTIONS.exists():
        for arm_dir in sorted(p for p in EXTRACTIONS.iterdir() if p.is_dir()):
            per = collections.defaultdict(list)
            for j in arm_dir.rglob("*.json"):
                # The optional middle token matches mi-response-abawd-fy2008, the one
                # file in the corpus that puts the doc class before "abawd". Without it
                # that state reads one document short forever. Same fix as
                # _state_from_name in fna_extraction_results.py.
                m = re.match(r"([a-z]{2,4})-(?:[a-z]+-)?abawd-", j.name)
                if m:
                    per[_fold(m.group(1))].append(j.stat().st_mtime)
            for st, mtimes in per.items():
                runs[st][arm_dir.name] = (len(mtimes), max(mtimes))
    return runs, ledger_ts


def latest_arm(st: str, runs: dict) -> str | None:
    """The arm this state was most recently extracted under. The table reports this
    arm's run status, so it is also the arm gold must be scored against — otherwise
    the score describes a different run than the row it sits in."""
    arms = runs.get(st) or {}
    return max(arms, key=lambda a: arms[a][1]) if arms else None


def run_cell(st: str, docs: int, runs: dict, ledger_ts: dict) -> tuple[str, str]:
    arms = runs.get(st) or {}
    arm = latest_arm(st, runs)
    if arm is None:
        return MARK_NONE, BLANK
    n_json, mtime = arms[arm]
    now = datetime.datetime.now().timestamp()
    if n_json >= docs:
        mark = MARK_DONE
    elif (now - mtime) < IN_FLIGHT_SECONDS:
        mark = MARK_LIVE
    else:
        mark = MARK_PARTIAL

    stamp = ledger_ts.get((st, arm))
    if stamp:
        date = stamp
    else:
        date = "~" + datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    cell = f"{date} ({ARM_LABEL.get(arm, arm)})"
    if n_json < docs:
        cell += f" — {n_json}/{docs}"
    return mark, cell


# ---------------------------------------------------------------- gold scores
_TOTAL_RE = re.compile(r"^\s*canonical\s+name\s+(\S+\s+\([^)]*\))\s+"
                       r"action\s+(\S+\s+\([^)]*\))\s+criterion\s+(\S+\s+\([^)]*\))")


def gold_states() -> list[str]:
    return sorted(p.name.split("-")[0].upper() for p in DATA.glob("*-hand-collected.xlsx")
                  if not p.name.startswith("~$"))


def score_gold(state: str, arm_root: pathlib.Path | None) -> dict[str, str] | None:
    """Call 2225 and lift its TOTAL line. The `canonical` basis is reported; `exact`
    and `gold_repaired` agreeing with it is the standing no-typo regression check."""
    cmd = [sys.executable, str(VALIDATOR), "--state", state]
    if arm_root:
        cmd += ["--json-root", str(arm_root)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=900).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    tail = out.split("TOTAL")[-1] if "TOTAL" in out else ""
    for line in tail.splitlines():
        m = _TOTAL_RE.match(line)
        if not m:
            continue
        res = {"name": m.group(1), "action": m.group(2), "crit": m.group(3)}
        # A zero denominator is NOT a score -- 2225 prints "0/0 (n/a)" when it matched
        # nothing at all (corpus absent, JSONs missing, wrong arm). Rendering that in the
        # table would read as a result. Refuse it and let the cell fall back to BLANK.
        if res["name"].startswith("0/0"):
            print(f"WARNING: {state} scored nothing against gold (empty comparison) — "
                  f"check the corpus and that the arm actually holds {state} JSONs.",
                  file=sys.stderr)
            return None
        return res
    return None


# ---------------------------------------------------------------- render
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-gold", action="store_true",
                    help="skip the 2225 subprocess calls (fast; gold cells show n/r)")
    ap.add_argument("--arm", default=None,
                    help="score gold against this extraction root instead of the "
                         "validator's default (e.g. 1_data/.../claude_v1_4_fedsusp)")
    ap.add_argument("--refresh-text-profile", action="store_true",
                    help="re-sweep the corpus with pdftotext before rendering")
    args = ap.parse_args()

    if args.refresh_text_profile:
        build_text_profile()

    registry = read_registry()
    corpus = read_corpus()
    geo = read_geography()
    scanned = read_text_profile(corpus)
    runs, ledger_ts = read_runs()

    gold: dict[str, dict] = {}
    if not args.no_gold:
        for st in gold_states():
            if st not in registry:
                continue
            if args.arm:
                arm_root = pathlib.Path(args.arm)
            else:
                arm = latest_arm(st, runs)
                arm_root = EXTRACTIONS / arm if arm else None
            res = score_gold(st, arm_root)
            if res:
                gold[st] = res

    missing_geo = sorted(set(registry) - set(geo))
    rows = []
    for st, reg in registry.items():
        c = corpus.get(st, {"docs": 0, "fys": []})
        g = geo.get(st, {"units": 0, "laus": 0, "towns": 0, "resv": 0, "legacy": 0})
        fys = c["fys"]
        years = f"{min(fys)}–{max(fys)}" if fys else BLANK

        wart = reg["geo_wart"].format(
            units=g["units"], laus=g["laus"], towns=g["towns"], resv=g["resv"],
            legacy=g["legacy"], docs=c["docs"], scanned=scanned.get(st, 0),
            fy_min=min(fys) if fys else "?", fy_max=max(fys) if fys else "?",
        )

        if reg["unit_basis"] == "town":
            units_cell = f"{g['towns']} towns"
        elif reg["unit_noun"]:
            units_cell = f"{g['units']} {reg['unit_noun']}"
        else:
            units_cell = str(g["units"])

        mark, last = run_cell(st, c["docs"], runs, ledger_ts)
        sc = gold.get(st)
        rows.append([
            st, reg["tier"], years, str(c["docs"]), units_cell, wart, mark, last,
            sc["name"] if sc else BLANK,
            sc["action"] if sc else BLANK,
            sc["crit"] if sc else BLANK,
        ])

    rows.sort(key=lambda r: (float(registry[r[0]]["tier_order"]), int(r[3]), r[0]))

    hdr = ["Code", "Tier", "Doc years", "Docs", "Units", "Geo warts", "Run", "Last run",
           "Gold: name", "Gold: action", "Gold: criterion"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "|".join(["---"] * len(hdr)) + "|")
    for r in rows:
        print("| " + " | ".join(r) + " |")

    print()
    print(f"{MARK_DONE} complete · {MARK_LIVE} writing now (<30 min) · "
          f"{MARK_PARTIAL} incomplete and quiet · {MARK_NONE} never run. "
          f"Gold is 2225's `canonical` basis; {BLANK} = no hand-collected sheet for "
          f"that state. `~` on a date = file mtime, not a collated ledger entry.")
    if missing_geo:
        print(f"WARNING: no geography build-report row for {', '.join(missing_geo)}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
