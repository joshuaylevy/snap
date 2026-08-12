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

GOLD_XLSX = {"WI": R.GOLD_WI, "ND": R.GOLD_ND}


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


def _norm_action(x) -> str:
    s = str(x).strip().lower() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    if s in {"denied", "rejected"}:
        return "not_approved"
    if s == "approved":
        return "approved"
    return s


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
    ei = ext.drop_duplicates(ekey).set_index(ekey)
    act_ok = 0
    crit_ok = crit_denom = 0
    disagree = []
    for k in matched:
        gc = str(gi.loc[k, "approval_criterion"]).lower()
        ec = str(ei.loc[k, "approval_criterion"]).lower()
        ga = _norm_action(gi.loc[k, "group_action"])
        ea = _norm_action(ei.loc[k, "group_action"])
        a_match = (ga == ea)
        act_ok += a_match
        c_match = None
        if ga == "approved":
            crit_denom += 1
            c_match = (gc == ec)
            crit_ok += c_match
        if not a_match or c_match is False:
            disagree.append({
                "unit": gi.loc[k, "geographic_unit_name"],
                "gold_crit": gi.loc[k, "approval_criterion"], "ext_crit": ei.loc[k, "approval_criterion"],
                "gold_act": ga, "ext_act": ea,
            })
    res["act_agree"] = act_ok
    res["crit_agree"] = crit_ok
    res["crit_denom"] = crit_denom
    res["disagreements"] = disagree[:20]
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", default="WI")
    ap.add_argument("--fys", nargs="*", type=int, required=True)
    ap.add_argument("--json-root", default=str(R.CLAUDE_DIR),
                    help="dir holding <batch>/<stub>.json (default: the claude/ run)")
    args = ap.parse_args()

    json_root = pathlib.Path(args.json_root)
    gold_path = GOLD_XLSX[args.state.upper()]
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

    for fy in args.fys:
        res = compare_fy(args.state.upper(), fy, gold, json_root)
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
            print(line)
        for who, fx in (("gold", res["gold_typo_fixes"]), ("ext ", res["ext_typo_fixes"])):
            if fx:
                pairs = ", ".join(f"{a}->{b}" for a, b in sorted(fx.items()))
                print(f"  typo repairs ({who.strip()}): {pairs}")

        # detail is reported on the canonical basis: spelling is already reconciled
        # there, so anything left is a real disagreement about content.
        b = res["bases"]["canonical"]
        if b["gold_only"]:
            print(f"  in gold, not extracted (canon): {b['gold_only']}")
        if b["ext_only"]:
            print(f"  extracted, not in gold (canon): {b['ext_only']}")
        for d in b["disagreements"]:
            print(f"    DIFF {d['unit']!r}: crit gold={d['gold_crit']} ext={d['ext_crit']} | "
                  f"act gold={d['gold_act']} ext={d['ext_act']}")


if __name__ == "__main__":
    main()
