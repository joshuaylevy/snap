#!/usr/bin/env python3
"""2131_build_geo_context.py — build per-state geography context files for extraction agents.

Offline, deterministic transform of the raw reference pulls (2130) + the hand-curated
county-change log (0_lit/01_geo/) into one agent-facing markdown file per state at
1_data/11_clean/111_geo_context/. Each file carries: the a-priori universe of areas a
state may request an ABAWD waiver for (BLS-LAUS units + LSA civil jurisdictions, framed
as a starting point, NOT an exclusive list), a canonical county/county-equivalent table
with FIPS codes and FY validity intervals, full symmetric county adjacency lists
(in-state neighbors, bare names, corner-touch pairs marked), LAUS cities >=25k with
parent counties, New England town lists, reservation names, and a state-specific
change log for the waiver era.

Run from the project root, `snap` env. Requires `make geo_fetch` to have run once.

Usage:
    python 2_scripts/21_scrape_dl/213_geo/2131_build_geo_context.py
    python .../2131_build_geo_context.py --states WI NC CT     # subset (still runs
                                                               # national asserts)

TODO(deferred): no deterministic post-extraction name validator in v1 — name validation
happens implicitly when extractions merge onto the optimal-application panel built from
BLS primitives; non-matches there surface typos/OCR errors. (Decision: Josh, 2026-08-10.)
"""

from __future__ import annotations

import argparse
import csv
import difflib
import pathlib
import re
import sys

import pandas as pd

# --- explicit path globals, composed from the project root ---
DATA_DIR = pathlib.Path("1_data")
RAW_GEO = DATA_DIR / "10_raw" / "103_geo"
LIT_GEO = pathlib.Path("0_lit") / "01_geo"
OUT_DIR = DATA_DIR / "11_clean" / "111_geo_context"
REPORT_CSV = OUT_DIR / "1110_build_report.csv"

ADJ_2010 = RAW_GEO / "county_adjacency_2010.txt"
ADJ_2025 = RAW_GEO / "county_adjacency_2025.txt"
ANSI_2020 = RAW_GEO / "national_county_2020.txt"
ANSI_2010 = RAW_GEO / "national_county_2010.txt"
PLACES_2020 = RAW_GEO / "national_place_by_county_2020.txt"
COUSUB_2020 = RAW_GEO / "national_cousub_2020.txt"
AIANNH_2020 = RAW_GEO / "national_aiannh_2020.txt"
LAUS_AREA = RAW_GEO / "la.area"
CT_XWALK = RAW_GEO / "ct_cou_to_cousub_crosswalk.txt"
CHANGES_CSV = LIT_GEO / "010_county_changes_1997_present.csv"

FNA_MANIFEST = DATA_DIR / "10_raw" / "102_fna" / "1020_download_manifest.csv"
GOLD_WI = DATA_DIR / "WI-hand-collected.xlsx"
GOLD_ND = DATA_DIR / "ND-hand-collected.xlsx"

NE_STATES = {"CT", "MA", "RI", "ME", "NH", "VT"}
# corpus filename codes that are not plain USPS state codes
CODE_ALIASES = {"GUAM": "GU", "NYC": "NY"}

# strip these trailing type words to get the bare name used in adjacency lists;
# longest-first so "City and Borough" wins over "Borough"
TYPE_SUFFIXES = [
    " City and Borough", " Planning Region", " Census Area", " Municipality",
    " Municipio", " Borough", " County", " Parish", " Island", " city/town",
    " city", " town",
]

EXPECTED_COUNTS = {"WI": 72, "NC": 100, "TX": 254, "VA": 133, "ND": 53}
NATIONAL_CURRENT_TOTAL = 3144  # 50 states + DC, incl. CT's 9 planning regions


# ---------------------------------------------------------------- parsing helpers
def _read_text(path: pathlib.Path) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("both", b"", 0, 1, f"cannot decode {path}")


def read_adjacency_2025() -> pd.DataFrame:
    """Pipe-delimited, header row, no self-rows; isolates have empty neighbor fields.
    Returns columns: geoid, name, n_geoid, n_name, length (NaN for isolates)."""
    df = pd.read_csv(ADJ_2025, sep="|", dtype=str, encoding="utf-8-sig")
    df.columns = ["name", "geoid", "n_name", "n_geoid", "length"]
    df["length"] = pd.to_numeric(df["length"], errors="coerce")
    return df


