---
name: progress-table
description: >
  Render the FNA/ABAWD extraction progress table — one row per state with tier, corpus
  size, geography warts, extraction run status, and gold-standard agreement. Use whenever
  Josh asks for "the progress table", "the tier table", "the tier0-4 table", "state
  status", "where does extraction stand", or any request to see which states have been
  extracted and how they scored.
---

# Extraction progress table

One markdown table, printed **inline in the reply** (not written to a file, not published
as an artifact unless asked). It answers two questions at once: where extraction stands,
and what is worth extracting next.

## How to produce it

Run from the project root, in the `snap` conda env:

```bash
python 2_scripts/22_extract/222_fna_waivers/2226_progress_table.py
```

Paste the script's stdout straight into the reply. Do **not** retype, reorder, or
re-derive the numbers by hand — the whole point of 2226 is that the table is recomputed
from the pipeline's own artifacts every time.

Flags:
- `--no-gold` — skip the per-state `2225` subprocess calls. Fast (seconds instead of a
  few minutes), but the three gold columns come back blank. Use only when Josh asks for
  a quick look or when the gold sheets are mid-edit.
- `--arm <path>` — score every gold state against one specific extraction root. Default
  is per-state: each state is scored against **the arm it was most recently extracted
  under**, so the score always describes the run the row reports.
- `--refresh-text-profile` — re-sweep the corpus with `pdftotext` before rendering.
  Needed only after new documents are downloaded; the cache is
  `1_data/10_raw/102_fna/1021_doc_text_profile.csv`.

## Column contract

| column | source | meaning |
|---|---|---|
| Code | registry | two-letter state/territory code (no state-name column — dropped by request) |
| Tier | registry (curated) | extraction priority, see vocabulary below |
| Doc years | download manifest | `FYmin–FYmax` of documents actually held |
| Docs | download manifest | all doc classes: response + modification + approval |
| Units | geography build report | current county-equivalents; **towns** for the six New England states, since towns are what actually get waived; parishes/boroughs/etc. named explicitly |
| Geo warts | registry template + live counts | <1 sentence on why the state sits in its tier |
| Run | extraction JSON tree | ✅ complete · 🔄 writing now (<30 min) · ⚠️ incomplete and quiet · ❌ never run |
| Last run | ledger, else mtime | date + arm label; `~` prefix means the date is a file mtime because that arm was never collated; `— n/N` shows a partial run |
| Gold: name / action / criterion | live `2225` call | `canonical` basis; `—` means the state has no hand-collected sheet |

**Tier vocabulary is `P, 0, 1, 2, 2.5, 3, X` — there is no Tier 4.** `P` = pilot state
with a gold sheet; `0` = near-free smoke test; `1` = small and standard county geography;
`2` = standard geography, larger corpus; `2.5` = names reservations as waiver areas but
only a small block; `3` = nonstandard geography (New England towns, LAUS-city-heavy,
tribal-area-heavy, independent cities); `X` = degenerate, 1–3 units, exercises no
grouping logic. If Josh says "tier0-4", he means this table.

Sort order is tier, then doc count ascending — cheapest-first within tier, which is the
order to actually work through.

## Editing it

`2226a_state_tier_registry.csv` is the **only** file to hand-edit. It is a versioned
source input (explicitly un-ignored in `.gitignore`, like the county-change log) holding
`state_code, state_name, tier, tier_order, unit_basis, unit_noun, geo_wart`.

- To **retier** a state: change `tier` and `tier_order` there. Nothing else.
- To **reword a wart**: edit `geo_wart`. Count-bearing claims must stay as placeholders —
  `{units} {laus} {towns} {resv} {legacy} {docs} {scanned} {fy_min} {fy_max}` — so the
  sentence tracks its source. Only genuinely qualitative claims (bundling behaviour,
  sub-county filing practice) are free prose, and those are judgments from reading the
  "Requested Area(s)" paragraphs.

Never edit derived numbers: they come from `1020_download_manifest.csv`,
`1110_build_report.csv`, `1021_doc_text_profile.csv`, the extraction JSON tree, the
ledger, and `2225`.

## Reading it honestly

- **A gold score belongs to an arm.** The arm label in "Last run" is not decoration —
  `98.5%` under `v1_4` and under `v1_5` are different claims. Say which when quoting.
- **Only four states have gold** (WI, ND, DE, IA). Every other row's `—` means unscored,
  not perfect. NC is the run-to-run stability state and still has no gold.
- **`⚠️` is not `✅`.** A partial run leaves `n/N` in the cell; do not describe such a
  state as extracted.
- **`~` dates are weaker evidence than plain dates** — an uncollated arm's mtime is
  exactly what lets a half-finished run look finished. If `~` appears, consider running
  `make fna_collate` for that arm.
