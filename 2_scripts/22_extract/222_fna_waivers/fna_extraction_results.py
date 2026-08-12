"""
Shared helpers for the FNA ABAWD waiver extraction (Phase 3, Claude in-harness extractor).

Owns: explicit path globals, the content-hash document_id, the response-PDF work list
(filterable by state/FY), JSON-schema validation of a model extraction, and the
(document_id x extractor x run_id) results ledger. Imported by 2222_extract_claude.py.

Run from project root with the `snap` conda env. All paths are declared explicitly
from the repo root down (no __file__ tricks), per project convention.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from datetime import datetime
from typing import Iterable, Optional

import pandas as pd

# --- explicit path spine (composed from repo root) --------------------------------
DATA_DIR = pathlib.Path("1_data")
RAW_DIR = DATA_DIR / "10_raw"
FNA_DIR = RAW_DIR / "102_fna"
RESP_DOCS_DIR = FNA_DIR / "1020_timelimit_waiver_docs"      # response/decision PDFs, per FY-batch
DOWNLOAD_MANIFEST = FNA_DIR / "1020_download_manifest.csv"

EXTRACT_DIR = FNA_DIR / "1022_extractions"
CLAUDE_DIR = EXTRACT_DIR / "claude"                          # in-harness extractions land here
LEDGER_CSV = EXTRACT_DIR / "10220_extraction_results.csv"    # provenance ledger

SCRIPTS_DIR = pathlib.Path("2_scripts") / "22_extract" / "222_fna_waivers"
SCHEMA_PATH = SCRIPTS_DIR / "2220c_schema.json"
INSTRUCTION_PATH = SCRIPTS_DIR / "2220a_extraction_instruction.txt"
PROMPT_PATH = SCRIPTS_DIR / "2220b_extraction_prompt.txt"

GOLD_WI = DATA_DIR / "WI-hand-collected.xlsx"
GOLD_ND = DATA_DIR / "ND-hand-collected.xlsx"

MODEL_TAG = "claude-opus-4-8[1m]"   # in-harness extractor model; part of the run_id

# --- state registry ----------------------------------------------------------------
# Corpus filename codes are lowercase USPS with three warts: 'gu' AND 'guam' both
# appear (same jurisdiction), 'nyc' is filed separately from 'ny' (kept distinct in
# the ledger; shares NY's geography context), and 'vi'/'dc' are non-state codes.
STATE_CODE_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia", "GU": "Guam", "VI": "U.S. Virgin Islands",
    "NYC": "New York City",
}
CODE_ALIASES = {"GUAM": "GU"}       # normalize the state_code itself
CONTEXT_ALIASES = {"NYC": "ny"}     # ledger code -> geo context file stub

GEO_CONTEXT_DIR = DATA_DIR / "11_clean" / "111_geo_context"


def geo_context_path(state_code) -> Optional[pathlib.Path]:
    """Per-state geography reference file for a ledger state_code, or None.
    NYC resolves to the NY file (its five boroughs are NY counties)."""
    if not state_code or not isinstance(state_code, str):
        return None
    code = CODE_ALIASES.get(state_code.upper(), state_code.upper())
    stub = CONTEXT_ALIASES.get(code, code.lower())
    p = GEO_CONTEXT_DIR / f"{stub}_geo_context.md"
    return p if p.exists() else None


# --- geographic name vocabulary (for validation, NOT for extraction) ----------------
# The per-state reference file is written for agents to READ; these helpers let the
# validator use the SAME vocabulary programmatically, so a name typo can be told apart
# from a substantive disagreement. Sections skipped: the prose preamble and the change
# log (neither is a name list).
_GEO_SKIP_SECTIONS = ("how to use", "changes to", "new york city")


def geo_reference_names(state_code) -> set[str]:
    """Every place name the state's geography reference lists: counties / county-
    equivalents, planning regions and legacy counties (CT), LAUS cities, New England
    cities and towns, and tribal areas. Display spelling, type words intact
    ('Apex town'); callers normalize."""
    p = geo_context_path(state_code)
    if p is None:
        return set()
    names: set[str] = set()
    section = ""
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if not section or section.startswith(_GEO_SKIP_SECTIONS):
            continue
        s = line.strip()
        if not s or s.startswith("Grouped by county") or s.startswith("Documents usually"):
            continue
        if s.startswith("|"):                       # markdown table -> first column
            cells = [c.strip() for c in s.strip("|").split("|")]
            head = cells[0] if cells else ""
            if not head or set(head) <= set("-: "):          # separator row
                continue
            if head.lower().startswith(("name", "city", "county", "region")):
                continue                                      # header row
            names.add(head)
        elif s.startswith("- ") and ":" in s:        # NE towns grouped by county
            names.update(t.strip() for t in s.split(":", 1)[1].split(","))
        elif "adjacency" in section and ":" in s:    # 'Alamance: Caswell, Chatham, ...'
            names.add(s.split(":", 1)[0].strip())
        elif "tribal" in section or "american indian" in section:
            names.update(t.strip() for t in s.split(","))
    return {n for n in names if n}


def _levenshtein(a: str, b: str) -> int:
    """Plain DP edit distance. Inputs here are short normalized place keys."""
    if a == b:
        return 0
    if not a or not b:
        return len(a) or len(b)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# a key must be at least this long before we will edit-distance it to a reference name;
# below it, 2 edits can turn one real short name into a different real short name.
GEO_MIN_FUZZY_LEN = 5
GEO_MAX_EDITS = 2


def resolve_geo_typo(key: str, ref_keys: Iterable[str]) -> Optional[str]:
    """Map a normalized place key onto a reference key when it is a near-miss for
    EXACTLY ONE of them -- the same rule 2220b gives the extraction agents ('within a
    character or two of exactly one name'). Returns None when the key is already exact,
    is too short to risk fuzzing, or is ambiguous (ties are never resolved)."""
    ref = set(ref_keys)
    if not key or key in ref or len(key) < GEO_MIN_FUZZY_LEN:
        return None
    best_d, best = GEO_MAX_EDITS + 1, []
    for r in ref:
        if abs(len(r) - len(key)) > GEO_MAX_EDITS:
            continue
        d = _levenshtein(key, r)
        if d < best_d:
            best_d, best = d, [r]
        elif d == best_d:
            best.append(r)
    if best_d <= GEO_MAX_EDITS and len(best) == 1:
        return best[0]
    return None


# --- identity & run bookkeeping ----------------------------------------------------
def document_id(pdf_path: pathlib.Path) -> str:
    """SHA256 of the PDF file CONTENT (not path). Dedupes identical files across FY pages."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_run_id(model_tag: str = MODEL_TAG) -> str:
    """Deterministic run identity = hash(instruction + prompt + schema + model_tag).

    Same prompt/schema/model -> same run_id -> resumable, idempotent ledger."""
    parts = [
        INSTRUCTION_PATH.read_text(encoding="utf-8"),
        PROMPT_PATH.read_text(encoding="utf-8"),
        SCHEMA_PATH.read_text(encoding="utf-8"),
        model_tag,
    ]
    return hashlib.sha256("\x1e".join(parts).encode("utf-8")).hexdigest()


def run_short(run_id: str) -> str:
    return run_id[:8]


# --- work list ---------------------------------------------------------------------
_FY_RE = re.compile(r"fy(\d{4})", re.IGNORECASE)


def _fy_from_name(name: str) -> Optional[int]:
    m = _FY_RE.search(name)
    return int(m.group(1)) if m else None


def _state_from_name(name: str) -> Optional[str]:
    """'wi-abawd-...' -> 'WI'; 'guam-abawd-...' -> 'GU'; 'nyc-abawd-...' -> 'NYC'."""
    m = re.match(r"([a-z]{2,4})-abawd", name, re.IGNORECASE)
    if not m:
        return None
    code = CODE_ALIASES.get(m.group(1).upper(), m.group(1).upper())
    return code if code in STATE_CODE_TO_NAME else None


def build_worklist(
    states: Optional[Iterable[str]] = None,
    fys: Optional[Iterable[int]] = None,
    json_root: Optional[pathlib.Path] = None,
) -> pd.DataFrame:
    """Response PDFs to extract, optionally filtered by state code and/or fiscal year.

    Returns columns: doc_stub, state_code, fiscal_year, batch, source_pdf_path,
    out_json_path, n_pages_note. One row per PDF. doc_stub is a stable slug used for
    the output JSON filename and as a human handle.

    json_root sets where out_json_path points; it defaults to CLAUDE_DIR. Pass a
    sibling directory (e.g. 1022_extractions/claude_v1_2_sonnet) to run a different
    spec — prompt revision, replicate, or a different model — without overwriting an
    existing run's JSONs. The run_id (spec hash) still distinguishes ledger rows."""
    states_up = {s.upper() for s in states} if states else None
    fys_set = {int(f) for f in fys} if fys else None
    root = pathlib.Path(json_root) if json_root is not None else CLAUDE_DIR

    rows = []
    for pdf in sorted(RESP_DOCS_DIR.rglob("*.pdf")) + sorted(RESP_DOCS_DIR.rglob("*.PDF")):
        name = pdf.name
        sc = _state_from_name(name)
        fy = _fy_from_name(name)
        if states_up is not None and (sc is None or sc not in states_up):
            continue
        if fys_set is not None and (fy is None or fy not in fys_set):
            continue
        batch = pdf.parent.name
        stub = pdf.stem.lower()  # e.g. wi-abawd-response-fy2003
        out_json = root / batch / f"{stub}.json"
        gcp = geo_context_path(sc)
        rows.append({
            "doc_stub": stub,
            "state_code": sc,
            "fiscal_year": fy,
            "batch": batch,
            "source_pdf_path": str(pdf),
            "out_json_path": str(out_json),
            "geo_context_path": str(gcp) if gcp else "",
        })
    df = pd.DataFrame(rows).drop_duplicates(subset=["source_pdf_path"]).reset_index(drop=True)
    return df


# --- schema validation -------------------------------------------------------------
def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_extraction(obj: dict) -> list[str]:
    """Return a list of schema-violation messages ([] == valid). Uses jsonschema if
    available; otherwise a minimal structural fallback."""
    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(load_schema())
        return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in validator.iter_errors(obj)]
    except ImportError:
        errs = []
        if not isinstance(obj, dict):
            return ["root: not an object"]
        rl = obj.get("request_level")
        if not isinstance(rl, dict):
            errs.append("request_level: missing/!object")
        elif rl.get("state") is None and rl.get("state_code") is None:
            errs.append("request_level: no state")
        if not isinstance(obj.get("groups"), list):
            errs.append("groups: missing/!list")
        return errs


