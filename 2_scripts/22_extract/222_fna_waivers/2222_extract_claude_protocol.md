# Extractor B — Claude in-harness (agentic) extraction protocol

This is the "agentic interpretation" half of Phase 3. Unlike the OpenAI Batch
extractor (Extractor A, script `2221`, spend-gated), this extractor runs **inside
the Claude Code harness**: a fan-out of Claude subagents each *reads* one FNA
response PDF and emits a JSON object conforming to `2220c_schema.json`. Because the
Read tool renders PDF pages as images, this path handles the **scanned, image-only
older documents** (e.g. WI FY2002/2003/2011/2013-a, NC FY2013) that have no text
layer and would defeat a `pdftotext`/text-only API extractor.

## Files (single source of truth)
- `2220a_extraction_instruction.txt` — system role for the extractor.
- `2220b_extraction_prompt.txt` — the extraction task spec (structure, criterion
  codes, splitting rule, dates/QC). Grounded in the rules KB
  (`0_lit/00_abawd_rules/002_rules_machine.yaml`).
- `2220c_schema.json` — the canonical JSON schema. Both extractors emit this.
- `fna_extraction_results.py` — path globals, content-hash `document_id`,
  work-list builder, schema validation, and the results ledger.
- `2222_extract_claude.py` — the driver (worklist / collate / status).
- `2225_validate_vs_hand_collected.py` — pilot agreement report vs ND/WI gold.

