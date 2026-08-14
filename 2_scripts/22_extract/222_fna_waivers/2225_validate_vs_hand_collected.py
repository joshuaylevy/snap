#!/usr/bin/env python3
"""
2225 — Validate Claude extractions against the ND/WI hand-collected gold standard.

PILOT-STAGE validator for the agentic extractor. Flattens each extraction JSON
(nested request_level + groups[].geographic_units[]) into one row per
(document x group x geographic unit) — the same grain as the gold xlsx — then
reports agreement per fiscal year:
  * document-level: serial number, type_of_request, document_type, group/unit counts
  * unit-level: name-matched units, and among matches, criterion + action agreement

Unit names are matched on THREE bases, because the hand-collected sheets carry their
own transcription typos (WI "Milwakuee"/"Onconto"/"Richalnd"/"Waukeshaw", ND "Kkidder").
Under exact matching those units can never match a correctly-spelled extraction, which
would score the state geography reference DOWN for doing its job:
  exact          both sides as written. Comparable with pre-geo-context runs.
  gold_repaired  gold typos snapped to the reference vocabulary, extraction left as
                 written. The treatment channel: rewards an extraction that spells
                 canonically, still penalizes one that does not.
  canonical      both sides snapped. Spelling reconciled, so residual disagreement is
                 substantive (which units, what criterion/action).
Every repair is printed, and a near-miss is only ever snapped when it is within two
edits of EXACTLY ONE reference name (R.resolve_geo_typo -- the same rule 2220b gives
the extraction agents). Detail lines are reported on the canonical basis.

Extractions are flattened via the SHARED canonical flattener (R.flatten_to_gold),
so the extraction side already carries the gold column vocabulary (approval_criterion,
group_action normalized to approved/rejected). The KB->gold criterion crosswalk lives
in R.KB_TO_GOLD.

Run from project root, `snap` env:
  python 2_scripts/22_extract/222_fna_waivers/2225_validate_vs_hand_collected.py --state WI --fys 2003 2008 2020
  # validate a specific run's JSONs (default is the primary claude/ run):
  python 2_scripts/22_extract/222_fna_waivers/2225_validate_vs_hand_collected.py \
      --state WI --fys 2003 2020 \
      --json-root 1_data/10_raw/102_fna/1022_extractions/claude_run2
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path("2_scripts") / "22_extract" / "222_fna_waivers"))
import fna_extraction_results as R  # noqa: E402

GOLD_XLSX = R.gold_path   # 1_data/<CODE>-hand-collected.xlsx, resolved per state


# area-type words to drop from the tail of a unit name before matching
# (extraction may store "Adams County" / "Bad River Reservation"; gold stores "Adams").
_TYPE_TOKENS = {
    "county", "city", "reservation", "parish", "borough", "community",
    "area", "town", "village", "indian", "tribe", "band", "nation", "colony",
    "wi", "nc", "nd",   # trailing state code (whole-word state names -> _state_alias)
}
# connector words: truncate the name at the first one ("Beloit City in Rock" -> "Beloit City";
# "Chippewa less Eau Claire" -> "Chippewa")
_CONNECTORS = {"in", "less", "part", "portion", "excluding", "minus"}
# canonical aliases for whole-jurisdiction rows (gold: "United States"); the state's
# OWN name is state-dependent and handled by _state_alias below.
_ALIAS = {"statewide": "statewide", "unitedstates": "national", "national": "national"}


def _norm_name(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    toks = re.sub(r"[^a-z0-9]+", " ", str(x).lower()).split()
    # truncate at first connector word, then strip trailing type/state tokens
    out = []
    for t in toks:
        if t in _CONNECTORS:
            break
        out.append(t)
    while len(out) > 1 and out[-1] in _TYPE_TOKENS:
        out.pop()
    key = "".join(out)
    return _ALIAS.get(key, key)


def _ref_keys(state: str) -> set[str]:
    """The state geography reference's place names, normalized to match keys."""
    return {k for k in (_norm_name(n) for n in R.geo_reference_names(state)) if k}


def _state_alias(state: str, ref: set[str]) -> dict:
    """Whole-jurisdiction rows: gold writes the state's own name ("Wisconsin",
    "North Dakota") where the extraction writes "statewide". Map it -- UNLESS the
    state's name is also one of its own counties (Iowa County, Iowa; Washington
    County in many states), where the row is genuinely ambiguous and is left alone."""
    nm = _norm_name(R.STATE_CODE_TO_NAME.get(state.upper(), ""))
    return {nm: "statewide"} if nm and nm not in ref else {}