# --- flatten to the hand-collected GOLD layout -------------------------------------
# Canonical flattener for the whole repo: nested extraction JSON -> one row per
# (document x group x geographic unit), in EXACTLY the 46-column order of the ND/WI
# hand-collected gold xlsx. The 2223 writer and the 2225 validator both call this so
# there is a single source of truth for the flat grain and column contract.
#
# GOLD_COLUMNS is the 46-col hand-collected contract and stays pristine (2225 aligns
# the extraction to the gold xlsx by these names). Columns with NO counterpart in the
# hand-collected sheet — model-extracted extras and derived/analysis columns (the v1_1
# flags; see EXTRA_COLUMNS) — are appended AFTER the gold block, so GOLD_COLUMNS remains
# an exact prefix of the emitted flat CSV (FLAT_COLUMNS).
GOLD_COLUMNS = [
    "fiscal_year", "document_type", "waiver_serial_number", "type_of_request",
    "primary_regulation_citation", "state", "fns_region",
    "action_reason_approval_denial", "reg_leg_action_basis", "conditions_and_reasons",
    "info_required_for_extension", "expiration_date", "limits_on_regional_office_approvals",
    "date_national_office_action", "date_state_request", "date_ro_transmittal_request",
    "date_ro_transmittal_response", "implementation_date_actual", "state_official_name",
    "fns_official_name", "fns_official_title", "response_date", "number_of_groups",
    "non_conforming_document", "non_conforming_reason", "group_id",
    "geographic_unit_name", "geographic_unit_area_type", "approval_criterion",
    "criterion_other_explanation", "criteria_summary_text",
    "national_unemployment_rate_cited", "local_unemployment_rate_cited",
    "data_collection_date", "group_action", "status", "waiver_effective_date",
    "waiver_expiry_date", "waiver_duration", "local_unemployment_window_criterion_cited",
    "local_unemployment_start_date", "local_unemployment_end_date",
    "local_unemployment_description", "state_name", "state_code", "notes",
]

