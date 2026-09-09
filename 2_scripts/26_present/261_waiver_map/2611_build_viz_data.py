#!/usr/bin/env python3
"""2611_build_viz_data.py — collate extraction arms into the waiver-map viz payload.

Reads the per-document extraction JSONs of one or more arms, resolves every
county-equivalent unit name to a FIPS code via the state geography reference (exact
match, then the same <=2-edit unique-repair rule the validator uses), and emits ONE
deterministic JSON payload (schema wmap_v2) that the artifact assembler (2612)
inlines: state -> fiscal year -> documents -> groups -> units. Cities carry
parent-county FIPS instead of their own; reservation areas, statewide units and
non-standard geographies (ZCTA, LMA, ...) carry none and are rendered off-map by the
client. Discovery is fully state-agnostic: whatever states appear under the arms
appear in the payload.

ARM SELECTION. With no --arm, every spec-versioned arm on disk
(`claude_v<major>_<minor>_*`) is read in ASCENDING version order and a later arm
SUPERSEDES an earlier one document-by-document, so re-extracting a state under a new
spec updates the map with no code change and the map never mixes two specs for the
same document. Pre-spec arms (`claude`, `claude_run2`, `openai`) are never picked up
by default; name them explicitly to see them. `--arm A B` forces exactly that list,
in that precedence order (last wins). Each document carries the arm that supplied it.

Fiscal year comes from the doc stub (`...-fy2013`, or a month span like
`...-10.2017-9.2018`). A handful of stubs are named by calendar year only
(`ga-abawd-approval-2018`); those fall back to the FY of the waiver's actual
implementation date, then of the FNS response date, and the fallback is reported.
The untracked run ledger, when present, is only a cross-check.

Extension slots (null until a future build step fills them): per-unit `unemployment`
(LAUS level/rate for the application window) and per-unit/per-doc `optimality`.
Consumers ignore unknown keys, so new fields land without a client rework.

Known deferral: VA independent cities and CT vintage layers resolve against the
CURRENT reference vintage only; revisit with the county-changes log when those states
are extracted (see plan; 0_lit/01_geo/010_county_changes_1997_present.csv).

Usage (from project root, snap env):
    python 2_scripts/26_present/261_waiver_map/2611_build_viz_data.py
    python 2_scripts/26_present/261_waiver_map/2611_build_viz_data.py --arm claude_v1_5_adjud
    python 2_scripts/26_present/261_waiver_map/2611_build_viz_data.py --arm claude_v1_2_sonnet claude_v1_4_fedsusp
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

# --- explicit path globals, composed from the project root ---
DATA_DIR = pathlib.Path("1_data")
EXTRACT_DIR = DATA_DIR / "10_raw" / "102_fna" / "1022_extractions"
LEDGER_CSV = EXTRACT_DIR / "10220_extraction_results.csv"

# Spec-versioned arm directories: claude_v<major>_<minor>_<slug>. Sorting on the parsed
# (major, minor) is what makes "newest spec wins" self-maintaining — a v1_6 arm needs no
# edit here. Arms predating the versioning scheme are opt-in via --arm.
_ARM_VERSION_RE = re.compile(r"^claude_v(\d+)_(\d+)(?:_|$)")

US_ATLAS_JSON = DATA_DIR / "10_raw" / "103_geo" / "1031_us_atlas" / "counties-10m.json"

OUT_DIR = pathlib.Path("6_present") / "61_waiver_map"
OUT_JSON = OUT_DIR / "610_waiver_map_data.json"

FNA_HELPERS_DIR = "2_scripts/22_extract/222_fna_waivers"
sys.path.insert(0, FNA_HELPERS_DIR)
import fna_extraction_results as R  # noqa: E402  (path set above, per repo convention)

SCHEMA_VERSION = "wmap_v2"   # v2: multi-arm payload + per-unit render `kind`

# criterion_code -> UI label; family from the shared RULE_FAMILY crosswalk. Codes the
# data contains that are missing here fall back to the raw code string.
RULE_LABELS = {
    "pct10_statutory":    "10% unemployment (statutory)",
    "pct20_above_natl":   "20% above national rate",
    "lsa":                "Labor Surplus Area",
    "eb_trigger":         "Extended Benefits trigger",
    "federal_suspension": "Federal suspension",
    "noncontig_1p5x":     "Noncontiguous 1.5x rule",
    "other":              "Other criterion",
}

# area_type vocabularies. County-equivalents MUST resolve to a FIPS; city-likes resolve
# to parent-county FIPS via the LAUS-cities table; everything else is off-map (null).
COUNTY_TYPES = {"county", "balance of county", "parish", "borough", "census area",
                "city and borough", "planning region", "independent city"}
# 'city (partial)' is a sub-city carve-out (e.g. the Marshall County portion of
# Wheeling): it still maps to parent counties, and the partial-ness is carried in the
# unit's non-standard-geography note rather than in a separate render kind.
CITY_TYPES = {"city", "town", "village", "city (partial)"}

# 'borough' is the one area_type whose census meaning depends on the state: in Alaska a
# borough IS the county equivalent, but in New Jersey (also CT and PA) it is a
# municipality sitting inside a county. So outside Alaska a borough resolves through the
# cities table like any other place, and a borough below the LAUS 25k cutoff lands
# off-map exactly as a sub-25k city does — rather than failing the county-FIPS gate.
BOROUGH_AS_COUNTY_STATES = {"AK"}

# Census type suffix each county-equivalent area_type implies, used to retry a bare
# printed name against a reference that disambiguates with the suffix. 'balance of
# county' shares the county arm: the balance-of qualifier is a render kind, not a name.
_TYPE_SUFFIX = {"county": "county", "balance of county": "county", "parish": "parish",
                "borough": "borough", "census area": "census area",
                "city and borough": "city and borough",
                "planning region": "planning region", "independent city": "city"}

# Render kind — the SINGLE vocabulary the client switches on, so the area_type strings
# stay a data field rather than a second copy of this logic in JS:
#   county | boc | city | statewide | partial_statewide | offmap
# 'partial_statewide' is the D-01 shape (open decision): a grant covering the whole
# state EXCEPT named carve-outs, encoded as one aggregate unit with a null area_type
# and a statewide qualifying basis. It must NOT paint the state — the complement is
# named in a sibling group — so it is listed off-map with its verbatim text.
KIND_COUNTY, KIND_BOC, KIND_CITY = "county", "boc", "city"
KIND_STATEWIDE, KIND_PARTIAL, KIND_OFFMAP = "statewide", "partial_statewide", "offmap"

# Pure county RENAMES (geometry unchanged): a document's legacy FIPS paints at its
# current-vintage topology id, keeping the printed name. ONLY for renames — a real
# boundary change must NOT be added here; it still trips the topology gate below.
FIPS_RENAMES = {
    "12025": "12086",   # Dade -> Miami-Dade (1997)
    "46113": "46102",   # Shannon -> Oglala Lakota (2015)
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DOC_TYPE_LABEL = {
    "fns_response_only": "FNS response",
    "state_request_only": "State request",
    "full_application": "Full application",
    "other_nonstandard": "Nonstandard document",
}

_SUFFIX_RE = re.compile(r"fy\d{4}-([a-z])$")
_MONTH_SPAN_RE = re.compile(r"-(\d{1,2})\.(\d{4})-(\d{1,2})\.(\d{4})$")


def _fy_of_date(iso) -> int | None:
    """Federal FY containing an ISO date: named for the year it ENDS in, so Oct–Dec
    belong to the next year's FY."""
    m = re.match(r"^(\d{4})-(\d{2})", str(iso or ""))
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    return year + 1 if month >= 10 else year


