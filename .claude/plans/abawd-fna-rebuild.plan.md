# ABAWD Waiver Pipeline v2 — From-Scratch Rebuild on the FNA Application Archive

## Context

The research project ("Inferring State Technical Capacity and Preferences from ABAWD Waiver Allocations," Duggan & Levy) needs a county-level panel of ABAWD waiver **applications and FNS decisions**: for every geographic unit a state applied for (alone or in a contiguous group), whether FNS approved/denied it, under which qualifying rule the state applied, and the data cited. This panel is the observed-choice side of the paper's weighted-set-packing optimality analysis.

The existing pipeline (R scraper → OpenAI Responses extraction → interpretations CSV) was built against the old fns.usda.gov waivers page, which held mostly **FNS response letters only**. FNS (now **FNA**) has released a fuller archive containing **applications and responses** at `https://www.fna.usda.gov/snap/waivers/timelimit/1997-1999` (per-FY-batch pages, last batch "Time Limit Waivers FY 2025–2029"). We rebuild from scratch against this archive.

Two hand-collected gold-standard panels exist: `1_data/ND-hand-collected.xlsx` (146 rows) and `1_data/WI-hand-collected.xlsx` (314 rows), one row per (document × group × geographic unit), ~46 columns. Their schema is the **floor** for the output panel; they are "generally correct" but suspected errors should be raised with Josh.

## Locked decisions (from Josh)

- **New branch, restructure in place** — replace current `1_data`/`2_scripts` contents; no nested v2 tree; no new repo.
- **Zip-archive the old corpus** and re-download everything fresh from the FNA archive.
- **Rules first, semantically**: v1 delivers a verified rules knowledge base with citations + effective dates; programmatic rule-checker is stubbed (schema hooks only). Unemployment/population data ingestion (LAUS vintages etc.) is **out of scope entirely**.
- **Deterministic download scripts**; scrape a .gov site slowly and respectfully.
- **Hybrid extraction**: OpenAI API (cost-capped, code likely needs endpoint/model refresh) + Claude in-harness agentic passes, with **adversarial cross-checking** between independent extractors. Claude session spend OK; OpenAI spend gated.
- **Validation is interactive** against ND/WI; propose schema additions; flag suspected hand-collection errors.
- Rules sources: links/refs in `5_write/weighted_set_packingv2.pdf`, deep research, and the rules disclosure recovered from the Cursor chat history (already extracted — see Phase 1 inputs). Verify summary with Josh **before** encoding into prompts.
- Python via the `snap` conda env, always run from project root, explicit path globals (no `__file__` tricks).

## Reusable assets

- `2_scripts/22_extract/221_abawd_waivers/2210b_extraction_prompt.txt` + `2210c_fns_field_mapping.md` — seed for the new extraction schema (already aligned to FNS Waiver Response form field names).
- `abawd_extraction_results.py` — run_id/provenance/upsert patterns to port (not copy verbatim).
- Recovered Cursor-chat rules disclosure + paper §§1.1–1.4 — seed for the rules KB.
- `1_data/10_raw/101_dol/10110_eta539_state_eb_triggerlist_panel.csv` — keep in place (EB trigger context for the rules doc).
- Makefile structure and numbering conventions.

## Target architecture (new branch `fna_rebuild`)