# KB criterion_code -> gold approval_criterion vocabulary.
KB_TO_GOLD = {
    "pct20_above_natl": "percent_20",
    "lsa": "LSA",
    "eb_trigger": "EUB",
    "federal_suspension": "ARRA",
    "pct10_statutory": "percent_10",
    "noncontig_1p5x": "noncontig_1p5x",
    "other": "other",
}

# KB criterion_code -> coarse qualifying-rule FAMILY (derived analysis column, not a
# gold field). This is the self-certification cut: only the statutory 10% rule lets a
# state self-certify and issue a waiver at application time WITHOUT FNS approval; the
# insufficient-jobs family (20% rule, LSA, EB, softer evidence) requires an FNS action.
# federal_suspension (ARRA/FFCRA) and noncontig_1p5x (OBBB) are neither. A null / unknown
# criterion_code maps to None (indeterminate) so it reads as an empty cell downstream.
RULE_FAMILY = {
    "pct10_statutory": "ten_percent",
    "pct20_above_natl": "insufficient_jobs",
    "lsa": "insufficient_jobs",
    "eb_trigger": "insufficient_jobs",
    "other": "insufficient_jobs",
    "federal_suspension": "federal_suspension",
    "noncontig_1p5x": "noncontig",
}

# Non-gold columns appended after the 46 gold columns. These have no hand-collected
# counterpart but are CORE to post-extraction analysis (the flattener always runs before
# analysis, so they are treated as part of the panel, not an optional add-on): the
# verbatim printed unit string, the derived rule family, and the v1_1 analysis flags
# (geography classification, softer-criterion, data-nonconformance, double-counting).
# GOLD_COLUMNS stays an exact prefix of FLAT_COLUMNS; the 2223 writer emits FLAT_COLUMNS.
EXTRA_COLUMNS = [
    "geographic_unit_orig_text",            # unit: verbatim printed string (v1_1)
    "qualifying_rule_family",               # derived from criterion_code
    # v1_2 bundle semantics: the level at which qualification was EVALUATED. groups[] is
    # the evaluated SET — a per_unit group holds one area, a joint_aggregate group holds
    # the whole constructed set — which is the convention the hand-collected sheets
    # already use (see flatten_to_gold's docstring for the verification). These columns
    # make the distinction EXPLICIT, which gold leaves implicit in the group sizes: gold
    # tells you WI FY2003 is 79 singletons, but not that they are singletons because LSA
    # designations attach per county. qualifying_basis additionally records, per unit,
    # which members of a joint set were carried by it.
    "qualification_level",                  # group: per_unit|joint_aggregate|statewide|unknown
    "qualification_level_evidence",         # group: what decided the call
    "bundle_label",                         # group: document's own name for a joint set
    "geographic_unit_unemployment_rate",    # unit: this area's OWN printed rate
    "geographic_unit_qualifying_basis",     # unit: own_rate|own_designation|carried_by_group|...
    "geographic_unit_non_standard_geography",       # unit flag (v1_1)
    "geographic_unit_non_standard_geography_note",  # unit (v1_1)
    "geographic_unit_balance_of_county",            # unit flag (v1_1)
    "soft_criterion_invoked",               # group flag (v1_1)
    "soft_criterion_verbatim",              # group (v1_1)
    "data_non_bls_source",                  # group data_nonconformance.* (v1_1)
    "data_seasonally_adjusted",
    "data_nonstandard_averaging",
    "data_older_vintage",
    "data_nonconformance_note",
    "possible_double_counting",             # request flag (v1_1)
    "double_counting_note",                 # request (v1_1)
]
FLAT_COLUMNS = GOLD_COLUMNS + EXTRA_COLUMNS