def parse_stub(stem: str, request_level: dict, report: dict) -> tuple[str, int, str | None]:
    """'nd-abawd-response-fy2013' -> ('ND', 2013, None); month-span stubs like
    'nd-abawd-approval-10.2017-9.2018' map to the FY containing the end month.
    A stub carrying only a calendar year ('ga-abawd-approval-2018' — the CY2018
    approval class) has no FY token at all; fall back to the document's own dates,
    preferring the waiver's implementation date (which agrees with the fyNNNN naming
    convention on 52 of the 53 documents that carry both) over the response date
    (which can sit in the FY BEFORE the waiver's).
    Hard-fails when nothing resolves — a skipped document is a silent data hole."""
    state = R._state_from_name(stem)
    if state is None:
        sys.exit(f"[viz-data] cannot parse state from doc stub: {stem!r}")
    fy = R._fy_from_name(stem)
    suffix = None
    if fy is not None:
        sm = _SUFFIX_RE.search(stem)
        return state, fy, sm.group(1) if sm else None
    m = _MONTH_SPAN_RE.search(stem)
    if m:
        end_month, end_year = int(m.group(3)), int(m.group(4))
        return state, end_year if end_month <= 9 else end_year + 1, None
    for field in ("implementation_date_actual", "response_date", "date_national_office_action"):
        fy = _fy_of_date(request_level.get(field))
        if fy is not None:
            report["fy_from_dates"].append(f"{stem}: FY{fy} from {field}="
                                           f"{request_level.get(field)}")
            return state, fy, None
    sys.exit(f"[viz-data] cannot parse fiscal year from doc stub or dates: {stem!r}")


