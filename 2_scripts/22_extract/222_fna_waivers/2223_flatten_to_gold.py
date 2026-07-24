#!/usr/bin/env python3
"""
2223 — Write Claude extraction JSONs out in the hand-collected GOLD column layout.

Thin CLI over the canonical flattener in fna_extraction_results (R.flatten_to_gold /
R.build_flat). Emits one row per (document x group x geographic unit) with the 46 gold
columns (R.GOLD_COLUMNS) followed by the appended non-gold columns (R.EXTRA_COLUMNS:
verbatim unit text, derived qualifying_rule_family, and the v1_1 analysis flags for
geography / softer-criterion / data-nonconformance / double-counting) -> R.FLAT_COLUMNS,
in order, to a "*_extractions_flat.csv". This is the single supported way to produce the
flat CSVs; earlier flat files came from ad-hoc, uncommitted flatteners with divergent
column sets.

See R.flatten_to_gold for the mapping contract and its known, intentional gaps vs. the
gold sheet (group_id / number_of_groups semantics, data_collection_date precision, notes).

Run from project root, `snap` env. Examples:
  # WI run 2 (JSONs under claude_run2/) -> wi_extractions_run2_flat.csv
  python 2_scripts/22_extract/222_fna_waivers/2223_flatten_to_gold.py \
      --states WI \
      --json-root 1_data/10_raw/102_fna/1022_extractions/claude_run2 \
      --tag run2

  # NC from the primary run (claude/) -> nc_extractions_flat.csv
  python 2_scripts/22_extract/222_fna_waivers/2223_flatten_to_gold.py --states NC
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("2_scripts") / "22_extract" / "222_fna_waivers"))
import fna_extraction_results as R  # noqa: E402


def _default_out(states, tag) -> pathlib.Path:
    stem = "_".join(s.lower() for s in states) if states else "all"
    suffix = f"_{tag}" if tag else ""
    return R.EXTRACT_DIR / f"{stem}_extractions{suffix}_flat.csv"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--states", nargs="*", default=None, help="state codes, e.g. WI NC")
    ap.add_argument("--fys", nargs="*", type=int, default=None, help="fiscal years")
    ap.add_argument("--json-root", default=str(R.CLAUDE_DIR),
                    help="dir holding <batch>/<stub>.json (default: the claude/ run)")
    ap.add_argument("--tag", default=None,
                    help="filename suffix, e.g. 'run2' -> wi_extractions_run2_flat.csv")
    ap.add_argument("--out", default=None, help="explicit output CSV path (overrides --tag)")
    args = ap.parse_args()

    out_path = pathlib.Path(args.out) if args.out else _default_out(args.states, args.tag)
    df = R.build_flat(states=args.states, fys=args.fys, json_root=pathlib.Path(args.json_root))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"wrote {len(df)} rows x {df.shape[1]} cols  ->  {out_path}")
    print(f"columns match flat layout (gold + derived): {list(df.columns) == R.FLAT_COLUMNS}")


if __name__ == "__main__":
    main()