def _serial_to_scalar(v):
    """Serial may be str, list[str], or null; the gold sheet holds a single scalar."""
    if v is None:
        return None
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return str(v)


def _natl_rate_scalar(obj):
    """national_unemployment_rate_cited is {value,text,vintage}; gold is a scalar."""
    if not isinstance(obj, dict):
        return None
    return obj.get("value") if obj.get("value") is not None else obj.get("text")


def gold_action(a):
    """Normalize an action to the gold vocabulary: approved | rejected."""
    if a is None:
        return None
    s = str(a).strip().lower()
    if s in {"denied", "rejected"}:
        return "rejected"
    if s == "approved":
        return "approved"
    return s


def flatten_to_gold(obj: dict, fiscal_year=None) -> list[dict]:
    """One extraction JSON -> list of gold-shaped row dicts (one per group x unit).

    approval_criterion is the KB->gold crosswalk of criterion_code; group_action and
    status are normalized to the gold vocabulary ('denied' -> 'rejected').

    number_of_groups and group_id carry the SCHEMA's semantics — group count, and a
    1-based group index — which is ALSO the hand-collected convention, verified against
    both sheets on 2026-08-10: gold group_id is a group index, not a per-unit counter
    (an earlier docstring here claimed otherwise and was wrong). Gold encodes both group
    shapes, matching the qualification_level distinction in 2220b: WI FY2003 has 79 units
    in 79 singleton groups (each LSA / 20%-rule / rejected county evaluated on its own),
    while ND FY2008 has 20 units in ONE group and WI FY2005 has 42 units in 19 groups
    sized 9/5/4/4/3/2 (genuine joint bundles). So a per_unit group holds one unit and a
    joint_aggregate group holds the whole constructed set, and the emitted group_id/
    number_of_groups line up with the gold columns directly.

    number_of_groups is DERIVED as len(groups) rather than taken from the model's
    self-reported request_level.number_of_groups, so it can never disagree with the
    group_id values in the same rows. 'notes' is gold-side human annotation with no
    schema source (left null); 'fiscal_year' is provenance passed in by the caller."""
    rl = obj.get("request_level") or {}
    doc = {
        "fiscal_year": fiscal_year,
        "document_type": rl.get("document_type"),
        "waiver_serial_number": _serial_to_scalar(rl.get("waiver_serial_number")),
        "type_of_request": rl.get("type_of_request"),
        "primary_regulation_citation": rl.get("primary_regulation_citation"),
        "state": rl.get("state"),
        "fns_region": rl.get("fns_region"),
        "action_reason_approval_denial": rl.get("action_reason_approval_denial"),
        "reg_leg_action_basis": rl.get("reg_leg_action_basis"),
        "conditions_and_reasons": rl.get("conditions_and_reasons"),
        "info_required_for_extension": rl.get("info_required_for_extension"),
        "expiration_date": rl.get("expiration_date"),
        "limits_on_regional_office_approvals": rl.get("limits_on_regional_office_approvals"),
        "date_national_office_action": rl.get("date_national_office_action"),
        "date_state_request": rl.get("date_state_request"),
        "date_ro_transmittal_request": rl.get("date_ro_transmittal_request"),
        "date_ro_transmittal_response": rl.get("date_ro_transmittal_response"),
        "implementation_date_actual": rl.get("implementation_date_actual"),
        "state_official_name": rl.get("state_official_name"),
        "fns_official_name": rl.get("fns_official_name"),
        "fns_official_title": rl.get("fns_official_title"),
        "response_date": rl.get("response_date"),
        # derived, not rl.get("number_of_groups"): must agree with the group_id column
        "number_of_groups": len(obj.get("groups") or []),
        "non_conforming_document": rl.get("non_conforming_document"),
        "non_conforming_reason": rl.get("non_conforming_reason"),
        "state_name": rl.get("state_name"),
        "state_code": rl.get("state_code"),
        "notes": None,
        # v1_1 request-level flags (constant across this doc's rows)
        "possible_double_counting": rl.get("possible_double_counting"),
        "double_counting_note": rl.get("double_counting_note"),
    }

    def _unit_row(gid, g, unit):
        lu = g.get("local_unemployment") or {}
        natl = g.get("national_unemployment_rate_cited") or {}
        dn = g.get("data_nonconformance") or {}
        u = unit or {}
        action = gold_action(g.get("group_action"))
        return {
            **doc,
            "group_id": gid,
            "geographic_unit_name": (unit or {}).get("name"),
            "geographic_unit_area_type": (unit or {}).get("area_type"),
            "geographic_unit_orig_text": (unit or {}).get("orig_text"),
            "approval_criterion": KB_TO_GOLD.get(g.get("criterion_code"), g.get("criterion_code")),
            "qualifying_rule_family": RULE_FAMILY.get(g.get("criterion_code")),
            # v1_2 bundle semantics (group-level, constant across this group's rows)
            "qualification_level": g.get("qualification_level"),
            "qualification_level_evidence": g.get("qualification_level_evidence"),
            "bundle_label": g.get("bundle_label"),
            "geographic_unit_unemployment_rate": u.get("unemployment_rate"),
            "geographic_unit_qualifying_basis": u.get("qualifying_basis"),
            "criterion_other_explanation": g.get("criterion_other_explanation"),
            "criteria_summary_text": g.get("criteria_summary_text"),
            "national_unemployment_rate_cited": _natl_rate_scalar(natl),
            "local_unemployment_rate_cited": lu.get("rate_cited"),
            "data_collection_date": (lu.get("vintage_or_date_of_data_cited")
                                     or (natl.get("vintage_or_date_of_data_cited")
                                         if isinstance(natl, dict) else None)),
            "group_action": action,
            "status": action,  # gold 'status' mirrors group_action
            "waiver_effective_date": g.get("waiver_effective_date"),
            "waiver_expiry_date": g.get("waiver_expiry_date"),
            "waiver_duration": g.get("waiver_duration_text"),
            "local_unemployment_window_criterion_cited": lu.get("window_type"),
            "local_unemployment_start_date": lu.get("start_date"),
            "local_unemployment_end_date": lu.get("end_date"),
            "local_unemployment_description": lu.get("description"),
            # v1_1 unit-level geography flags
            "geographic_unit_non_standard_geography": u.get("non_standard_geography"),
            "geographic_unit_non_standard_geography_note": u.get("non_standard_geography_note"),
            "geographic_unit_balance_of_county": u.get("balance_of_county"),
            # v1_1 group-level flags
            "soft_criterion_invoked": g.get("soft_criterion_invoked"),
            "soft_criterion_verbatim": g.get("soft_criterion_verbatim"),
            "data_non_bls_source": dn.get("non_bls_source"),
            "data_seasonally_adjusted": dn.get("seasonally_adjusted"),
            "data_nonstandard_averaging": dn.get("nonstandard_averaging"),
            "data_older_vintage": dn.get("older_vintage"),
            "data_nonconformance_note": dn.get("note"),
        }

    rows = []
    groups = obj.get("groups") or []
    if not groups:
        return [_unit_row(None, {}, None)]  # non-conforming / zero-group doc
    for gid, g in enumerate(groups, start=1):
        units = g.get("geographic_units") or []
        if not units:
            rows.append(_unit_row(gid, g, None))
        for u in units:
            rows.append(_unit_row(gid, g, u))
    return rows


