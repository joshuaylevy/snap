#!/usr/bin/env python3
"""
2225 — Validate Claude extractions against the ND/WI hand-collected gold standard.

PILOT-STAGE validator for the agentic extractor. Flattens each extraction JSON
(nested request_level + groups[].geographic_units[]) into one row per
(document x group x geographic unit) — the same grain as the gold xlsx — then
reports agreement per fiscal year:
  * document-level: serial number, type_of_request, document_type, group/unit counts
  * unit-level: name-matched units, and among matches, criterion + action agreement

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
    "wi", "nc", "nd",   # trailing state code (whole-word "Wisconsin" handled by _ALIAS)
}
# connector words: truncate the name at the first one ("Beloit City in Rock" -> "Beloit City";
# "Chippewa less Eau Claire" -> "Chippewa")
_CONNECTORS = {"in", "less", "part", "portion", "excluding", "minus"}
# canonical aliases for whole-jurisdiction rows (gold: "Wisconsin"/"United States")
_ALIAS = {"wisconsin": "statewide", "statewide": "statewide",
          "unitedstates": "national", "national": "national"}


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

    g["_k"] = g["geographic_unit_name"].map(_norm_name)
    ext["_k"] = ext["geographic_unit_name"].map(_norm_name)
    g_units = set(g["_k"]) - {""}
    e_units = set(ext["_k"]) - {""}
    matched = g_units & e_units
    out["name_matched"] = len(matched)
    out["gold_only"] = sorted(g_units - e_units)[:15]
    out["ext_only"] = sorted(e_units - g_units)[:15]

    # among name-matched units: action agreement (all matched); criterion agreement
    # scored only where gold marks the unit APPROVED (gold leaves criterion blank on
    # denials, so a denied unit's ext 'other'/code is not a real disagreement).
    gi = g.drop_duplicates("_k").set_index("_k")
    ei = ext.drop_duplicates("_k").set_index("_k")
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
    out["act_agree"] = act_ok
    out["crit_agree"] = crit_ok
    out["crit_denom"] = crit_denom
    out["disagreements"] = disagree[:20]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", default="WI")
    ap.add_argument("--fys", nargs="*", type=int, required=True)
    ap.add_argument("--json-root", default=str(R.CLAUDE_DIR),
                    help="dir holding <batch>/<stub>.json (default: the claude/ run)")
    args = ap.parse_args()

    json_root = pathlib.Path(args.json_root)
    gold = pd.read_excel(GOLD_XLSX[args.state.upper()])
    for fy in args.fys:
        res = compare_fy(args.state.upper(), fy, gold, json_root)
        print("=" * 70)
        print(f"{args.state.upper()} FY{fy}")
        if "note" in res:
            print(f"  {res['note']}  (gold_units={res['gold_units']}, ext_units={res['ext_units']})")
            continue
        m = res["name_matched"]
        print(f"  gold_units={res['gold_units']}  ext_units={res['ext_units']}  name_matched={m}")
        if m:
            cd = res["crit_denom"]
            print(f"  action agreement: {res['act_agree']}/{m}   "
                  f"criterion agreement (approved units): {res['crit_agree']}/{cd}")
        if res["gold_only"]:
            print(f"  in gold, not extracted (norm): {res['gold_only']}")
        if res["ext_only"]:
            print(f"  extracted, not in gold (norm): {res['ext_only']}")
        for d in res["disagreements"]:
            print(f"    DIFF {d['unit']!r}: crit gold={d['gold_crit']} ext={d['ext_crit']} | "
                  f"act gold={d['gold_act']} ext={d['ext_act']}")


if __name__ == "__main__":
    main()