def _norm(s: str) -> str:
    return " ".join(str(s).replace(".", "").casefold().split())


_CITY_TYPE_WORDS = {"city", "town", "village", "borough", "cdp"}


def _city_keys(name: str) -> list[str]:
    """Lookup keys for a city name, most specific first. Both the reference table and
    the document's printed name go through this, so the two meet on whichever key
    matches.

      'Appleton city'        -> ['appleton city', 'appleton']
      'Michigan City'        -> ['michigan city', 'michigan']
      'Michigan City city'   -> ['michigan city city', 'michigan city', 'michigan']
      'Macon-Bibb County'    -> ['macon-bibb county', 'macon']

    Keeping the UNSTRIPPED key is what makes 'Michigan City' work: stripping the
    trailing type word off a city whose NAME ends in 'City' yields 'michigan', which
    matches nothing — the reference lists it as 'Michigan City city'. The hyphen head
    is for consolidated city-counties, which the reference names 'City-County'
    while documents print the bare city."""
    n = re.sub(r"\s*\([^)]*\)\s*$", "", str(name))
    parts = _norm(n).split()
    keys = [" ".join(parts)] if parts else []
    while len(parts) > 1 and parts[-1] in _CITY_TYPE_WORDS:
        parts = parts[:-1]
        keys.append(" ".join(parts))
    head = keys[-1].split("-")[0].strip() if keys else ""
    if head and head not in keys:
        keys.append(head)
    return keys