def read_adjacency_2010() -> tuple:
    """Tab-delimited, quoted names, continuation rows blank in the first two fields.
    Self-rows are asserted then dropped. Returns (df[geoid, name, n_geoid, n_name],
    universe {geoid: name}) — the universe keeps isolate counties (e.g. Hawaii's
    single-island counties) whose only row is their self-row."""
    rows, cur_name, cur_geoid = [], None, None
    selfrow_geoids, universe = set(), {}
    for line in _read_text(ADJ_2010).splitlines():
        if not line.strip():
            continue
        f = line.split("\t")
        if len(f) < 4:
            continue
        if f[1].strip():  # new county block (name cell is blank once — Watonwan, MN)
            cur_name, cur_geoid = f[0].strip().strip('"'), f[1].strip()
        n_name, n_geoid = f[2].strip().strip('"'), f[3].strip()
        if not n_geoid:
            continue
        if n_geoid == cur_geoid:
            selfrow_geoids.add(cur_geoid)
            if not cur_name:  # backfill the blank name cell from the self-row
                cur_name = n_name
            universe[cur_geoid] = cur_name
            continue
        universe.setdefault(cur_geoid, cur_name)
        rows.append({"geoid": cur_geoid, "name": cur_name,
                     "n_geoid": n_geoid, "n_name": n_name})
    df = pd.DataFrame(rows)
    missing_self = set(df["geoid"]) - selfrow_geoids
    assert not missing_self, f"2010 adjacency: counties w/o self-row: {sorted(missing_self)[:5]}"
    return df, universe


def assert_symmetric(df: pd.DataFrame, tag: str) -> None:
    pairs = set(zip(df["geoid"], df["n_geoid"]))
    asym = {(a, b) for (a, b) in pairs if (b, a) not in pairs}
    assert not asym, f"{tag}: asymmetric pairs, e.g. {sorted(asym)[:5]}"


def read_ansi(path: pathlib.Path, pipe: bool) -> pd.DataFrame:
    """Returns columns: usps, geoid, name."""
    if pipe:
        df = pd.read_csv(path, sep="|", dtype=str, encoding="utf-8-sig")
        df = df.rename(columns={"STATE": "usps", "COUNTYNAME": "name"})
    else:
        df = pd.read_csv(path, sep=",", dtype=str, encoding="latin-1", header=None,
                         names=["usps", "STATEFP", "COUNTYFP", "name", "CLASSFP"])
    df["geoid"] = df["STATEFP"] + df["COUNTYFP"]
    return df[["usps", "geoid", "name"]]


def read_laus_cities() -> pd.DataFrame:
    """LAUS type G (cities/towns >=25k) and H (NE cities/towns <25k) areas.
    Returns: area_type, state_fips, name (e.g. 'Beloit city'), usps."""
    df = pd.read_csv(LAUS_AREA, sep="\t", dtype=str)
    df = df[df["area_type_code"].isin(["G", "H"])].copy()
    df["state_fips"] = df["area_code"].str[2:4]
    split = df["area_text"].str.rsplit(", ", n=1)
    df["name"] = split.str[0]
    df["usps"] = split.str[1]
    return df[["area_type_code", "state_fips", "name", "usps"]]


def read_aiannh() -> pd.DataFrame:
    """Reservation/tribal-area names per state (STATES column is '~'-separated)."""
    df = pd.read_csv(AIANNH_2020, sep="|", dtype=str, encoding="utf-8-sig")
    df = df.assign(usps=df["STATES"].str.split("~")).explode("usps")
    return df[["AIANNHNAME", "usps"]].rename(columns={"AIANNHNAME": "name"})


AIANNH_SUFFIXES = [
    " Reservation and Off-Reservation Trust Land", " Indian Community",
    " Indian Reservation", " Community", " Reservation",
]