def _repair(keys: pd.Series, ref: set[str]) -> tuple[pd.Series, dict]:
    """Snap near-miss keys onto the reference vocabulary (2220b's rule). Returns the
    repaired series and the {before: after} map, so every repair stays auditable."""
    if not ref:
        return keys, {}
    fixes = {}
    for k in sorted(set(keys) - {""}):
        hit = R.resolve_geo_typo(k, ref)
        if hit:
            fixes[k] = hit
    return keys.map(lambda k: fixes.get(k, k)), fixes


# The gold sheets were hand-collected in two vintages with DIFFERENT criterion
# vocabularies: WI/ND use the FNS-form labels (percent_20, LSA, EUB, ARRA), the later
# DE/IA sheets use the rules-KB codes (pct_20_above_natl, federal_suspension). The
# extraction side arrives in the WI/ND vocabulary (R.KB_TO_GOLD). Comparing the raw
# strings scores a DE sheet 0% on criterion for a pure naming difference, so fold every
# synonym onto the KB code before comparing. Unrecognized labels pass through unchanged
# and will simply fail to match, which is the safe direction — a silent alias is worse
# than a visible disagreement.
_CRIT_CANON = {
    # 20% above national
    "percent_20": "pct20_above_natl", "pct_20_above_natl": "pct20_above_natl",
    "pct20_above_natl": "pct20_above_natl", "20_percent": "pct20_above_natl",
    # statutory 10%
    "percent_10": "pct10_statutory", "pct_10_statutory": "pct10_statutory",
    "pct10_statutory": "pct10_statutory", "10_percent": "pct10_statutory",
    # labor surplus area
    "lsa": "lsa",
    # extended-benefits trigger (gold writes EUB, the KB writes eb_trigger)
    "eub": "eb_trigger", "eb": "eb_trigger", "eb_trigger": "eb_trigger",
    # federal suspensions: ARRA (2009-10) and FFCRA (2020-23) are one code
    "arra": "federal_suspension", "ffcra": "federal_suspension",
    "federal_suspension": "federal_suspension",
    # OBBB noncontiguous-state provision
    "noncontig_1p5x": "noncontig_1p5x",
    "other": "other",
}