class StateGeo:
    """Per-state name->FIPS resolution built on the geography reference tables."""

    def __init__(self, state_code: str):
        self.state_code = str(state_code).upper()
        self.table = R.geo_reference_table(state_code)
        if not self.table:
            sys.exit(f"[viz-data] no geography reference for state {state_code!r}")
        self.by_key: dict[str, dict] = {}
        for row in self.table:
            for key in (_norm(row["name"]), _norm(row["official_name"])):
                self.by_key.setdefault(key, row)
        # Article-dropped aliases ('St. John Baptist' for 'St. John the Baptist').
        # Tracked separately so a hit still reports as a name repair.
        self._alias_keys: set[str] = set()
        for key, row in list(self.by_key.items()):
            toks = key.split()
            if "the" in toks:
                alias = " ".join(t for t in toks if t != "the")
                if alias not in self.by_key:
                    self.by_key[alias] = row
                    self._alias_keys.add(alias)
        # current vintage = validity window with no end year ('1997–', '~2022–')
        self.current_fips = {r["fips"] for r in self.table
                             if r["valid_fy"].rstrip().endswith("–")}
        self.state_fips = self.table[0]["fips"][:2]
        # State-specific split of the two vocabularies (see BOROUGH_AS_COUNTY_STATES).
        borough_is_county = self.state_code in BOROUGH_AS_COUNTY_STATES
        self.county_types = COUNTY_TYPES if borough_is_county else COUNTY_TYPES - {"borough"}
        self.city_types = CITY_TYPES if borough_is_county else CITY_TYPES | {"borough"}
        # city key -> parent county names. A reference row is indexed under every key
        # _city_keys yields, least specific LAST so a more specific row wins the slot.
        self.city_parents: dict[str, list[str]] = {}
        for city, parents in R.geo_city_parents(state_code).items():
            # Consolidated city-counties ('Augusta-Richmond County (consolidated) city')
            # carry '(not matched)' in the parent cell because no plain county shares
            # their name — but the county IS named in the row itself, after the hyphen.
            if not any(self.by_key.get(_norm(p)) for p in parents):
                m = re.match(r"^[^-]+-(.+?)(?:\s*\(|$)", re.sub(r"\s+city$", "", str(city)))
                if m and _norm(m.group(1)) in self.by_key:
                    parents = [m.group(1).strip()]
            for key in _city_keys(city):
                self.city_parents.setdefault(key, parents)

    def resolve_county(self, name: str, area_type: str | None = None
                       ) -> tuple[str | None, str | None]:
        """-> (fips, repaired_display_name|None). Exact first, then the census type
        suffix the unit's area_type implies, then unique <=2-edit, then a structural
        fallback: a consolidated-government name ('Anaconda-Deer Lodge') resolves when
        exactly one of its hyphen/slash segments names a county-equivalent.

        The suffix retry is what disambiguates a state where the reference must carry
        the type to keep two rows apart — Virginia's 'Franklin County' (51067) vs
        'Franklin city' (51620) — while the document prints the bare 'Franklin'. The
        area_type the extraction recorded picks the arm, so an independent city goes to
        'X city' ('Baltimore' -> 'Baltimore city', never the county) and a county goes
        to 'X County'; it is never guessed from the name alone. Hitting this path
        returns the reference's full name as a repair, so the choice is auditable in the
        run report and in the rendered unit label."""
        key = _norm(name)
        row = self.by_key.get(key)
        if row:
            return row["fips"], (row["name"] if key in self._alias_keys else None)
        suffix = _TYPE_SUFFIX.get(area_type or "")
        if suffix:
            row = self.by_key.get(f"{key} {suffix}")
            if row:
                return row["fips"], row["name"]
        fixed = R.resolve_geo_typo(key, self.by_key.keys())
        if fixed:
            row = self.by_key[fixed]
            return row["fips"], row["name"]
        if re.search(r"[-/]", key):
            hits = {r["fips"]: r for part in re.split(r"[-/]", key)
                    if (r := self.by_key.get(part.strip()))}
            if len(hits) == 1:
                row = next(iter(hits.values()))
                return row["fips"], row["name"]
        return None, None

    def resolve_city(self, name: str) -> list[str]:
        """-> parent-county FIPS list (possibly empty: pre-vintage or sub-25k city)."""
        parents: list[str] = []
        for key in _city_keys(name):
            if key in self.city_parents:
                parents = self.city_parents[key]
                break
        out = []
        for p in parents:
            fips, _ = self.resolve_county(p)
            if fips:
                out.append(fips)
        return out


def seed_flag(basis: str | None) -> bool | None:
    if basis in {"own_rate", "own_designation"}:
        return True
    if basis == "carried_by_group":
        return False
    return None  # unknown / statewide / null — never silently render as 'carried'