def aiannh_short(official: str) -> str:
    """'Oneida (WI) Reservation' -> 'Oneida'; 'Sokaogon Chippewa Community' ->
    'Sokaogon Chippewa'. Documents usually print the short form."""
    s = re.sub(r"\s*\([^)]*\)", "", official).strip()
    for suf in AIANNH_SUFFIXES:
        if s.endswith(suf):
            return s[: -len(suf)]
    return s


def read_parent_counties() -> dict:
    """(usps, unit name lowercased) -> sorted list of county names, from the
    place-by-county file with the county-subdivision file as fallback."""
    out: dict = {}
    deep: dict = {}
    for path, name_col in ((PLACES_2020, "PLACENAME"), (COUSUB_2020, "COUSUBNAME")):
        df = pd.read_csv(path, sep="|", dtype=str, encoding="utf-8-sig")
        for r in df.itertuples(index=False):
            nm = getattr(r, name_col)
            out.setdefault((r.STATE, nm.lower()), set()).add(r.COUNTYNAME)
            deep.setdefault((r.STATE, town_deep(nm).lower()), set()).add(r.COUNTYNAME)
    # deep-normalized keys only fill gaps; exact keys win
    for k, v in deep.items():
        out.setdefault(k, v)
    return {k: sorted(v) for k, v in out.items()}


_TOWN_SUFFIX_RE = re.compile(
    r"\s+(city|town|borough|village|plantation|township|grant|purchase|location|gore"
    r"|ut|unorganized(?: territory)?|county)(/(city|town|borough))?$", re.IGNORECASE)


def town_bare(name: str) -> str:
    """'Milford city (balance)' -> 'Milford'; 'Naugatuck borough/town' -> 'Naugatuck';
    'Ansonia city/town' -> 'Ansonia'. Display + join form for NE town names."""
    s = re.sub(r"\s*\([^)]*\)", "", str(name)).strip()
    return _TOWN_SUFFIX_RE.sub("", s)


def town_deep(name: str) -> str:
    """town_bare applied to a fixpoint: 'Amesbury Town city' -> 'Amesbury'.
    Last-resort join key only — can over-strip names like 'Old Town city'."""
    s = town_bare(name)
    while True:
        t = _TOWN_SUFFIX_RE.sub("", s)
        if t == s:
            return s
        s = t


def ct_key(name: str) -> str:
    """Normalized join key for CT town names ('Ansonia city/town' == 'Ansonia town')."""
    return town_bare(name).lower()


def read_ct_town_regions() -> dict:
    """CT bare town name (lowercased) -> (legacy county name, planning region name)."""
    df = pd.read_csv(CT_XWALK, sep="|", dtype=str, encoding="utf-8-sig")
    df.columns = [re.sub(r"\s+", " ", c).strip() for c in df.columns]
    old_i = next(i for i, c in enumerate(df.columns) if "OLD_COUNTY_NAMELSAD" in c)
    new_i = next(i for i, c in enumerate(df.columns) if "NEW_COUNTY_NAMELSAD" in c)
    town_i = next(i for i, c in enumerate(df.columns) if "COUSUB_NAMELSAD" in c)
    out = {}
    for r in df.itertuples(index=False):
        out[ct_key(r[town_i])] = (str(r[old_i]), str(r[new_i]))
    return out


# ---------------------------------------------------------------- name handling
def bare_name(full: str) -> str:
    """'Adams County' -> 'Adams'; 'Juneau City and Borough' -> 'Juneau';
    'Richmond city' -> 'Richmond'. Collision handling is done per state."""
    for suf in TYPE_SUFFIXES:
        if full.endswith(suf):
            return full[: -len(suf)]
    return full


def display_names(fulls: list) -> dict:
    """full official name -> display name. Bare name unless two units in the state
    would collide (e.g. 'Richmond city' vs 'Richmond County'), which keep the suffix."""
    bares: dict = {}
    for f in fulls:
        bares.setdefault(bare_name(f), []).append(f)
    return {f: (b if len(fs) == 1 else f) for b, fs in bares.items() for f in fs}


def strip_state(name: str) -> str:
    """'Adams County, WI' -> 'Adams County'."""
    return name.rsplit(", ", 1)[0]