```
0_lit/00_abawd_rules/                     # rules KB: guidance PDFs + statutes
    000_sources/                          #   downloaded primary sources
    001_abawd_waiver_rules.md             #   THE semantic rules document (cited, effective-dated)
    002_rules_machine.yaml                #   machine-readable rule codes/windows/thresholds (checker stub interface)
1_data/10_raw/
    100_usda/  → zipped to 1_data/10_raw/100_usda_legacy_fns_scrape_archived_<date>.zip (gitignored), then deleted
    101_dol/                              # unchanged
    102_fna/
        1020_timelimit_waiver_docs/FY97_99/ ... FY25_29/   # fresh scrape, organized by FY batch page
        1020_download_manifest.csv        # url, page, link text, http status, sha256, timestamp
        1021_document_inventory.csv       # document_id (sha256 of file CONTENT), state, fy, doc class guess, path, source url
        1022_extractions/
            openai/FYxx/*.json            # raw API responses, run_short in filename
            claude/FYxx/*.json            # in-harness extractions, same schema
            10220_extraction_results.csv  # (document_id × extractor × run_id) provenance ledger
            10221_adjudications.csv       # field-level agreement/referee verdicts
            10222_human_review_queue.csv
    11_clean/
        110_waiver_panel/
            1100_waiver_unit_panel.csv    # document × group × geographic unit (superset of xlsx schema)
            1101_state_year_application_panel.csv
2_scripts/
    21_scrape_dl/212_fna_timelimit/
        2120_recon_fna_site.py            # one-time polite recon; writes page/link map
        2121_download_fna_waiver_docs.py  # deterministic, resumable, rate-limited
        2122_make_document_inventory.py   # content-hash IDs (kills the old R↔Python path-hash contract)
    22_extract/222_fna_waivers/
        2220a_extraction_instruction.txt
        2220b_extraction_prompt.txt       # rebuilt from 2210b + rules KB + application-side fields
        2220c_schema.json                 # canonical JSON schema (single source of truth for both extractors)
        2221_extract_openai.py            # refreshed API code (verify current endpoints/models; Batch API)
        2222_extract_claude_protocol.md   # protocol doc driving in-harness agentic extraction
        2223_adjudicate_extractions.py    # field-level compare → agree/referee/human-review
        2224_build_waiver_panel.py        # adjudicated JSONs → 1100/1101 panels
        2225_validate_vs_hand_collected.py# agreement report vs ND/WI xlsx
    (legacy 211_*/221_* scripts deleted on this branch; recoverable via git)
```

## Phases

### Phase 0 — Branch + archive (small, mechanical)
1. Commit the pending WIP on `new_extraction_prompt` (renames `2110_`/`2111_`, `2211` fix) so nothing is lost; branch `fna_rebuild` from it.
2. Version this plan: commit `.claude/plans/abawd-fna-rebuild.plan.md` on `fna_rebuild` (mirroring how `.cursor/plans/` is tracked) so the plan travels with the repo across sessions/machines.
3. Zip `1_data/10_raw/100_usda/` → `100_usda_legacy_fns_scrape_archived_<date>.zip` (add to `.gitignore`), remove originals, delete legacy scripts on the branch.
4. Scaffold the new tree + Makefile targets.

### Phase 1 — Rules knowledge base (checkpoint with Josh)
1. **Deep-research** (deep-research skill) the rule history, anchored on the paper's references: PRWORA §824 / FSA §6(o); 7 CFR 273.24; FNS guidance Dec 1996, Aug 2006, Dec 2016, Sept 2021; LSA designation rules (20 CFR 654, incl. 6% floor / 10% ceiling); EB trigger mechanics (ETA-539 IUR/TUR); ARRA suspension (Apr 2009–Sep 2010); FFCRA suspension (Apr 2020–Jun 2023); OBBB 2025 (ends Insufficient-Jobs criterion + grouping); the FNS→FNA rename; statewide-waiver-via-EB automatic qualification; window-selection rules (24-month window starting no earlier than January two FYs before waiver-start FY).
2. Reconcile terminology conflicts — e.g., the Cursor-chat disclosure calls LSA "the 10% rule," while the paper reserves [10% Rule] for the statutory >10% unemployment criterion. The KB defines one canonical code set (proposed: `pct10_statutory`, `pct20_above_natl`, `lsa`, `eb_trigger`, `federal_suspension`, `statewide_eb`, `other`) with per-code effective windows.
3. Download primary-source PDFs into `0_lit/00_abawd_rules/000_sources/`.
4. Write `001_abawd_waiver_rules.md` (narrative, cited, effective-date table, operationalization details: data sources, aggregation/rounding, window legality, contiguity, no-double-counting) and `002_rules_machine.yaml` (stub interface for the future programmatic checker — codes, dates, thresholds; no checking code).
5. **CHECKPOINT: present the rules summary to Josh for verification. Do not proceed to prompt-building until confirmed.**

### Phase 2 — FNA scraper + inventory (checkpoint: volume report)
1. **Recon**: `2120` fetches the seed page, discovers all FY-batch pages (through "FY 2025–2029"), maps document links, link text, and grouping (state? application vs response?). NOTE: the seed URL timed out from this machine twice on 2026-07-21 — first execution step is confirming reachability (Josh should verify the link loads in a browser; may need different network).
2. **Download** (`2121`): deterministic, resumable via manifest; ≥1–2 s between requests, retry with backoff, honest User-Agent, respect robots.txt; per-FY-batch folders; record everything in `1020_download_manifest.csv`.
3. **Inventory** (`2122`): `document_id = sha256(file content)`; parse state/FY/doc-class from link text + URL patterns; dedupe identical files appearing on multiple pages.
4. **CHECKPOINT: report corpus size/composition (n docs, applications vs responses, per-state coverage, gaps vs the old 1,112-PDF corpus) before any extraction spend.**