def doc_label(doc_type: str | None, dates: dict, suffix: str | None) -> str:
    label = DOC_TYPE_LABEL.get(doc_type, "Document")
    for k in ("response_date", "date_national_office_action", "date_state_request"):
        d = dates.get(k)
        if d and re.match(r"^\d{4}-\d{2}", str(d)):
            y, m = str(d)[:4], int(str(d)[5:7])
            if 1 <= m <= 12:
                label += f", {MONTHS[m - 1]} {y}"
                break
    if suffix:
        label += f" ({suffix})"
    return label


def natl_rate(group: dict):
    return R._natl_rate_scalar(group.get("national_unemployment_rate_cited"))


def build_group(g: dict, gid: int, geo: StateGeo, report: dict, ctx: str) -> dict:
    label = g.get("bundle_label")
    bundle_id = _norm(label) if label else f"g{gid}"
    lu = g.get("local_unemployment") or {}
    units = []
    for u in g.get("geographic_units") or []:
        area_type = _norm(u.get("area_type") or "")
        basis = u.get("qualifying_basis")
        name = u.get("name") or u.get("orig_text") or ""
        fips = repaired = None
        parent_fips: list[str] = []
        if area_type in geo.county_types:
            kind = KIND_BOC if (area_type == "balance of county"
                                or u.get("balance_of_county")) else KIND_COUNTY
            fips, repaired = geo.resolve_county(name, area_type)
            if fips is None:
                report["unresolved"].append(f"{ctx}: {name!r} ({area_type})")
            elif repaired:
                report["repairs"].append(f"{ctx}: {name!r} -> {repaired!r}")
            elif fips not in geo.current_fips:
                painted = FIPS_RENAMES.get(fips)
                report["legacy_fips"].append(
                    f"{ctx}: {name!r} -> {fips}"
                    + (f" (rename; painted as {painted})" if painted else ""))
                fips = painted or fips
        elif area_type in geo.city_types:
            kind = KIND_CITY
            parent_fips = geo.resolve_city(name)
            if not parent_fips:
                report["cities_unparented"].append(f"{ctx}: {name!r}")
        elif area_type == "statewide":
            kind = KIND_STATEWIDE
        elif not area_type and basis == "statewide":
            kind = KIND_PARTIAL
            report["partial_statewide"].append(f"{ctx}: {name!r}")
        else:
            # reservation areas and non-standard geographies (ZCTA, LMA, ...): real
            # waiver areas with no county geometry, listed in the side panel.
            kind = KIND_OFFMAP
            report["offmap"].append(f"{ctx}: {name!r} ({area_type or 'no area_type'})")
        report["area_types"][area_type] += 1
        units.append({
            "name": repaired or name,
            "orig_text": u.get("orig_text"),
            "area_type": area_type,
            "kind": kind,
            "fips": fips,
            "parent_fips": parent_fips or None,
            "balance_of_county": bool(u.get("balance_of_county")),
            "seed": seed_flag(basis),
            "qualifying_basis": basis,
            "own_rate": u.get("unemployment_rate"),
            # v1_4+: the agent's own flag that the printed area is not a standard
            # geography, plus its explanation — the only place a ZCTA/LMA/partial-city
            # unit says WHY it cannot be drawn.
            "non_standard_geography": bool(u.get("non_standard_geography")),
            "non_standard_note": u.get("non_standard_geography_note"),
            "unemployment": None,   # EXTENSION SLOT (LAUS level/rate for the window)
            "optimality": None,     # EXTENSION SLOT (per-unit measures)
        })
    return {
        "gid": gid,
        "bundle_id": bundle_id,
        "bundle_label": label,
        "criterion_code": g.get("criterion_code"),
        "criterion_other_explanation": g.get("criterion_other_explanation"),
        "criterion_verbatim": g.get("criterion_verbatim"),
        "criteria_summary": g.get("criteria_summary_text"),
        # v1_5: coverage the STATE declares instead of a waiver (7 CFR 273.24(g)
        # discretionary exemptions). Null in every document extracted so far; carried
        # so the client renders it the day a document uses it.
        "state_alternative_coverage": g.get("state_alternative_coverage"),
        "qualification_level": g.get("qualification_level"),
        "group_action": R.gold_action(g.get("group_action")),
        "group_action_reason": g.get("group_action_reason_citation"),
        "soft_criterion_invoked": g.get("soft_criterion_invoked"),
        "soft_criterion_verbatim": g.get("soft_criterion_verbatim"),
        "local_unemployment": {
            "rate": lu.get("rate_cited"),
            "window_type": lu.get("window_type"),
            "start": lu.get("start_date"),
            "end": lu.get("end_date"),
            "description": lu.get("description"),
        },
        "national_rate_cited": natl_rate(g),
        "waiver_effective": g.get("waiver_effective_date"),
        "waiver_expiry": g.get("waiver_expiry_date"),
        "applied_start": g.get("applied_waiver_start_date"),
        "applied_end": g.get("applied_waiver_end_date"),
        "units": units,
    }