# ---------------------------------------------------------------- change log
def load_changes() -> pd.DataFrame:
    df = pd.read_csv(CHANGES_CSV, dtype=str).fillna("")
    df["first_affected_fy"] = df["first_affected_fy"].astype(int)
    return df


def post2010_expected_diffs(changes: pd.DataFrame) -> set:
    """GEOIDs allowed to differ between the 2010 and 2025 adjacency vintages."""
    allowed = set()
    for r in changes.itertuples(index=False):
        if int(r.first_affected_fy) <= 2010:
            continue
        for col in (r.old_fips, r.new_fips):
            allowed |= {g.strip() for g in col.split(";") if g.strip()}
    return allowed


# ---------------------------------------------------------------- per-state assembly
HEADER_TEMPLATE = """# {state_name} — geographic reference for ABAWD waiver extraction

Generated by 2_scripts/21_scrape_dl/213_geo/2131_build_geo_context.py — do not hand-edit.
Sources: Census county adjacency files (2010 and 2025 vintages), Census ANSI/FIPS code
lists (2020), BLS LAUS area registry (current vintage), Census AIANNH national file,
curated county-change log (0_lit/01_geo/).

## How to use this file (read first)

- PURPOSE. Reference for (a) verifying transcriptions of geographic names from
  scanned/typed waiver PDFs and (b) judging whether a set of areas could form one
  geographically contiguous group.
- THIS LIST IS A STARTING POINT, NOT EXCLUSIVE. It covers the areas with standard
  BLS/LAUS unemployment data, which is what FNS guidance (7 CFR 273.24(f)(2)) anchors
  waiver requests to: the whole state, counties/county-equivalents, cities of 25,000+,
  New England cities and towns, and metro / labor-market-area aggregates of them — plus
  DOL Labor Surplus Area "civil jurisdictions" (largely the same universe: counties,
  balance-of-county, cities 25,000+, certain towns). States CAN and DO request other
  areas: Indian reservations (evaluated with BIA data), and occasionally non-standard
  geographies (e.g., Wisconsin requested ZIP-code areas in FY2025; FNS denied them).
  An area absent from this file is NOT, by itself, evidence of a transcription error.
- TRANSCRIPTION. Always record the document's printed string verbatim in `orig_text`.
  If the printed name is within a character or two of exactly one name below (e.g.
  "Pasguotank" vs "Pasquotank"), treat the reference spelling as the intended area for
  the `name` field. Never force a match; if nothing here is close, keep the printed
  name as-is and flag it.
- CONTIGUITY. Since 2016, FNS requires that a jointly-evaluated group of areas be
  geographically contiguous OR constitute an economic region (e.g. a labor market
  area). Use the adjacency lists below to check whether a candidate bundle is connected
  (a set is contiguous if you can walk from any member to any other through listed
  neighbors). Contiguity is corroborating evidence only — follow your extraction
  spec's decision rules; if a document's named set is non-contiguous, keep the set as
  the document draws it and note the tension. Pairs marked "(corner-touch only)" meet
  at a single point, not a shared border.
- Adjacency is COUNTY-LEVEL and IN-STATE only. For cities, towns, and reservations,
  reason at the level of their parent counties (listed below).
"""


def county_table_rows(state_fips, usps, cur_units, changes_st, ct_legacy=None):
    """Rows: (display, official, fips, valid, note). cur_units: {geoid: full_name}."""
    old_geoids = set()
    created_fy, dissolved = {}, {}
    for r in changes_st.itertuples(index=False):
        fy = int(r.first_affected_fy)
        for g in str(r.new_fips).split(";"):
            if g.strip():
                created_fy[g.strip()] = fy
        for g_, n_ in zip(str(r.old_fips).split(";"), str(r.old_name).split(";")):
            if g_.strip():
                old_geoids.add(g_.strip())
                dissolved[g_.strip()] = (n_.strip(), fy, r.change_type, r.note)

    fulls = [strip_state(n) for n in cur_units.values()]
    # legacy units that are NOT in the current universe get their own rows
    legacy = {g: v for g, v in dissolved.items() if g not in cur_units}
    fulls += [v[0] for v in legacy.values()]
    disp = display_names(sorted(set(fulls)))

    rows = []
    for g, full in sorted(cur_units.items(), key=lambda kv: strip_state(kv[1])):
        name = strip_state(full)
        fy0 = created_fy.get(g)
        valid = f"~{fy0}–" if fy0 and fy0 > 1997 else "1997–"
        note = ""
        if g in dissolved:  # renamed-in-place (kept code) e.g. Petersburg 02195
            old_nm, fy, _, _ = dissolved[g]
            note = f"before ~FY{fy}: {old_nm}"
        rows.append((disp[name], name, g, valid, note))
    for g, (old_nm, fy, ctype, note) in sorted(legacy.items(), key=lambda kv: kv[1][0]):
        rows.append((disp.get(old_nm, old_nm), old_nm, g, f"1997–~{fy}",
                     f"no longer exists ({ctype.replace('_', ' ')}; see changes below)"))
    return rows, disp


