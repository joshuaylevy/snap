#!/usr/bin/env python3
"""
2222 — FNA ABAWD waiver extraction, Extractor B (Claude in-harness / agentic).

This is the driver for the "agentic interpretation" half of Phase 3. The actual
reading and interpretation is done by Claude agents inside the Claude Code harness
(they Read each response PDF — including scanned image-only forms that have no text
layer — and emit one JSON object per 2220c_schema.json to the out_json_path). This
script is the deterministic scaffolding around that: it builds the work list, prints
the per-document agent assignments, and — after the JSONs are written — validates
them against the schema and writes the (document_id x extractor x run_id) ledger.

Run from project root in the `snap` conda env.

Subcommands:
  worklist  --states WI NC [--fys 2003 2020 ...]   list docs + agent assignments
  collate   --states WI NC [--fys ...]             validate written JSONs -> ledger
  status    [--states ...] [--fys ...]             show current ledger rows

worklist/collate also take --json-root and --model-tag. A run is identified by its
spec hash (run_id = instruction + prompt + schema + model_tag), but the output PATH
is just claude/<batch>/<stub>.json, so a new spec would silently overwrite an older
run's JSONs. Point --json-root at a sibling directory to keep runs side by side, and
pass the same --json-root/--model-tag to collate.

Typical flow:
  1) python 2_scripts/.../2222_extract_claude.py worklist --states WI NC
  2) (Claude fans out one agent per PDF; each writes out_json_path)
  3) python 2_scripts/.../2222_extract_claude.py collate --states WI NC
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import pandas as pd

# import sibling helpers (script is always run from repo root; add its dir to path)
sys.path.insert(0, str(pathlib.Path("2_scripts") / "22_extract" / "222_fna_waivers"))
import fna_extraction_results as R  # noqa: E402


def _worklist(args) -> None:
    wl = R.build_worklist(states=args.states, fys=args.fys, json_root=args.json_root)
    if wl.empty:
        print("No matching response PDFs.", file=sys.stderr)
        return
    run_id = R.compute_run_id(model_tag=args.model_tag)
    pd.set_option("display.max_colwidth", 80)
    pd.set_option("display.width", 200)
    print(f"run_id={run_id}  ({R.run_short(run_id)})  model={args.model_tag}")
    print(f"{len(wl)} documents to extract "
          f"[states={args.states or 'ALL'} fys={args.fys or 'ALL'}]\n")
    print(wl[["doc_stub", "state_code", "fiscal_year", "batch"]].to_string(index=False))

    # ensure output dirs exist so agents can write straight to out_json_path
    for p in wl["out_json_path"]:
        pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)

    print("\n--- AGENT ASSIGNMENTS (one per document) ---")
    for _, r in wl.iterrows():
        done = pathlib.Path(r["out_json_path"]).exists()
        flag = "  [done]" if done else ""
        print(f"\n* {r['doc_stub']}{flag}")
        print(f"    READ : {r['source_pdf_path']}")
        if r.get("geo_context_path"):
            print(f"    READ : {r['geo_context_path']}    (state geography reference)")
        print(f"    WRITE: {r['out_json_path']}")


def _collate(args) -> None:
    wl = R.build_worklist(states=args.states, fys=args.fys, json_root=args.json_root)
    if wl.empty:
        print("No matching response PDFs.", file=sys.stderr)
        return
    run_id = R.compute_run_id(model_tag=args.model_tag)

    # Guard the crossed-roots mistake: these JSONs are already in the ledger under a
    # different spec, so collating them here would relabel another arm's output as
    # this spec's. Re-collating the SAME arm is unaffected (same run_id).
    clash = R.foreign_run_rows(wl["out_json_path"], run_id)
    if not clash.empty and not args.force:
        print(f"REFUSING: {len(clash)} of these JSONs are already recorded under a "
              f"different run_id.\nThis run_id is {R.run_short(run_id)} "
              f"(model={args.model_tag}); the files on disk were collated as:",
              file=sys.stderr)
        for rs, grp in clash.groupby("run_short"):
            print(f"  {rs}  model={grp['model_tag'].iloc[0]}  n={len(grp)}  "
                  f"e.g. {grp['response_json_path'].iloc[0]}", file=sys.stderr)
        print("\nPoint --json-root at THIS arm's own directory, or pass --force if you "
              "really mean to re-attribute them.", file=sys.stderr)
        sys.exit(1)

    rows = []
    for _, r in wl.iterrows():
        meta = {k: r[k] for k in ("doc_stub", "state_code", "fiscal_year", "batch")}
        row = R.collate_extraction(
            pdf_path=pathlib.Path(r["source_pdf_path"]),
            json_path=pathlib.Path(r["out_json_path"]),
            meta=meta,
            run_id=run_id,
            model_tag=args.model_tag,
        )
        rows.append(row)
    rep = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(f"run_id={run_id}  ({R.run_short(run_id)})  model={args.model_tag}")
    print(rep[["doc_stub", "status", "n_groups", "n_units", "schema_errors"]].to_string(index=False))
    ok = (rep["status"] == "ok").sum()
    print(f"\n{ok}/{len(rep)} valid  |  ledger -> {R.LEDGER_CSV}")
    bad = rep[rep["status"] != "ok"]
    if not bad.empty:
        print("\nNeeds attention:")
        for _, b in bad.iterrows():
            print(f"  - {b['doc_stub']}: {b['status']} :: {b['schema_errors']}")


def _status(args) -> None:
    if not R.LEDGER_CSV.exists():
        print("No ledger yet.", file=sys.stderr)
        return
    df = pd.read_csv(R.LEDGER_CSV, dtype=str)
    if args.states:
        df = df[df["state_code"].isin([s.upper() for s in args.states])]
    if args.fys:
        df = df[df["fiscal_year"].isin([str(int(f)) for f in args.fys])]
    pd.set_option("display.width", 200)
    print(df[["doc_stub", "state_code", "fiscal_year", "extractor",
              "n_groups", "n_units", "status", "run_short"]].to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("worklist", _worklist), ("collate", _collate), ("status", _status)):
        sp = sub.add_parser(name)
        sp.add_argument("--states", nargs="*", default=None, help="state codes, e.g. WI NC")
        sp.add_argument("--fys", nargs="*", type=int, default=None, help="fiscal years")
        if name != "status":
            sp.add_argument("--json-root", default=None, type=pathlib.Path,
                            help="write/read JSONs under this root instead of "
                                 f"{R.CLAUDE_DIR} (use for a prompt revision, a "
                                 "replicate, or a different model)")
            sp.add_argument("--model-tag", default=R.MODEL_TAG,
                            help=f"model tag recorded in the ledger and hashed into "
                                 f"the run_id (default {R.MODEL_TAG})")
        if name == "collate":
            sp.add_argument("--force", action="store_true",
                            help="collate even when these JSONs are already recorded "
                                 "under a different run_id (re-attributes them)")
        sp.set_defaults(func=fn)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