def build_doc(path: pathlib.Path, obj: dict, arm: str, suffix: str | None,
              geo: StateGeo, report: dict) -> dict:
    rl = obj.get("request_level") or {}
    stub = path.stem
    groups = [build_group(g, i, geo, report, f"{stub}#g{i}")
              for i, g in enumerate(obj.get("groups") or [])]
    # repo-relative path of the interpreted source PDF (batch dirs mirror the
    # extraction arm's). The client's "source PDF" button uses it: a real link under
    # file://, a copyable `open` command on the hosted page (which can't reach disk).
    source_pdf = R.RESP_DOCS_DIR / path.parent.name / f"{stub}.pdf"
    return {
        "doc_stub": stub,
        "doc_label": doc_label(rl.get("document_type"), rl, suffix),
        "document_type": rl.get("document_type"),
        "arm": arm,
        "source_pdf": str(source_pdf),
        "request": {
            "date_state_request": rl.get("date_state_request"),
            "response_date": rl.get("response_date"),
            "date_national_office_action": rl.get("date_national_office_action"),
            "implementation_date": rl.get("implementation_date_actual"),
            "expiration_date": rl.get("expiration_date"),
            "action_reason": rl.get("action_reason_approval_denial"),
            "possible_double_counting": rl.get("possible_double_counting"),
            "double_counting_note": rl.get("double_counting_note"),
            # v1_5: free-text adjudication context — why a referenced area got no row,
            # what the document says about a partial-statewide grant, and so on.
            "notes": rl.get("notes"),
            "non_conforming_reason": rl.get("non_conforming_reason"),
        },
        "optimality": None,  # EXTENSION SLOT (doc-level sub/optimality measures)
        "groups": groups,
    }


# Fields written even when null, because the client distinguishes "absent" from
# "recorded as nothing" for them: `seed` is tri-state (own / carried / unknown) and a
# dropped false would read as unknown; the two extension slots are the documented
# contract that a future build step fills them in place.
_KEEP_NULL = {"seed", "unemployment", "optimality"}


def compact(obj, keep=_KEEP_NULL):
    """Drop null-valued keys before writing. Every consumer reads these fields with
    optional access (JS `undefined == null`), so an absent key and a null key mean the
    same thing to the client — but the key NAME costs bytes on 5,000 units, and the
    page inlines this payload whole. Cuts roughly a quarter off the file."""
    if isinstance(obj, dict):
        return {k: compact(v, keep) for k, v in obj.items()
                if v is not None or k in keep}
    if isinstance(obj, list):
        return [compact(v, keep) for v in obj]
    return obj


def discover_arms() -> list[str]:
    """Spec-versioned arm directories on disk, oldest spec FIRST (= lowest precedence).
    Unversioned exploratory arms (`claude`, `claude_run2`, `openai`) are excluded: they
    predate the v1_2 schema and would otherwise silently outrank nothing / everything
    depending on alphabetical luck. Name them with --arm to look at them."""
    found = []
    for d in sorted(p for p in EXTRACT_DIR.iterdir() if p.is_dir()):
        m = _ARM_VERSION_RE.match(d.name)
        if m and any(d.rglob("*.json")):
            found.append(((int(m.group(1)), int(m.group(2))), d.name))
    if not found:
        sys.exit(f"[viz-data] no spec-versioned arms (claude_v<major>_<minor>_*) under "
                 f"{EXTRACT_DIR} — name an arm explicitly with --arm")
    return [name for _, name in sorted(found)]