def adjacency_lines(state_fips, adj, disp, universe):
    """Full symmetric per-county neighbor lists, in-state only, bare display names.
    Zero-length (corner-touch) neighbors marked. Returns (lines, n_corner)."""
    sub = adj[(adj["geoid"].str[:2] == state_fips)]
    instate = sub[sub["n_geoid"].str[:2] == state_fips]
    by_geoid: dict = {g: [] for g in universe}
    n_corner = 0
    for r in instate.itertuples(index=False):
        nm = disp.get(strip_state(r.n_name), strip_state(r.n_name))
        corner = ("length" in instate.columns and pd.notna(r.length) and r.length == 0)
        n_corner += int(corner)
        by_geoid.setdefault(r.geoid, []).append(nm + (" (corner-touch only)" if corner else ""))
    lines = []
    for g in sorted(universe, key=lambda g: universe[g]):
        me = disp.get(strip_state(universe[g]), strip_state(universe[g]))
        nbrs = sorted(set(by_geoid.get(g, [])))
        lines.append(f"{me}: {', '.join(nbrs) if nbrs else '(none — no in-state land neighbor)'}")
    return lines, n_corner // 2


def fy_of_date(iso: str) -> int:
    y, m = int(iso[:4]), int(iso[5:7])
    return y + 1 if m >= 10 else y


def changes_section(changes_st) -> list:
    lines = []
    for r in changes_st.itertuples(index=False):
        lines.append(f"- **{r.effective_date}** ({r.change_type.replace('_', ' ')}): "
                     f"{r.old_name.replace(';', '; ') or '—'} → "
                     f"{r.new_name.replace(';', '; ') or 'dissolved'}. {r.note}")
    return lines