## Outputs
- Extraction JSONs: `1_data/10_raw/102_fna/1022_extractions/claude/<FY-batch>/<doc_stub>.json`
  (one file per document; content is exactly the model's schema object, no wrapper).
- Ledger: `1_data/10_raw/102_fna/1022_extractions/10220_extraction_results.csv`
  — one row per `(document_id, extractor, run_id)` with schema-valid flag,
  group/unit counts, and provenance. `run_id = sha256(instruction + prompt +
  schema + model_tag)`, so re-running with an unchanged spec is idempotent.

## Run arms
A run arm is `(spec, model, json root)`. `run_id = sha256(instruction + prompt +
schema + model_tag)` is computed from the spec files **as they are on disk right
now**, so a prompt edit starts a new arm. The output path is only
`<root>/<batch>/<stub>.json`, so each arm needs its OWN `--json-root`: re-running in
place overwrites the previous arm's JSONs, and collating an old root under a new spec
would relabel that arm's output (the driver refuses this; `--force` overrides).

| arm | root | run_id | model | spec |
|---|---|---|---|---|
| opus baseline | `1022_extractions/claude` | `5b2866b2` | `claude-opus-4-8[1m]` | pre-v1_2 |
| replicate | `1022_extractions/claude_run2` | — | opus | pre-v1_2 |
| **control** (no geo) | `1022_extractions/claude_v1_2_sonnet` | `01dc7c84` | `claude-sonnet-5` | v1_2, `998db7f` |
| **treatment** (geo) | `1022_extractions/claude_v1_3_geo` | `904ee8fa` | `claude-sonnet-5` | v1_3, `4809aa1` |
| **v1_4** (geo + blinding + fed-suspension) | `1022_extractions/claude_v1_4_fedsusp` | `3c73108d` | `claude-sonnet-5` | v1_4 |

**All JSONs from the arms above were deleted from the working tree (2026-08-12, Josh's
call) so that future extraction agents cannot read a prior arm's output. They remain in
git history — `git log --diff-filter=D --stat -- '1_data/10_raw/102_fna/1022_extractions'`
finds the deletion commit, and `git show <commit>^:<path>` recovers any file. The
gitignored comparison CSVs and the ledger were NOT recoverable and are gone for good;
the ledger rebuilds from `collate`. Gold `.xlsx` untouched. v1_4 has not been run yet.**

Control vs treatment differ ONLY in the `4809aa1` prompt edit (contiguity checked
against the adjacency lists; near-miss names resolved to the reference spelling), so
holding `--model-tag claude-sonnet-5` fixed makes the geography reference the single
moving part. Gold sheets exist for **WI and ND only** — NC has no gold and can be
compared run-to-run but never scored.

## Procedure (per FY-batch / state slice)
1. **Worklist.** From project root, `snap` env (or `make fna_worklist STATES="WI ND"
   JSON_ROOT=...`):
   ```
   python 2_scripts/22_extract/222_fna_waivers/2222_extract_claude.py worklist \
       --states WI ND --json-root 1_data/10_raw/102_fna/1022_extractions/claude_v1_3_geo \
       --model-tag claude-sonnet-5
   ```
   Prints the documents, their `run_id`, and per-document `READ`/`WRITE` paths, and
   creates the output directories. `[done]` marks docs whose JSON already exists —
   note this keys on the file existing, NOT on the run_id, so a fresh arm shows every
   document as not-done only because its root is empty.

2. **Fan out.** For each not-`[done]` document, spawn one Claude subagent (Agent
   tool, `general-purpose`) with a self-contained task that instructs it to:
   - Read `2220a`, `2220b`, `2220c` (the spec + schema).
   - Read the state geography reference (the second `READ` path, when the worklist
     lists one) BEFORE the PDF. Use it to (a) verify name transcriptions — canonical
     spelling goes in `name`, the verbatim print stays in `orig_text` — and (b) check
     whether a candidate joint bundle is geographically contiguous via the county
     adjacency lists. It is a STARTING POINT, not an exclusive list: never discard or
     "correct away" an area because it is absent. For large states, Grep single
     adjacency rows instead of re-Reading the whole file.
   - Read the assigned PDF (ALL pages; for >10-page PDFs pass the `pages` range —
     Read caps at 20 pages/request). Treat scanned PDFs as images and transcribe.
   - Produce one JSON object per the schema; apply the **splitting rule** (one
     group per distinct rule/action combination, even within a single serial).
   - Write the JSON (no markdown fences) to the exact `WRITE` path.
   - Return a short report (serial, #groups, #units, criterion mix, actions,
     dates, anything ambiguous) — NOT the full JSON.
   Run agents in parallel (batch of ~5–16). Keep the task prompt self-contained;
   subagents inherit no conversation context.

   **BLINDING (required — every task prompt must carry it).** Subagents have full
   repo access and will go looking for corroboration if the prompt does not forbid
   it. In the WI v1_3 run, 2 of 20 agents did exactly that: one read
   `wi_vs_gold_run2.csv` and rewrote its answer to match gold (adopting gold's
   `United States`/national/approved convention over what the document supports, and
   suppressing a second group *because* "the gold sheet shows only one row"); another
   cited the `claude_v1_2_sonnet` control arm as support for a judgment call. Both
   were re-run blinded — and the FY2009 answer CHANGED (to statewide/`null`), so the
   contamination was consequential, not cosmetic. State in each prompt that the agent
   may read ONLY the spec files (`2220a/b/c`), the rules KB, the geography reference,
   and its assigned PDF, and must NOT read: any `*.xlsx` gold sheet or `*gold*` path,
   any comparison CSV (`*vs_gold*`, `*_flat.csv`, `*run1_vs_run2*`), the ledger, the
   validator `2225`, or ANY other extraction JSON (other arms *or* other documents in
   its own arm). Ask for a one-line compliance confirmation in the report. Without
   this, agreement statistics are circular and the arm is not evidence.

3. **Collate.** Pass the SAME `--json-root`/`--model-tag` used for the worklist:
   ```
   make fna_collate STATES="WI ND" JSON_ROOT=1_data/10_raw/102_fna/1022_extractions/claude_v1_3_geo
   ```
   Validates each written JSON against `2220c_schema.json`, counts groups/units,
   and upserts the ledger. Re-dispatch agents for any `schema_invalid` / `bad_json`
   / `missing_json` rows, then re-collate.

4. **Validate vs gold (WI/ND only).**
   ```
   make fna_validate STATE=WI JSON_ROOT=1_data/10_raw/102_fna/1022_extractions/claude_v1_3_geo
   ```
   Reports name-matched units and criterion/action agreement per FY on three matching
   bases (`exact` / `gold_repaired` / `canonical` — see the `2225` docstring), with the
   typo repairs listed and a disagreement table for joint review with Josh.

   Note the unit-level comparison flattens away `groups[]`, so bundling — the channel
   the adjacency lists actually drive — is not scored here; gold does carry `group_id`
   and `number_of_groups` if that metric is wanted later.

### Gold provenance
The sheets are hand-maintained and `*.xlsx` is gitignored, so gold is **not under
version control**: a result is only interpretable against a stated sheet version, and
`2225` prints `sha256`/row count on every run for that reason. Josh hand-cleaned both
sheets on 2026-08-11 (`WI sha256=b4aca656`, 313 rows; `ND sha256=65d0f1db`, 145 rows),
fixing six transcription typos (`Milwakuee`→Milwaukee ×8 rows FY2002–07, `Onconto`,
`Richalnd`, `Waukeshaw`, `Kkidder`, `Nel`→Nelson), a trailing space, a `Lac Du/du
Flambeau` case split, and — the big one — 19 WI rows whose blank `fiscal_year` hid the
FY2025 record's groups 2–17, so FY2025 read as 1 unit instead of 20.

Consequences for reading any comparison: `exact` and `gold_repaired` should now be
IDENTICAL (no gold typos left to repair) — if they ever diverge again, a typo has crept
back into the sheet, which makes that pair a standing regression check. WI gold rose
from 281 to 298 scoreable units. Two known gaps remain and are NOT typos: 46 WI rows
have a blank `group_action` (FY2008 all 41, 2013, 2015, 2020) — and for FY2008 the
extraction is null too, so that year's "action" agreement is two blanks agreeing rather
than a verified match; and WI FY2003's `Sokagoan` plus FY2025's `Flambeau` are faithful
transcriptions of what the documents print, not errors to fix.

### Control baseline (arm 01dc7c84, scored against the cleaned gold)
| state | basis | name | action | criterion |
|---|---|---|---|---|
| WI | exact / gold_repaired | 294/298 (98.7%) | 98.0% | 99.5% |
| WI | canonical | 295/298 (99.0%) | 98.0% | 99.5% |
| ND | exact / gold_repaired | 135/136 (99.3%) | 98.5% | 97.8% |
| ND | canonical | 136/136 (100%) | 98.5% | 97.8% |

The gap between `exact` and `canonical` is now entirely extraction-side spelling —
`layfayette` (WI FY2003), `pembia` (ND FY1998), `rollette` (ND FY2014). Those three are
the concrete errors the geography reference is supposed to remove, and they are worth
+1 matched unit in each state. That is the whole name-channel headroom: criterion and
action are already ≥98%, so a treatment effect has to show up in bundling, which this
report does not score.

### Treatment result (arm 904ee8fa, WI, 20/20 schema-valid, 2026-08-11)
| arm | basis | name | action | criterion |
|---|---|---|---|---|
| control 01dc7c84 | exact | 294/298 (98.7%) | 288/294 (98.0%) | 200/201 (99.5%) |
| control 01dc7c84 | canonical | **295**/298 (99.0%) | 289/295 (98.0%) | 201/202 (99.5%) |
| treatment 904ee8fa | exact | 294/298 (98.7%) | 288/294 (98.0%) | 201/202 (99.5%) |
| treatment 904ee8fa | canonical | **294**/298 (98.7%) | 288/294 (98.0%) | 201/202 (99.5%) |

**No unit-level effect, as predicted by the headroom argument above.** The composition
did change, and in offsetting directions:
- **+1 `layfayette` → `Lafayette`** (FY2003). The reference fixed the one real spelling
  error, exactly as designed, and `exact` == `canonical` now holds in WI — no
  extraction-side spelling residual is left.
- **−1 `Sokagoan` → `Sokaogon`** (FY2003). Gold stores the document's *verbatim* print,
  which the provenance note explicitly records as faithful, NOT a typo. The v1_3 spec
  puts the canonical spelling in `name`, so the extraction now disagrees with gold on a
  name it arguably transcribed better. **This is a scoring-convention gap, not an
  extraction error:** `2225` compares extraction `name` against gold's name column, but
  `name` is now canonical-by-construction while gold is verbatim-by-construction. To
  score the name channel honestly post-v1_3, compare gold against `orig_text`, or match
  on either field. Same mechanism (benign, unscoreable) behind `Ho-Chunk` →
  `Ho-Chunk Nation`, `Sokaogon Chippewa` → `...Community`, `Stockbridge Munsee` →
  `...Community` in FY2020/2024/2025.

**Bundling did not move at all.** Comparing group composition JSON-to-JSON across the
two arms: group counts identical on 20/20 documents, and the *partition of units into
groups* identical on 20/20. The four documents with any structural diff (FY2003, 2020,
2024, 2025) differ only in unit names plus two `qualification_level` labels. The
adjacency lists were used heavily by agents — verifying the Ashland–Bayfield–Iron and
Bay-Lake bundles, flagging Milwaukee–Washington as a corner-touch-only weak link, and
falsifying FY2006-a's printed claim that Langlade and West Bend form a "contiguous
sub-region" — but they *confirmed* bundles the control had already drawn the same way.
The groups-semantics fix in `7a72b12` (shared by both arms) is what settled grouping;
geography adds assurance, not different answers.

**One genuine data fix the score cannot see:** FY2025 control emitted a denied group
with **zero** geographic units — the 13-ZCTA denial was dropped on the floor. Treatment
carries it as a populated unit (ext_units 19 → 20). Real recovered record, invisible in
the agreement rates because gold's label for it (`zcta of 13 zip codes`) does not
string-match the extraction's.

**Residual WI misses are all substantive, none of them spelling:** FY2009
`national` vs `statewide` (see below), FY2005 `Winnebago` (gold has a unit the
extraction does not), FY2025 ZCTA label, FY2003 `Sokagoan`.

**FY2009 is a schema gap, not a miss.** The ARRA letter approves and denies nothing —
FNS calls the request "no longer necessary." Gold records `United States`/national/
approved; a blinded agent reading only the document produces `Wisconsin`/statewide/
`null`, because the document never prints "United States" and `group_action` has no
value for this disposition. This is the `moot`/`not_required` enum addition already on
the schema-refinement list, now confirmed load-bearing against gold.

## Notes / conventions
- **Adversarial cross-check (later):** Extractor A (OpenAI) emits the same schema;
  `2223_adjudicate_extractions.py` (not yet built) will field-compare A vs B and
  route disagreements to a Claude referee, then to `10222_human_review_queue.csv`.
- **Model tag** is recorded in the ledger (`MODEL_TAG` in `fna_extraction_results.py`);
  bump it when the harness model changes so `run_id` versions cleanly.
- **Scope:** this extractor reads response/decision PDFs, which embed the request
  (geography, serial, rule, data, dates), so extraction works from them alone.
  Application-side zips (`1023_application_docs/`) are a later enrichment.