def ledger_crosscheck(docs_by_stub: dict[str, tuple[str, int]]) -> None:
    """Optional: the run ledger is untracked and may not exist (e.g. fresh worktree)."""
    if not LEDGER_CSV.exists():
        print("[viz-data] ledger not present — skipping FY cross-check")
        return
    import pandas as pd
    led = pd.read_csv(LEDGER_CSV).drop_duplicates(subset=["doc_stub"])
    n = 0
    for _, row in led.iterrows():
        got = docs_by_stub.get(str(row["doc_stub"]))
        if got is None:
            continue
        state, fy = got
        # The ledger's fiscal_year is parsed from the stub, so it is blank exactly
        # where the stub carries no FY token and this script fell back to the
        # document's dates — nothing to cross-check there, only the state.
        if pd.isna(row["fiscal_year"]):
            if str(row["state_code"]) != state:
                print(f"[viz-data] WARN ledger disagrees on {row['doc_stub']} state: "
                      f"ledger {row['state_code']} vs stub {state}")
                n += 1
            continue
        if str(row["state_code"]) != state or int(row["fiscal_year"]) != fy:
            print(f"[viz-data] WARN ledger disagrees on {row['doc_stub']}: "
                  f"ledger ({row['state_code']}, {row['fiscal_year']}) vs stub ({state}, {fy})")
            n += 1
    if n == 0:
        print("[viz-data] ledger cross-check: no disagreements")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", nargs="+", default=None,
                    help=f"extraction arm directories under {EXTRACT_DIR}, in ascending "
                         "precedence (a later arm supersedes an earlier one document by "
                         "document). Default: every claude_v<major>_<minor>_* arm on "
                         "disk, oldest spec first.")
    args = ap.parse_args()

    arms = args.arm if args.arm else discover_arms()
    for arm in arms:
        if not (EXTRACT_DIR / arm).is_dir():
            sys.exit(f"[viz-data] no such arm directory: {EXTRACT_DIR / arm}")

    # doc stub -> (arm, path). Iterating arms in precedence order and overwriting means
    # the LAST arm holding a document wins, and each document comes from exactly one
    # arm — the map never blends two specs for the same PDF.
    chosen: dict[str, tuple[str, pathlib.Path]] = {}
    superseded: Counter = Counter()
    for arm in arms:
        for path in sorted((EXTRACT_DIR / arm).rglob("*.json")):
            if path.stem in chosen:
                superseded[chosen[path.stem][0]] += 1
            chosen[path.stem] = (arm, path)
    if not chosen:
        sys.exit(f"[viz-data] no extraction JSONs under {[str(EXTRACT_DIR / a) for a in arms]}")

    report = {"unresolved": [], "repairs": [], "legacy_fips": [],
              "cities_unparented": [], "offmap": [], "partial_statewide": [],
              "fy_from_dates": [], "area_types": Counter()}
    geos: dict[str, StateGeo] = {}
    states: dict[str, dict] = {}
    docs_by_stub: dict[str, tuple[str, int]] = {}
    arm_doc_counts: Counter = Counter()

    for stub in sorted(chosen):
        arm, path = chosen[stub]
        obj = json.loads(path.read_text(encoding="utf-8"))
        state, fy, suffix = parse_stub(stub, obj.get("request_level") or {}, report)
        docs_by_stub[stub] = (state, fy)
        arm_doc_counts[arm] += 1
        geo = geos.setdefault(state, StateGeo(state))
        entry = states.setdefault(state, {
            "name": R.STATE_CODE_TO_NAME[state],
            "state_fips": geo.state_fips,
            "county_count_expected": len(geo.current_fips),
            "arms": [],
            "fys": {},
        })
        if arm not in entry["arms"]:
            entry["arms"].append(arm)
        entry["fys"].setdefault(str(fy), []).append(
            build_doc(path, obj, arm, suffix, geo, report))

    # deterministic ordering: states alphabetical, FYs ascending, docs by (suffix, date)
    for entry in states.values():
        for fy, docs in entry["fys"].items():
            docs.sort(key=lambda d: (d["doc_stub"], d["request"]["response_date"] or ""))
        entry["fys"] = {fy: entry["fys"][fy]
                        for fy in sorted(entry["fys"], key=int)}
    states = dict(sorted(states.items()))

    codes_seen = {g["criterion_code"]
                  for s in states.values() for docs in s["fys"].values()
                  for d in docs for g in d["groups"] if g["criterion_code"]}
    rule_labels = {c: {"short": RULE_LABELS.get(c, c), "family": R.RULE_FAMILY.get(c)}
                   for c in sorted(codes_seen)}

    n_docs = sum(len(d) for s in states.values() for d in s["fys"].values())
    payload = {
        "schema_version": SCHEMA_VERSION,
        "extraction_arms": [{"arm": a, "docs": arm_doc_counts.get(a, 0)} for a in arms
                            if arm_doc_counts.get(a, 0)],
        "extraction_spec": R.load_schema().get("title", ""),
        "corpus": {"states": len(states), "documents": n_docs},
        "rule_labels": rule_labels,
        "states": states,
    }

    # --- join report + hard gates ---
    print(f"[viz-data] arms={arms} -> {n_docs} docs from "
          f"{ {a: n for a, n in arm_doc_counts.items()} }"
          + (f", superseded {dict(superseded)}" if superseded else ""))
    print(f"[viz-data] {len(states)} states: "
          f"{ {s: sum(len(d) for d in e['fys'].values()) for s, e in states.items()} }")
    print(f"[viz-data] unit area_types: {dict(report['area_types'])}")
    for f in report["fy_from_dates"]:
        print(f"[viz-data] stub carries no fiscal year — {f}")
    for r in report["repairs"]:
        print(f"[viz-data] typo repair: {r}")
    for c in report["cities_unparented"]:
        print(f"[viz-data] city without parent mapping (off-map, listed in panel): {c}")
    for o in report["offmap"]:
        print(f"[viz-data] off-map unit (side panel only): {o}")
    for p in report["partial_statewide"]:
        print(f"[viz-data] partial-statewide aggregate unit (D-01, not painted): {p}")
    for lf in report["legacy_fips"]:
        print(f"[viz-data] NOTE unit resolved to a non-current-vintage FIPS: {lf}")
    if report["unresolved"]:
        for u in report["unresolved"]:
            print(f"[viz-data] UNRESOLVED county unit: {u}", file=sys.stderr)
        sys.exit(f"[viz-data] {len(report['unresolved'])} county-equivalent units "
                 "did not resolve to FIPS — refusing to write a payload with holes")

    # every resolved FIPS must exist in the inlined topology (vintage-drift tripwire)
    if US_ATLAS_JSON.exists():
        topo_ids = {g["id"] for g in
                    json.loads(US_ATLAS_JSON.read_text())["objects"]["counties"]["geometries"]}
        all_fips = {u["fips"] for s in states.values() for docs in s["fys"].values()
                    for d in docs for g in d["groups"] for u in g["units"] if u["fips"]}
        missing = sorted(all_fips - topo_ids)
        if missing:
            sys.exit(f"[viz-data] FIPS not present in topology (vintage drift?): {missing}")
        print(f"[viz-data] topology check: all {len(all_fips)} distinct FIPS present")
    else:
        print("[viz-data] WARN topology not downloaded (run `make viz_fetch`) — "
              "skipping FIPS-in-topology check")

    ledger_crosscheck(docs_by_stub)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(compact(payload), fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"[viz-data] wrote {OUT_JSON} ({OUT_JSON.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