def build_state(usps, state_name, state_fips, data, args):
    adj25, adj10 = data["adj25"], data["adj10"]
    changes_st = data["changes"][data["changes"]["state"] == usps]

    # current county universe from the 2025 adjacency file (isolates included)
    sub = adj25[adj25["geoid"].str[:2] == state_fips]
    cur_units = dict(sorted(set(zip(sub["geoid"], sub["name"]))))
    assert cur_units, f"{usps}: no units in 2025 adjacency"

    ct_mode = usps == "CT"
    rows, disp = county_table_rows(state_fips, usps, cur_units, changes_st)

    md = [HEADER_TEMPLATE.format(state_name=state_name)]

    # --- counties table
    unit_word = "planning regions" if ct_mode else "counties / county-equivalents"
    n_cur = len(cur_units)
    md.append(f"\n## {unit_word.capitalize()} ({n_cur} current; FIPS; validity in federal FYs)\n")
    if ct_mode:
        md.append("Connecticut replaced its 8 counties with 9 planning regions as "
                  "county-equivalents (adopted June 2022; Census products switched over "
                  "2023–2024). Documents through ~FY2023 use counties (legacy layer "
                  "below); later documents use planning regions. The regions do NOT "
                  "nest inside the old counties.\n")
    md.append("| Name (used in adjacency lists) | Official name | FIPS | Valid (FY) | Note |")
    md.append("|---|---|---|---|---|")
    for d, full, g, valid, note in rows:
        md.append(f"| {d} | {full} | {g} | {valid} | {note} |")

    # --- adjacency (current vintage)
    md.append(f"\n## {'Planning region' if ct_mode else 'County'} adjacency "
              f"(each unit: ALL its in-state neighbors)\n")
    lines, n_corner = adjacency_lines(state_fips, adj25, disp, cur_units)
    md.extend(lines)
    md.append("\n(Out-of-state neighbors are omitted. \"(corner-touch only)\" = the two "
              "units meet at a single point, not a shared border.)")

    # --- CT legacy dual layer
    if ct_mode:
        sub10 = adj10[adj10["geoid"].str[:2] == "09"]
        legacy_units = dict(sorted(set(zip(sub10["geoid"], sub10["name"]))))
        ldisp = display_names([strip_state(n) for n in legacy_units.values()])
        md.append(f"\n## Legacy counties ({len(legacy_units)}; used in documents through ~FY2023)\n")
        md.append("| Name | FIPS | Valid (FY) |")
        md.append("|---|---|---|")
        for g, full in sorted(legacy_units.items(), key=lambda kv: kv[1]):
            md.append(f"| {strip_state(full)} | {g} | 1997–~2023 |")
        md.append("\n## Legacy county adjacency (documents through ~FY2023)\n")
        llines, _ = adjacency_lines("09", adj10, ldisp, legacy_units)
        md.extend(llines)

    # --- LAUS cities / NE towns
    laus_st = data["laus"][data["laus"]["usps"] == usps]
    parents = data["parents"]
    n_cities = n_towns = 0
    if usps in NE_STATES:
        towns = sorted(laus_st["name"])
        n_towns = len(towns)
        md.append(f"\n## Cities and towns with standard LAUS data ({n_towns}; ALL New "
                  f"England cities/towns have their own series, any size)\n")
        if ct_mode:
            ct_map = data["ct_towns"]
            by_region: dict = {}
            by_county: dict = {}
            for t in towns:
                old_c, new_r = ct_map.get(ct_key(t), ("(unmatched)", "(unmatched)"))
                by_region.setdefault(bare_name(new_r), []).append(town_bare(t))
                by_county.setdefault(bare_name(old_c), []).append(town_bare(t))
            md.append("Grouped by CURRENT planning region:\n")
            for k in sorted(by_region):
                md.append(f"- {k}: {', '.join(sorted(by_region[k]))}")
            md.append("\nGrouped by LEGACY county (documents through ~FY2023):\n")
            for k in sorted(by_county):
                md.append(f"- {k}: {', '.join(sorted(by_county[k]))}")
        else:
            by_county: dict = {}
            for t in towns:
                cs = (parents.get((usps, t.lower()))
                      or parents.get((usps, town_deep(t).lower()), ["(unmatched)"]))
                for c in cs:
                    by_county.setdefault(c, []).append(town_bare(t))
            md.append("Grouped by county:\n")
            for k in sorted(by_county):
                md.append(f"- {k}: {', '.join(sorted(set(by_county[k])))}")
    else:
        cities = sorted(laus_st[laus_st["area_type_code"] == "G"]["name"])
        n_cities = len(cities)
        if cities:
            md.append(f"\n## Cities with standard LAUS data (population 25,000+; "
                      f"{n_cities}; current vintage — a city's absence here does not "
                      f"invalidate an older waiver, membership churns with population)\n")
            md.append("| City | Parent county(ies) |")
            md.append("|---|---|")
            for c in cities:
                cs = parents.get((usps, c.lower()))
                md.append(f"| {c} | {', '.join(cs) if cs else '(not matched)'} |")

    # --- reservations
    aiannh_st = data["aiannh"][data["aiannh"]["usps"] == usps]
    n_resv = len(aiannh_st)
    if n_resv:
        md.append(f"\n## American Indian / Alaska Native / tribal areas ({n_resv}; "
                  f"permitted waiver areas, evaluated with BIA — not BLS — data; "
                  f"county overlaps not listed in v1)\n")
        md.append("Documents usually print the short form (e.g. \"Bad River\", "
                  "\"Oneida\") without the official Reservation/Community suffix.\n")
        md.append(", ".join(sorted(aiannh_st["name"])))

    # --- special notes
    if usps == "NY":
        md.append("\n## New York City\n")
        md.append("NYC waivers (documents filed under 'nyc') cover the five boroughs, "
                  "which are these five counties: Bronx, Kings (= Brooklyn), New York "
                  "(= Manhattan), Queens, Richmond (= Staten Island).")

    # --- changes
    md.append(f"\n## Changes to {state_name} geography since FY1997\n")
    ch = changes_section(changes_st)
    md.extend(ch if ch else ["None. Units are unchanged over the waiver period."])

    text = "\n".join(md) + "\n"
    out = OUT_DIR / f"{usps.lower()}_geo_context.md"
    out.write_text(text, encoding="utf-8")
    return {
        "state": usps, "n_current_units": n_cur, "n_legacy_rows": len(rows) - n_cur,
        "n_laus_cities": n_cities, "n_ne_towns": n_towns, "n_reservations": n_resv,
        "n_corner_pairs": n_corner, "est_tokens": len(text) // 4, "path": str(out),
    }