def _norm_crit(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip().lower()
    return _CRIT_CANON.get(s, s)


def _norm_alt(x) -> str:
    """state_alternative_coverage. Gold and the schema enum share one spelling
    ('discretionary_exemption_273_24_g'), so this only trims case and whitespace —
    a mismatch here is a real disagreement, not a formatting difference."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    return str(x).strip().lower()


def _norm_action(x) -> str:
    s = str(x).strip().lower() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    if s in {"denied", "rejected"}:
        return "not_approved"
    if s == "approved":
        return "approved"
    return s


def _resolve_multi_doc(g: pd.DataFrame, ext: pd.DataFrame, gkey: str, ekey: str):
    """Choose ONE extraction row per unit when a fiscal year holds SEVERAL documents.

    Gold carries one row per (FY, unit) and no document provenance, but a fiscal year
    can hold several distinct FNS actions: WI FY2005 is a February modification AND a
    June modification-and-extension on the same serial (2020071), and West Bend is coded
    percent_20 in the first and LSA in the second. Both extractions are faithful to their
    own document, so keying on (FY, unit) alone made the score depend on which document
    pandas happened to see first. Keep instead the candidate that agrees with gold — the
    question being "does the corpus contain gold's action", not "did an arbitrary pick
    land on it" — and return every contest so the choice is reported, never silent.
    """
    if "doc_stub" not in ext.columns:
        return ext.drop_duplicates(ekey).set_index(ekey), {}
    gi = g.drop_duplicates(gkey).set_index(gkey)
    keep, contested = [], {}
    for key, block in ext.groupby(ekey, sort=False):
        rows = list(block.index)
        if key in gi.index and block["doc_stub"].nunique() > 1:
            ga, gc = (_norm_action(gi.loc[key, "group_action"]),
                      _norm_crit(gi.loc[key, "approval_criterion"]))
            rows.sort(reverse=True, key=lambda i: (_norm_action(ext.loc[i, "group_action"]) == ga,
                                                   _norm_crit(ext.loc[i, "approval_criterion"]) == gc))
            contested[str(gi.loc[key, "geographic_unit_name"])] = sorted(block["doc_stub"].unique())
        keep.append(rows[0])
    return ext.loc[keep].set_index(ekey), contested


def compare_fy(state: str, fy: int, gold: pd.DataFrame, json_root: pathlib.Path) -> dict:
    wl = R.build_worklist(states=[state], fys=[fy])
    ext_rows = []
    for _, r in wl.iterrows():
        jp = json_root / r["batch"] / f"{r['doc_stub']}.json"
        if not jp.exists():
            continue
        try:
            obj = json.loads(jp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        f = pd.DataFrame(R.flatten_to_gold(obj, fiscal_year=fy))
        f["doc_stub"] = r["doc_stub"]
        ext_rows.append(f)
    ext = pd.concat(ext_rows, ignore_index=True) if ext_rows else pd.DataFrame()

    g = gold[gold["fiscal_year"] == fy].copy()
    out = {"state": state, "fy": fy, "gold_units": len(g), "ext_units": len(ext)}
    if ext.empty or g.empty:
        out["note"] = "no extraction JSON" if ext.empty else "no gold rows"
        return out

    g["_raw"] = g["geographic_unit_name"].map(_norm_name)
    ext["_raw"] = ext["geographic_unit_name"].map(_norm_name)

    # Three matching bases, because the gold sheets carry their own transcription
    # typos (WI 'Milwakuee'/'Richalnd'/'Waukeshaw', ND 'Kkidder'). Under exact
    # matching those units can NEVER match a correctly-spelled extraction, so the
    # geography reference -- whose whole point is canonical spelling -- would be
    # scored down for being right. Each basis answers a different question:
    #   exact          both sides raw. Comparable with pre-geo-context runs.
    #   gold_repaired  gold typos snapped to the reference, extraction left raw.
    #                  This is the TREATMENT channel: it rewards an extraction that
    #                  spells names canonically and still penalizes one that does not.
    #   canonical      both sides snapped. Spelling noise removed on both sides, so
    #                  what is left is substantive (which units, what criterion/action).
    ref = _ref_keys(state)
    alias = _state_alias(state, ref)
    if alias:
        g["_raw"] = g["_raw"].map(lambda k: alias.get(k, k))
        ext["_raw"] = ext["_raw"].map(lambda k: alias.get(k, k))
    g["_rep"], gold_fixes = _repair(g["_raw"], ref)
    ext["_rep"], ext_fixes = _repair(ext["_raw"], ref)
    out["ref_names"] = len(ref)
    out["gold_typo_fixes"] = gold_fixes
    out["ext_typo_fixes"] = ext_fixes

    bases = {
        "exact":         ("_raw", "_raw"),
        "gold_repaired": ("_rep", "_raw"),
        "canonical":     ("_rep", "_rep"),
    }
    out["bases"] = {n: _basis_stats(g, ext, gk, ek) for n, (gk, ek) in bases.items()}
    return out


def _basis_stats(g: pd.DataFrame, ext: pd.DataFrame, gkey: str, ekey: str) -> dict:
    """Name/action/criterion agreement for one choice of gold/extraction match key."""
    g_units = set(g[gkey]) - {""}
    e_units = set(ext[ekey]) - {""}
    matched = g_units & e_units
    res = {
        "name_matched": len(matched),
        "gold_n": len(g_units),
        "ext_n": len(e_units),
        "gold_only": sorted(g_units - e_units)[:15],
        "ext_only": sorted(e_units - g_units)[:15],
    }

    # among name-matched units: action agreement (all matched); criterion agreement
    # scored only where gold marks the unit APPROVED (gold leaves criterion blank on
    # denials, so a denied unit's ext 'other'/code is not a real disagreement).
    gi = g.drop_duplicates(gkey).set_index(gkey)
    ei, res["multi_doc_units"] = _resolve_multi_doc(g, ext, gkey, ekey)
    act_ok = 0
    crit_ok = crit_denom = 0
    alt_ok = alt_denom = 0
    alt_col = "state_alternative_coverage" in g.columns
    disagree = []
    for k in matched:
        gc = _norm_crit(gi.loc[k, "approval_criterion"])
        ec = _norm_crit(ei.loc[k, "approval_criterion"])
        ga = _norm_action(gi.loc[k, "group_action"])
        ea = _norm_action(ei.loc[k, "group_action"])
        a_match = (ga == ea)
        act_ok += a_match
        c_match = None
        if ga == "approved":
            crit_denom += 1
            c_match = (gc == ec)
            crit_ok += c_match
        # state_alternative_coverage (v1_5): scored only where the gold sheet carries the
        # column AND declares a route, so states whose sheets predate it are unaffected.
        alt_match = None
        if alt_col:
            g_alt, e_alt = _norm_alt(gi.loc[k, "state_alternative_coverage"]), _norm_alt(
                ei.loc[k, "state_alternative_coverage"] if "state_alternative_coverage" in ei else None)
            if g_alt:
                alt_denom += 1
                alt_match = (g_alt == e_alt)
                alt_ok += alt_match
        if not a_match or c_match is False or alt_match is False:
            disagree.append({
                "unit": gi.loc[k, "geographic_unit_name"],
                "gold_crit": gi.loc[k, "approval_criterion"], "ext_crit": ei.loc[k, "approval_criterion"],
                "gold_act": ga, "ext_act": ea,
            })
    res["act_agree"] = act_ok
    res["crit_agree"] = crit_ok
    res["crit_denom"] = crit_denom
    res["alt_agree"], res["alt_denom"] = alt_ok, alt_denom
    res["disagreements"] = disagree[:20]
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", default="WI")
    ap.add_argument("--fys", nargs="*", type=int, default=None,
                    help="fiscal years to score; default is every FY the gold sheet "
                         "carries (each state's sheet covers different years)")
    ap.add_argument("--json-root", default=str(R.CLAUDE_DIR),
                    help="dir holding <batch>/<stub>.json (default: the claude/ run)")
    args = ap.parse_args()

    json_root = pathlib.Path(args.json_root)
    gold_path = GOLD_XLSX(args.state)
    if not gold_path.exists():
        sys.exit(f"No gold sheet for {args.state.upper()} at {gold_path}. "
                 f"States with gold: {', '.join(R.gold_states()) or '(none)'}")
    gold = pd.read_excel(gold_path)

    # Provenance header. The gold sheets are hand-maintained and NOT under version
    # control (*.xlsx is gitignored), so a result is only interpretable against a
    # known sheet version -- print its content hash the way document_id / run_id /
    # geo_context_hash pin the rest of the pipeline.
    gold_sha = hashlib.sha256(gold_path.read_bytes()).hexdigest()
    print(f"gold  : {gold_path}  sha256={gold_sha[:8]}  rows={len(gold)}")
    print(f"ext   : {json_root}")
    blank_fy = int(gold["fiscal_year"].isna().sum())
    if blank_fy:
        print(f"  WARNING: {blank_fy} gold rows have a blank fiscal_year and are "
              f"invisible to every per-FY comparison below.")

    fys = args.fys or sorted(int(f) for f in gold["fiscal_year"].dropna().unique())
    # per-basis running totals, so the state's headline agreement rate is printed once
    # at the end rather than left for the reader to add up across 17 per-FY blocks
    totals = {b: dict(name=0, gold_n=0, act=0, act_n=0, crit=0, crit_n=0)
              for b in ("exact", "gold_repaired", "canonical")}
    for fy in fys:
        res = compare_fy(args.state.upper(), fy, gold, json_root)
        if "note" not in res:
            for label, t in totals.items():
                b = res["bases"][label]
                t["name"] += b["name_matched"]
                t["gold_n"] += b["gold_n"]
                t["act"] += b["act_agree"]
                t["act_n"] += b["name_matched"]
                t["crit"] += b["crit_agree"]
                t["crit_n"] += b["crit_denom"]
        print("=" * 70)
        print(f"{args.state.upper()} FY{fy}")
        if "note" in res:
            print(f"  {res['note']}  (gold_units={res['gold_units']}, ext_units={res['ext_units']})")
            continue
        print(f"  gold_units={res['gold_units']}  ext_units={res['ext_units']}  "
              f"(geo reference: {res['ref_names']} names)")
        for label in ("exact", "gold_repaired", "canonical"):
            b = res["bases"][label]
            m = b["name_matched"]
            line = f"  {label:<14} name {m}/{b['gold_n']}"
            if m:
                line += (f"   action {b['act_agree']}/{m}"
                         f"   criterion {b['crit_agree']}/{b['crit_denom']}")
                if b["alt_denom"]:
                    line += f"   alt_coverage {b['alt_agree']}/{b['alt_denom']}"
            print(line)
        for who, fx in (("gold", res["gold_typo_fixes"]), ("ext ", res["ext_typo_fixes"])):
            if fx:
                pairs = ", ".join(f"{a}->{b}" for a, b in sorted(fx.items()))
                print(f"  typo repairs ({who.strip()}): {pairs}")

        # detail is reported on the canonical basis: spelling is already reconciled
        # there, so anything left is a real disagreement about content.
        b = res["bases"]["canonical"]
        for unit, stubs in sorted(b["multi_doc_units"].items()):
            print(f"  multi-document unit {unit!r}: {stubs} -> scored against the "
                  f"document that agrees with gold")
        if b["gold_only"]:
            print(f"  in gold, not extracted (canon): {b['gold_only']}")
        if b["ext_only"]:
            print(f"  extracted, not in gold (canon): {b['ext_only']}")
        for d in b["disagreements"]:
            print(f"    DIFF {d['unit']!r}: crit gold={d['gold_crit']} ext={d['ext_crit']} | "
                  f"act gold={d['gold_act']} ext={d['ext_act']}")

    def _pct(n, d):
        return f"{n}/{d} ({100 * n / d:.1f}%)" if d else f"{n}/0 (n/a)"

    print("=" * 70)
    print(f"{args.state.upper()} TOTAL over {len(fys)} gold fiscal years")
    for label, t in totals.items():
        print(f"  {label:<14} name {_pct(t['name'], t['gold_n']):<18} "
              f"action {_pct(t['act'], t['act_n']):<18} "
              f"criterion {_pct(t['crit'], t['crit_n'])}")


if __name__ == "__main__":
    main()