### Phase 3 — Hybrid adversarial extraction (checkpoint: pilot + cost gate)
1. **Schema** (`2220c_schema.json`): superset of the ND/WI xlsx columns. Keep `request_level` / `groups` / `geographic_units` structure from `2210b`. Proposed additions (to be approved during validation): FIPS codes for geographic units; `source_url` + `document_id` provenance; explicit applied-vs-granted window fields; cited data vintage/access date; rule code aligned to the KB's canonical codes; extractor-agreement flags.
2. **Prompt** (`2220b`): rebuilt from `2210b`, now grounded in the verified rules KB (the extractor knows what rules exist in which years — better classification, and it can flag internally inconsistent documents).
3. **Extractor A — OpenAI** (`2221`): refresh the API code (verify against current OpenAI docs — model lineup, Responses/Batch endpoints, structured outputs; existing code may reference dead endpoints). Batch API + smallest adequate model + cached static prefix. Keep run_id = hash(instruction+prompt+schema+model), run_short in filenames, resumable results ledger, `--fys` subsetting.
4. **Extractor B — Claude in-harness** (`2222` protocol): agent fan-out reads PDFs directly and emits the same JSON schema into `1022_extractions/claude/`; same ledger. This satisfies the "multiple bots, adversarial checking" requirement without OpenAI double-spend.
5. **Adjudication** (`2223`): normalize both extractions; field-level compare. Agree → accept. Disagree → referee (Claude agent given the PDF, both candidates, and the rules KB) picks/overrides with justification. Unresolved or non-conforming → `10222_human_review_queue.csv`.
6. **Cost controls**: dry-run token/cost estimator printed **before** any OpenAI submission; per-FY-batch submission gates (explicit go-ahead); Claude passes and refereeing run in-harness.
7. **CHECKPOINT: pilot on FY97–99 batch + the ND/WI-covered years; review agreement rates and cost projection before scaling.**

### Phase 4 — Panel construction
- `2224`: adjudicated JSONs + inventory → `1100_waiver_unit_panel.csv` (document × group × unit; all xlsx columns + provenance + agreement metadata) and `1101_state_year_application_panel.csv` (one row per application: state, FY, serial, dates, n groups, n units, outcome mix). Applications and responses matched on (state, serial number, FY) with fuzzy fallback → both document_ids on each panel row.

### Phase 5 — Interactive validation vs ND/WI
- `2225` aligns machine panel to each xlsx on (state, fy, waiver_serial_number, group, unit); reports field-by-field agreement; produces disagreement tables for joint review with Josh. Iterate prompt/adjudication until acceptable; raise any suspected hand-collection errors explicitly (they are presumed generally correct). Schema additions proposed here get folded back into Phase 3 schema and re-run cheaply via run_id versioning.

## Verification (end-to-end)

1. `make fna_recon` → page map matches what Josh sees in a browser.
2. Pilot download of one FY batch; manifest rows == links on page; sha256s stable on re-run (idempotent).
3. Pilot extraction (both extractors) on ~20 docs including ND FY2013 and WI FY2019/2023 documents; adjudication produces a panel slice.
4. `2225` agreement report vs the corresponding ND/WI xlsx rows — target: exact match on serials/dates/geography lists, near-match on long text fields; every disagreement classified (extractor error / hand-collection issue / genuine ambiguity).
5. Full run gated per FY batch with cost printout; final panels rebuilt via `make` from a clean checkout + the zip-archived corpus absent (proves the pipeline is self-contained).

## Open items (resolve during execution)

- FNA site reachability (timed out from this machine — Josh to confirm link works).
- Whether FNA pages distinguish applications from responses in link text (recon determines inventory heuristics).
- OpenAI model choice + current pricing (verify at execution; Josh gates spend).
- FIPS-crosswalk enhancement approval (CT planning regions, AK boroughs, LA parishes, independent cities).
- Exact canonical rule-code set (settled at the Phase 1 checkpoint).