# ---------------------------------------------------------------- national asserts
def national_asserts(data):
    adj25, adj10, ansi20 = data["adj25"], data["adj10"], data["ansi20"]
    assert_symmetric(adj25.dropna(subset=["n_geoid"]), "2025 adjacency")
    assert_symmetric(adj10, "2010 adjacency")
    assert (adj25["geoid"] == adj25["n_geoid"]).sum() == 0, "2025: unexpected self-rows"

    # ANSI cross-check (50 states + DC, CT excepted — ANSI2020 still lists legacy counties)
    set25 = {g for g in set(adj25["geoid"]) if g[:2] <= "56"}
    set20 = {g for g in set(ansi20["geoid"]) if g[:2] <= "56"}
    diff = (set25 ^ set20) - {g for g in set25 | set20 if g.startswith("09")}
    assert not diff, f"2025 adjacency vs ANSI2020 mismatch outside CT: {sorted(diff)[:8]}"
    assert len(set25) == NATIONAL_CURRENT_TOTAL, \
        f"national current total {len(set25)} != {NATIONAL_CURRENT_TOTAL}"

    for usps, n in EXPECTED_COUNTS.items():
        fips = data["usps_to_fips"][usps]
        got = len({g for g in set25 if g[:2] == fips})
        assert got == n, f"{usps}: {got} units, expected {n}"
    for name in ("Pasquotank County, NC", "Perquimans County, NC"):
        assert (adj25["name"] == name).any(), f"missing {name}"

    # change-log accounting: every 2010<->2025 GEOID diff must be explained
    set10 = {g for g in data["adj10_universe"] if g[:2] <= "56"}
    allowed = post2010_expected_diffs(data["changes"])
    unexplained = {g for g in set10 ^ set25
                   if g not in allowed and not g.startswith("09")}
    assert not unexplained, f"GEOID diffs unexplained by change log: {sorted(unexplained)}"

    # Four Corners corner-touch presence (informational)
    fc = adj25[(adj25["geoid"] == "04001") & (adj25["n_geoid"] == "08083")]
    print(f"[geo] Four Corners point-contact pair present in 2025 file: {not fc.empty} "
          f"(length={fc['length'].iloc[0] if not fc.empty else 'n/a'})")


def gold_crosscheck(report_rows, data):
    """Non-fatal: compare gold xlsx unit names against the built lists."""
    for path, usps in ((GOLD_WI, "WI"), (GOLD_ND, "ND")):
        if not path.exists():
            print(f"[geo] gold file missing, skipping cross-check: {path}")
            continue
        gold = pd.read_excel(path)
        fips = data["usps_to_fips"][usps]
        sub = data["adj25"][data["adj25"]["geoid"].str[:2] == fips]
        cur = {bare_name(strip_state(n)) for n in sub["name"]}
        g_by_type = gold.groupby("geographic_unit_area_type")["geographic_unit_name"]
        for area_type, names in g_by_type:
            names = {str(n).strip() for n in names.dropna()}
            if area_type == "county":
                pool = cur
            elif area_type == "city":
                pool = {bare_name(n) for n in
                        data["laus"][data["laus"]["usps"] == usps]["name"]}
            elif area_type == "reservation area":
                official = set(data["aiannh"][data["aiannh"]["usps"] == usps]["name"])
                pool = official | {aiannh_short(n) for n in official}
            else:
                continue
            exact = {n for n in names if n in pool}
            fuzzy, miss = {}, []
            for n in names - exact:
                m = difflib.get_close_matches(n, sorted(pool), n=1, cutoff=0.75)
                (fuzzy.__setitem__(n, m[0]) if m else miss.append(n))
            print(f"[geo] gold {usps}/{area_type}: {len(exact)}/{len(names)} exact"
                  + (f", fuzzy {fuzzy}" if fuzzy else "")
                  + (f", UNMATCHED {miss}" if miss else ""))