def build_flat(
    states: Optional[Iterable[str]] = None,
    fys: Optional[Iterable[int]] = None,
    json_root: Optional[pathlib.Path] = None,
) -> pd.DataFrame:
    """Walk the worklist, load each JSON from json_root/<batch>/<stub>.json, flatten to
    the gold layout. json_root defaults to the primary claude/ run (CLAUDE_DIR)."""
    root = pathlib.Path(json_root) if json_root is not None else CLAUDE_DIR
    wl = build_worklist(states=states, fys=fys)
    rows, missing, bad = [], [], []
    for _, r in wl.iterrows():
        jp = root / r["batch"] / f"{r['doc_stub']}.json"
        if not jp.exists():
            missing.append(r["doc_stub"])
            continue
        try:
            obj = json.loads(jp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            bad.append(r["doc_stub"])
            continue
        rows.extend(flatten_to_gold(obj, fiscal_year=r["fiscal_year"]))
    if missing:
        print(f"  [skip] {len(missing)} docs without JSON under {root}: "
              f"{missing[:6]}{' ...' if len(missing) > 6 else ''}")
    if bad:
        print(f"  [skip] {len(bad)} docs with invalid JSON: {bad}")
    return pd.DataFrame(rows).reindex(columns=FLAT_COLUMNS)


# --- results ledger ----------------------------------------------------------------
LEDGER_COLUMNS = [
    "document_id", "extractor", "run_id", "run_short", "model_tag",
    "doc_stub", "state_code", "fiscal_year", "batch",
    "source_pdf_path", "response_json_path",
    "n_groups", "n_units", "schema_valid", "schema_errors",
    "extracted_at", "status", "geo_context_hash",
]


def upsert_ledger_row(row: dict) -> None:
    """One row per (document_id, extractor, run_id); replaces any existing match."""
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    full = {c: row.get(c) for c in LEDGER_COLUMNS}
    if LEDGER_CSV.exists():
        df = pd.read_csv(LEDGER_CSV, dtype=str)
        for c in LEDGER_COLUMNS:
            if c not in df.columns:
                df[c] = pd.NA
        mask = (
            (df["document_id"].astype(str) == str(full["document_id"]))
            & (df["extractor"].astype(str) == str(full["extractor"]))
            & (df["run_id"].astype(str) == str(full["run_id"]))
        )
        df = df[~mask]
        df = pd.concat([df, pd.DataFrame([full])], ignore_index=True)
    else:
        df = pd.DataFrame([full])
    df = df[LEDGER_COLUMNS]
    df.to_csv(LEDGER_CSV, index=False)


def collate_extraction(
    pdf_path: pathlib.Path,
    json_path: pathlib.Path,
    meta: dict,
    run_id: str,
    extractor: str = "claude_in_harness",
    model_tag: str = MODEL_TAG,
) -> dict:
    """Validate a written extraction JSON, count groups/units, upsert the ledger row.
    Returns the ledger row dict (also for CLI reporting)."""
    status = "ok"
    errs: list[str] = []
    n_groups = n_units = 0
    try:
        obj = json.loads(json_path.read_text(encoding="utf-8"))
        errs = validate_extraction(obj)
        groups = obj.get("groups") or []
        n_groups = len(groups)
        n_units = sum(len(g.get("geographic_units") or []) for g in groups)
        if errs:
            status = "schema_invalid"
    except FileNotFoundError:
        status = "missing_json"
    except json.JSONDecodeError as e:
        status = "bad_json"
        errs = [f"json: {e}"]

    row = {
        "document_id": document_id(pdf_path) if pdf_path.exists() else None,
        "extractor": extractor,
        "run_id": run_id,
        "run_short": run_short(run_id),
        "model_tag": model_tag,
        "doc_stub": meta.get("doc_stub"),
        "state_code": meta.get("state_code"),
        "fiscal_year": meta.get("fiscal_year"),
        "batch": meta.get("batch"),
        "source_pdf_path": str(pdf_path),
        "response_json_path": str(json_path),
        "n_groups": n_groups,
        "n_units": n_units,
        "schema_valid": (status == "ok"),
        "schema_errors": " | ".join(errs) if errs else None,
        "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        # sha256 of the state geography context file as of collate time (not proof
        # of what the agent read; honest-provenance approximation for v1)
        "geo_context_hash": _geo_context_hash(meta.get("state_code")),
    }
    upsert_ledger_row(row)
    return row


def _geo_context_hash(state_code) -> Optional[str]:
    p = geo_context_path(state_code)
    if p is None:
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()