def corpus_coverage(data):
    """Every state code in the FNA download manifest must resolve to an emitted file."""
    if not FNA_MANIFEST.exists():
        print("[geo] FNA manifest missing; skipping corpus-coverage check")
        return
    codes = {str(c).strip().upper() for c in
             pd.read_csv(FNA_MANIFEST, dtype=str)["state"].dropna()}
    missing = []
    for c in sorted(codes):
        u = CODE_ALIASES.get(c, c)
        if not (OUT_DIR / f"{u.lower()}_geo_context.md").exists():
            missing.append(c)
    assert not missing, f"corpus states with no context file: {missing}"
    print(f"[geo] corpus coverage: all {len(codes)} manifest state codes resolve "
          f"to a context file (aliases: {CODE_ALIASES})")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", nargs="*", default=None,
                    help="subset of USPS codes to (re)build, e.g. WI NC CT")
    args = ap.parse_args()

    for p in (ADJ_2010, ADJ_2025, ANSI_2020, LAUS_AREA, AIANNH_2020, CHANGES_CSV):
        if not p.exists():
            sys.exit(f"missing input {p}; run `make geo_fetch` first")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ansi20 = read_ansi(ANSI_2020, pipe=True)
    usps_to_fips = dict(sorted(set(zip(ansi20["usps"], ansi20["geoid"].str[:2]))))
    usps_to_fips.setdefault("DC", "11")
    adj10, adj10_universe = read_adjacency_2010()
    data = {
        "adj25": read_adjacency_2025(),
        "adj10": adj10,
        "adj10_universe": adj10_universe,
        "ansi20": ansi20,
        "laus": read_laus_cities(),
        "aiannh": read_aiannh(),
        "parents": read_parent_counties(),
        "ct_towns": read_ct_town_regions() if CT_XWALK.exists() else {},
        "changes": load_changes(),
        "usps_to_fips": usps_to_fips,
    }

    national_asserts(data)

    # state name lookup from the LAUS statewide rows
    la = pd.read_csv(LAUS_AREA, sep="\t", dtype=str)
    st_rows = la[la["area_type_code"] == "A"]
    fips_to_name = {r.area_code[2:4]: r.area_text for r in st_rows.itertuples(index=False)}
    fips_to_name.setdefault("11", "District of Columbia")
    fips_to_name.setdefault("66", "Guam")
    fips_to_name.setdefault("78", "U.S. Virgin Islands")

    targets = [(u, f) for u, f in usps_to_fips.items()
               if f <= "56" or u in ("GU", "VI")]
    targets = sorted(set(targets) | {("GU", "66"), ("VI", "78")})
    if args.states:
        wanted = {s.upper() for s in args.states}
        targets = [(u, f) for u, f in targets if u in wanted]

    report = []
    for usps, fips in targets:
        row = build_state(usps, fips_to_name.get(fips, usps), fips, data, args)
        report.append(row)
    rep = pd.DataFrame(report)
    rep.to_csv(REPORT_CSV, index=False)
    print(rep[["state", "n_current_units", "n_laus_cities", "n_ne_towns",
               "n_reservations", "n_corner_pairs", "est_tokens"]].to_string(index=False))
    big = rep[rep["est_tokens"] > 15000]
    if not big.empty:
        print(f"[geo] WARNING: files over ~15k tokens:\n{big[['state', 'est_tokens']]}")

    gold_crosscheck(report, data)
    if not args.states:
        corpus_coverage(data)
    print(f"[geo] wrote {len(report)} context files -> {OUT_DIR}")


if __name__ == "__main__":
    main()
