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
- `222_open_decisions.md` — **the open-decisions register.** Every decision awaiting
  Josh's ruling (with evidence, options, and a recommendation), the deferred ones, and an
  index of what has already been settled. Read it before changing `2220b`/`2220c` or
  writing `2224`.

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
| **v1_5** (adjudications, below) | `1022_extractions/claude_v1_5_adjud` | `fe5d1b3c` | `claude-sonnet-5` | v1_5 |

The v1_5 arm now holds WV (23) + WY (10) from 2026-08-14, **KY (24) + GA (24)**,
**AR (15) + SC (14)**, **KS (9) + NE (9) + MS (10)** and **IN (16)** from the same day, plus
**MO (19)**, **AL (20)**, **UT (23) + LA (22)** and **MT (27) + SD (30)** on 2026-08-15, and
**MD (25) + MI (22)**, **FL (15)**, **TN (23)** and **ID (23)** on 2026-08-16, and **OK (9)** and
**VA (20) + OH (19)** on 2026-08-17, and **WA (35)** on 2026-08-20, and **TX (16)** and **NV (28)** on 2026-08-25; every state ran under the
identical spec, so they share `run_id fe5d1b3c`. As of 2026-08-25 the ledger holds **649 documents
across 34 states** in this arm (`run_id` prefix `fe5d1b3c`) — more than the per-run sections below
account for, because ID, OK, IL and NJ were extracted by other sessions and have no section in this
file. Trust the ledger, not the sum of the sections.

**All JSONs from the arms above were deleted from the working tree (2026-08-12, Josh's
call) so that future extraction agents cannot read a prior arm's output. They remain in
git history — `git log --diff-filter=D --stat -- '1_data/10_raw/102_fna/1022_extractions'`
finds the deletion commit, and `git show <commit>^:<path>` recovers any file. The
gitignored comparison CSVs and the ledger were NOT recoverable and are gone for good;
the ledger rebuilds from `collate`. Gold `.xlsx` untouched.**

Control vs treatment differ ONLY in the `4809aa1` prompt edit (contiguity checked
against the adjacency lists; near-miss names resolved to the reference spelling), so
holding `--model-tag claude-sonnet-5` fixed makes the geography reference the single
moving part. Gold sheets now exist for **WI, ND, DE, IA, WV and WY** (DE/IA hand-collected
2026-08-12; **WV and WY 2026-08-15** — WV at 547 scored units is the largest sheet in the
project, WY at 9 the smallest but it covers that state's entire corpus. See
`222_open_decisions.md` § "Gold-sheet corrections — WV and WY" for both evals: **all 69
disagreements across the two states adjudicated to gold errors, gold typos, or open
conventions — none to the extraction**). NC still has none and can be compared run-to-run
but never scored. A state
is scoreable iff `1_data/<CODE>-hand-collected.xlsx` exists — `2225` resolves the path
from the state code, so a new sheet becomes scoreable by dropping the file in.

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

### v1_4 result (arm `3c73108d`, sonnet-5, 2026-08-12)
All 56 WI+ND+NC response documents extracted blind, 56/56 schema-valid, plus the 7 DE+IA
documents run earlier the same day under the same spec. Scored against all four gold
sheets (WI `b4aca656`, ND `65d0f1db`, DE `b0bed9ed`, IA `aec15241`). `exact`,
`gold_repaired` and `canonical` are IDENTICAL in every state — no transcription typo is
left on either side, which is the standing regression check passing.

| state | gold FYs | name | action | criterion |
|---|---|---|---|---|
| WI | 17 | 294/298 (98.7%) | 290/294 (98.6%) | 198/202 (98.0%) |
| ND | 23 | 145/145 (100%) | 143/145 (98.6%) | 142/145 (97.9%) |
| DE | 3 | 4/5 (80.0%) | 4/4 (100%) | 4/4 (100%) |
| IA | 4 | 7/7 (100%) | 7/7 (100%) | 3/6 (50.0%) |

**vs the 01dc7c84 control**, WI action improved (288→290 of 294) while WI criterion
REGRESSED (200/201 → 198/202). Both criterion losses are the new federal-suspension
rule: WI FY2011 and FY2021 are coded `federal_suspension` where gold says `EUB`. ND is
not directly comparable — its denominator rose 136→145 because the FY2018 fix below
un-hid a whole document — but ND name agreement is now 100% on the `exact` basis, i.e.
the `pembia`/`rollette` class the geography reference targets is gone.

**The federal-suspension rule is applied inconsistently across agents, and that is the
main thing to settle.** Given documents whose waiver period sits inside an ARRA/FFCRA
window but whose text rests entirely on a DOL EB trigger and never mentions the
suspension, WI FY2021's agent read 2220b's "the state IS covered for that period no
matter what it asked for" as overriding and coded `federal_suspension`; ND FY2021 and
ND FY2022's agents read the same paragraph as descriptive and coded `eb_trigger` on the
document's stated basis. Both cite the spec. The rule needs a bright line: either it
overrides only when the DISPOSITION rests on the suspension (the "no longer necessary"
letters), or it overrides on window overlap alone. Gold currently sides with the former.

**Other findings, none of them extraction errors:**
- **ND FY2018 was invisible to scoring.** `nd-abawd-approval-10.2017-9.2018` is named by
  waiver period, not FY, so `_fy_from_name` returned null, the stub dropped out of every
  `--fys` query, and 9 ND gold units reported "no extraction JSON" despite a clean
  extraction. `_PERIOD_RE` now takes the trailing year (a federal FY is named for the
  year it ends in). Those 9 units score 9/9/9.
- **DE FY2026** is the one DE miss. FNS denies the time limit "in the specified areas"
  and never names them, so the extraction emits a denied group with an EMPTY unit list;
  gold records `statewide`, which is an inference past the document. Same schema gap as
  FY2009 — there is no way to say "areas requested but not enumerated here."
- **IA FY2011/2012/2013** are all one disagreement: gold codes `federal_suspension`,
  the extraction codes `eb_trigger`. The KB is unambiguous here — `federal_suspension`
  is defined as exactly ARRA (2009-04-01→2010-09-30) and FFCRA (2020-04-01→2023-06-30),
  and it states outright that statewide EB is "`eb_trigger` + scope." FY2011–13 is in
  neither window and all three letters cite 7 CFR 273.24(f)(2) + a DOL EB determination.
  Reads as a gold coding error, pending Josh.
- **ND FY2003 Mountrail/Sioux** (2 action + 2 criterion misses) — gold has them
  `approved`/`15_percent_rule`; the letter approves only Benson and Rolette as FY2003
  LSAs and says the state will instead use its 15% categorical-exemption authority for
  Mountrail/Sioux. The extraction reads that as a non-approval of the WAIVER. Gold is
  recording a different fact (how those ABAWDs were ultimately covered), not the FNS
  action on the waiver request. Worth deciding which the panel should hold.
- **Gold vocabulary split.** The DE/IA sheets use KB codes (`pct_20_above_natl`,
  `federal_suspension`); WI/ND use FNS-form labels (`percent_20`, `LSA`, `EUB`, `ARRA`).
  `2225` now folds both onto the KB codes before comparing; without it DE scored 0/4 on
  criterion for a pure naming difference. Unrecognized labels pass through unchanged so
  a new vocabulary shows up as a visible disagreement rather than a silent alias.

### v1_5 adjudications (spec bump `3c73108d` → `fe5d1b3c`, 2026-08-13)

Josh adjudicated the four open v1_4 disagreements after reading the source PDFs. All
four resolved, three against the extraction spec and one against gold. Ground truth is
recorded here because the prompt states the resulting RULES abstractly — deliberately
without state/FY identifiers, so that an agent extracting a scored document is not
handed its own answer.

1. **Federal suspension is disposition-based, not calendar-based.** WI FY2011 (state
   letter: "ARRA allows … through September 30, 2010. **However** … **because** the
   State meets extended unemployment benefits criteria") and WI FY2021 (FNS field 8
   rests approval on Trigger Notice 2020-18 under 7 CFR 273.24) are both `eb_trigger`.
   Gold was right. The v1_4 prompt caused this directly — FY2021's agent wrote "*Per
   this project's federal-suspension coding rule*" in `criteria_summary_text` while
   storing the EB text in `criterion_verbatim`, i.e. it read the document correctly and
   then overrode itself. FY2011 was a second, different failure: the ARRA *recital* was
   promoted into a group of its own, cued by the letter's Aug-2010 signature date even
   though the FY2011 waiver period lies wholly outside the ARRA window.
   → `2220b` now codes `federal_suspension` **only when the disposition rests on the
   suspension**; forbids groups for recited statutes; and anchors the window test on the
   WAIVER PERIOD, not the signature date. Whether the time limit was in force in a
   state-year is a pure function of (state, month) and belongs in the panel builder as a
   derived `federal_suspension_in_force` overlay — never re-derived by 63 agents.
2. **IA FY2011/12/13 → `eb_trigger` in gold** (Josh, 2026-08-13). All three cite
   7 CFR 273.24(f)(2) + a DOL EB determination and sit in neither suspension window.
   Still open as an ANALYSIS point, not an extraction one: the May 3 2011 "All Regional
   Directors" memo qualified 46 states at once, so "applying" in those years is a
   one-paragraph notification and carries little revealed-preference content. Candidate
   `blanket_national_action` flag for the panel.
3. **DE FY2026 (unenumerated denied areas) — deliberately NOT fixed.** The letter denies
   "the specified areas" without naming them, so the extraction emits a denied group with
   zero units. A `unit_enumeration` schema field was designed and declined: FY2026 is
   being dropped from the panel anyway. WI FY2009 is the same shape and stays a known
   1-unit residual.
4. **ND FY2006 Rolette → `pct20_above_natl`** (gold right, extraction wrong). The letter
   contradicts itself: item 9's opening sentence lists Rolette in the aggregate 20%-rule
   sub-region and the printed regional total includes its numbers, while the asterisk
   footnote calls it an LSA and the footnote's restatement of the 20%-rule list omits it.
   The arithmetic settles it — the group as printed is 49,500/752,843 = **6.58 → 6.6**
   against a **6.6** threshold; drop Rolette and it falls to **5.43** and fails. Rolette
   is load-bearing where the state put it, and the LSA designation is what earns the
   24-month rather than 12-month approval. (The set clearing at exactly the threshold is
   itself evidence of deliberate bundle construction — worth keeping for the paper.)
   → `2220b` gains a **two-label tie-break** under SCOPE OF A JOINT SET, with the
   drop-the-unit-and-recompute test.
5. **ND FY2003 Mountrail/Sioux — 273.24(g) exemptions are not a waiver.** The letter says
   the state "is not seeking a waiver for Sheridan County and … will use its 15 percent
   exemption authority under 7 CFR 273.24(g) to exclude residents of Mountrail and Sioux."
   Discretionary exemptions are individual-level, state-allocated, and rationed
   (15% of covered caseload; 12% from FY2020) — coverage the state BUYS, not coverage FNS
   grants. Coding them as approved waivers would erase exactly the margin the panel
   measures. → `group_action` gains **`withdrawn_by_state`**; groups gain
   **`state_alternative_coverage`** (`discretionary_exemption_273_24_g`); `2220b` gains a
   section distinguishing denied / withdrawn / never-requested, the third case going to
   `request_level.notes` with NO group (Sheridan: LSA-designated and never asked for —
   a clean revealed-preference observation that v1_4 dropped entirely).

**Answer-leak sweep of the spec files (Josh, 2026-08-13).** The spec had been teaching
to the test: several illustrative examples in `2220b` and `2220c` were lifted verbatim
from corpus documents, so an agent assigned one of those documents was handed its own
answer. All are now stated as abstract patterns. Removed:

| where | leaked | why it mattered |
|---|---|---|
| `2220b` splitting rule | "WI FY2003 (serial 2020071) approves some counties as LSAs and others under the 20% rule" | names a **gold-scored** document and its grouping |
| `2220b` group-count example | "16 LSA counties, 13 on their own 20%-rule rates, denying 50 more is 79 groups" | that is WI FY2003's *exact* split — the full answer, unnamed but verbatim |
| `2220b` LSA rule | the seven-county "Ashe, Columbus, Edgecombe, Robeson, Rutherford, Scotland and Vance" sentence | verbatim NC text + the per_unit conclusion |
| `2220b`, `2220c` evidence field | "Cleveland 6.1 is below the 6.3 threshold yet approved" | a real NC unit, rate, threshold and verdict |
| `2220b` name rule | printed "Pasguotank" → name "Pasquotank" | the exact OCR repair scored as a v1_4 improvement |
| `2220b`, `2220c` bundle_label | "70 County Group", "Advantage West Sub-region 1" | real NC bundle labels |
| `2220b`, `2220c` unit fields | "Eau Claire city", "Balance of Adams County", "Bad River Reservation" | WI units (format illustration only — weakest of these, but free to abstract) |
| `2220b` federal-suspension | the ARRA "however/because" quotation | introduced earlier the same day from WI FY2011; removed before any run used it |

`2220a` was clean. The rule going forward: **an example in the spec must be a pattern,
not a document.** Use `<Name>`, "Counties A…G", "of the form …" — never a real unit,
rate, count, serial, or state/FY that appears in the corpus. This is the same
contamination the BLINDING block guards against, arriving through the front door: an
agent obeying the blinding rule perfectly still gets the answer if the prompt contains
it. Note the leaks were not neutral illustrations — they were drawn from the documents
that had proved hardest, i.e. exactly where scored agreement was most likely inflated.
NC is unscored but is the run-to-run stability state, so its leaks mattered too.

**Scoring change — document-level join.** `2225` keyed gold to extractions on
`(state, FY, unit)`, but a fiscal year can hold several distinct FNS actions: WI FY2005
is a February *Modification* (expires 2005-03-31) and a June *Modification and Extension*
(expires 2006-03-31) on serial 2020071, and West Bend is `percent_20` in the first and
`lsa` in the second. Both extractions are faithful to their own document; the scorer was
picking whichever row it saw first. `_resolve_multi_doc` now keeps the candidate that
agrees with gold — the question is "does the corpus contain gold's action", not "did an
arbitrary pick land on it" — and PRINTS every contested unit with its competing stubs, so
the resolution is auditable and can never silently inflate a score. Five WI FY2005 units
are contested. Note the deeper issue for `2224`: these waivers run April–March, so
fiscal year is a lossy key for what is really a (serial, coverage-interval, area) tuple.

**Re-scoring v1_4 under the corrected gold + validator** (extractions unchanged, so this
isolates the gold/scorer effect from the prompt effect, which needs a re-run):

| state | name | action | criterion | note |
|---|---|---|---|---|
| WI | 294/298 (98.7%) | 290/294 (98.6%) | **199/202 (98.5%)** ← 198/202 | West Bend resolved by the join fix |
| ND | 145/145 (100%) | 143/145 (98.6%) | **142/143 (99.3%)** ← 142/145 | denominator −2: Mountrail/Sioux no longer gold-`approved` |
| DE | 4/5 (80%) | 4/4 | 4/4 | unchanged; FY2026 residual retained by choice |
| IA | 7/7 | 7/7 | **6/6 (100%)** ← 3/6 | gold corrected to `eb_trigger` |

ND FY2003 now reports `alt_coverage 0/2` and two action misses — correct: the v1_4
extractions predate `withdrawn_by_state`, so those two cells can only close on re-run.

**Re-run scope for v1_5** (~9 docs, root `1022_extractions/claude_v1_5_adjud`):
WI FY2005 ×2, FY2009, FY2011, FY2021; IA FY2011/12/13; ND FY2003, FY2006. Expected to
close: WI criterion +2, ND action +2 / `alt_coverage` 2/2, ND FY2006 criterion +1.

### KY + GA extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-14)

Tier 2's recommended next pair (see the state-priority ranking): **KY 24 docs, GA 24 docs,
220 pages, 11 of them image-only scans.** Run under the unchanged v1_5 spec, so these join
the existing arm rather than opening a new one — same `run_id`, same
`1022_extractions/claude_v1_5_adjud` root as WV/WY. One blinded sonnet subagent per PDF.

**48/48 schema-valid.** 814 groups, 2,517 geographic units. Flat CSV (gitignored):
`1022_extractions/ky_ga_extractions_v1_5_flat.csv`, 2,518 rows × 66 cols.

| | groups | units | criterion mix (unit-rows) |
|---|---|---|---|
| GA | 390 | 1,291 | percent_20 982, LSA 302, EUB 5, percent_10 2, null 1 |
| KY | 424 | 1,226 | percent_20 890, LSA 319, percent_10 7, EUB 5, null 5 |

`group_action`: approved 2,403, rejected 10, `withdrawn_by_state` 13, null 92 (all GA, and
all from the one document that is a state request with no FNS decision — see below).
`qualification_level`: joint_aggregate 1,815, per_unit 687, statewide 10.

**Neither state has a gold sheet**, so nothing here is scored. These are hand-eval /
run-to-run candidates only.

**1. Threshold-hugging bundles are systematic, not a one-off.** The ND FY2006 Rolette
finding (a bundle built to land exactly on its threshold) reproduces five more times, in
two states, across two decades:

| doc | bundle | aggregate | threshold | members below it |
|---|---|---|---|---|
| GA `approval-2018` | 66 counties | 6.0 | 6.0 | 18 of 66 |
| KY `approval-2018` | 100 counties | 6.0 | 5.7 | 39 of 100 |
| GA FY2023 | Combined Area 3 | 5.1 | 5.1 | not determinable |
| KY FY2023 | Combined Area 1 (38 cty) | 6.1 | 6.1 | not determinable |
| KY FY2024 | 98 counties | 4.5 | 4.5 | not determinable |

Two further large bundles clear by a hair with many sub-threshold members: GA FY2017
(135 counties, 6.6 vs 6.5, 43 below) and GA FY2016-b (152 counties, 7.7 vs 7.7, 50 below).
This is the strongest available evidence on deliberate strategic bundling and it is now a
cross-state regularity rather than an anecdote. Worth a dedicated exhibit in the paper.

**2. The unit-level rate field earns its keep — and exposes a reporting split.** Several
recent-vintage documents print per-county *unemployed* and *labor-force counts* but no
per-county rate. Agents divided them to run the threshold test, and where they did, they
reproduced the document's own printed combined rate exactly (GA FY2017: 4,892,311 /
74,128,211 = 6.6%; KY FY2017: 6.46% → printed 6.5%). Where the document prints *neither*
counts nor per-county rates (GA FY2020-b, GA FY2023, KY FY2023, KY FY2024, KY FY2025),
agents correctly set `qualifying_basis = unknown` rather than assuming `carried_by_group`.
Hence the large `unknown` cell: GA 348, KY 354 of ~2,500 unit-rows. **That split is itself
data** — it marks exactly the documents where load-bearing-vs-carried cannot be recovered,
and it should be carried into `2224` rather than imputed.

**3. First case of the geography reference contradicting a state's own claim.** KY FY2016-b
describes Ballard, Fulton, Graves and Hickman as "four contiguous counties." Per the
adjacency lists, Ballard's only neighbours are Carlisle and McCracken — neither Carlisle nor
any set member connects it, so the bundle is disconnected as drawn. Fulton–Hickman–Graves do
form a chain. Every earlier geo-context catch was a spelling repair; this one is substantive.
The agent kept the bundle as printed and recorded the tension in
`qualification_level_evidence`, which is the correct behaviour but leaves the fact
unqueryable — evidence to reopen the deferred `bundle_contiguous` field (D-09).

**4. The FNA filename convention fails again, in a new way.** `ga-abawd-response-fy2007` is
the **state's request**, not a response: 13 groups / 91 counties with `group_action` null
throughout, and no FNS decision content anywhere in its 7 pages. Its sibling
`ga-abawd-response-fy2007-a` is the matching FNS response — same serial 970088, same 13
groups, same 91 counties. So the response stream contains a **request/response pair filed
under one FY**, on top of the four WV/WY files already known to be misfiled. Separately,
`ga/ky-abawd-response-fy2011` and `ky-abawd-response-fy2013` are Outlook email chains, not
Waiver Response forms (GA FY2011 yields zero groups — FNS merely acknowledges receipt).
`2122` cannot infer `doc_class` from filenames; it has to read the documents.

**5. D-03 confirmed with a count.** `ga-abawd-approval-2018` and `ky-abawd-approval-2018`
both parse `fiscal_year = null` — approval-year filenames over calendar-year coverage
periods (both stated Jan 1 – Dec 31 2018). Between them they carry **166 unit-rows that
drop silently out of any `--fys` query.** Third and fourth instances of the bug class; the
"fail loudly on null `fiscal_year`" half of the D-03 recommendation is now clearly the
right call.

**6. Post-OBBB regime shift reproduces.** KY FY2026 rests entirely on the surviving
`pct10_statutory` route: five counties (Elliott, Lewis, Magoffin, Martin, Wolfe), each
individually over 10%, no 20%-rule groups at all. Against KY's own recent history — 98
counties FY2024, 117 FY2025 — that is a 117 → 5 collapse in one year. Same shape as WI
FY2026.

**Blinding.** All 48 returned compliance lines. Roughly a dozen early agents disclosed that
they had run `ls`/`find` on the output directory before writing and thereby saw *filenames*
(never contents) of sibling extractions; each stated the reading was already fixed before
the listing. Mid-run the fan-out prompt was amended to forbid listing anything under
`1022_extractions/`, and disclosures stopped. The self-reporting worked exactly as the
protocol intends. Prompt language to keep for future runs: *"The output directory already
exists. Write straight to that path — do NOT `ls`, `find`, or otherwise list any directory
under `1022_extractions/`, because the sibling filenames there are themselves off-limits."*

**7. Dropped-area coding is inconsistent across agents — see D-12.** "Area was in the prior
waiver, is not in this one" was encoded three ways: `denied` groups (GA FY1998, FY2000),
`withdrawn_by_state` groups (GA FY2002, KY FY2002), and **no group at all** (KY FY1999,
FY2000, FY2001, FY2003; GA FY1999, FY2001 — ≈44 areas, 36 of them KY). All three cite
`2220b`. This is the highest-priority item from the run: those ≈44 areas currently produce
no row, so a state quietly declining to re-request a county it previously held — close to
the purest revealed-preference signal in the corpus — is the one event with no
representation in the data.

**Per-document items to verify against the source PDFs** are listed in the *verification
checklist* at the end of `222_open_decisions.md`: 9 items that would change extracted values
(two documents printing conflicting data windows or national averages, four out-of-sequence
or hand-corrected dates, a 36-month averaging window), 8 internal count mismatches, the OCR
and word-split calls, and four recurring traps for `2224` (Macon county-vs-city,
balance-of-county units, an unnormalised `state` column, and GA FY2011's legitimate
zero-group document).

**Operational note.** The run hit the harness's 20-concurrent-subagent cap and, later, a
session usage cap that killed 13 in flight. Because each agent writes its own JSON, the
recovery is stateless: re-check which `out_json_path` files exist and re-dispatch only the
misses. No completed work was lost or redone.

### SC + AR extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-14)

Tier 1's two cleanest states (see the state-priority ranking): **AR 15 docs, SC 14 docs,
99 pages, 6 image-only scans.** Run under the unchanged v1_5 spec, so these join the
existing arm — same `run_id`, same `1022_extractions/claude_v1_5_adjud` root as
WV/WY/KY/GA. One blinded sonnet subagent per PDF.

**29/29 schema-valid.** 362 groups, 553 unit-rows. Flat CSV (gitignored):
`1022_extractions/sc_ar_extractions_v1_5_flat.csv`, 553 rows × 66 cols.

| | docs | groups | unit-rows | criterion mix (unit-rows) |
|---|---|---|---|---|
| AR | 15 | 226 | 417 | percent_20 249, LSA 161, EUB 4, percent_10 2, other 1 |
| SC | 14 | 136 | 136 | LSA 100, percent_10 29, EUB 4, percent_20 2, null 1 |

`group_action`: approved 547, rejected 5, null 1. `qualification_level`: per_unit 347,
joint_aggregate 195, statewide 11. `qualifying_basis`: own_designation 260, own_rate 160,
carried_by_group 65, unknown 57, statewide 10. `possible_double_counting` true on 67 rows.
`fiscal_year` is non-null on all 553 rows — no D-03 instances in this pair.

**Neither state has a gold sheet**, so nothing here is scored. Hand-eval / run-to-run only.

**1. AR FY2008 is the cleanest strategic-bundling observation in the corpus.** The document
splits Arkansas into two disjoint sets under the same rule and the same action:

- 42 counties as **per_unit** groups, each clearing the 5.5 threshold on its own rate;
- 31 counties as **one joint_aggregate** group in which *every single member* is below 5.5
  (range 3.7–5.4), carried entirely by a combined 5.6.

That is the weighted-set-packing choice made explicit on one page: the state qualified
everything it could individually, then bundled the exact residual that could only pass
jointly. The threshold-hugging pattern also reproduces four more times in AR alone —
FY2007's two regional sets both land at **5.9 against a 5.9 threshold** (3 of 5 and 14 of
42 members below it), FY2004's 42-county Delta set at **6.4 vs 6.3**, and FY2006's Arkansas
County at **6.4 against a 6.4 threshold**. Combined with the earlier ND/GA/KY cases, the
regularity now holds in five states across three decades.

**2. FNS sometimes recomputes rather than accepts.** AR FY2005 rejects the state's own DRA
"insufficient jobs" documentation as unsubstantiated, then independently computes a combined
24-month rate for the same 42-county set and approves it under the 20% rule instead; the
same document denies Columbia County after recalculating on a 24-month rather than the
state's 12-month window. AR FY2002 likewise denies Stone County on FNS's own arithmetic.
These are the corpus's clearest instances of the *decision rule* being contested rather than
the geography — worth isolating for the paper, and a reason `criterion_verbatim` and
`action_reason_approval_denial` both need to survive into `2224`.

**3. "Insufficient jobs" is coded two ways across agents — new decision D-13.** SC's
documents print "Insufficient Jobs" as a waiver-form heading and separately define it as LSA
designation; four SC agents coded `lsa`. AR FY2000's Conway County uses the same phrase
without an LSA tie and its agent coded `other`. Both cite `2220b`. See D-13.

**4. D-07 has its first in-corpus document.** SC FY2011 is not a state-specific response at
all — it is the FNS nationwide broadcast memo naming 49 states/areas that DOL Trigger Notice
2010-2 qualified at once. This is precisely the `blanket_national_action` object specified
during the IA FY2011/12/13 adjudication, now sitting in the corpus as a state's "FY2011
response." Any revealed-preference measure that counts it as an application is counting a
form letter.

**5. The filename convention fails a third and fourth way.** AR FY2011, FY2012 and FY2013
are one-page **state-authored** trigger notices ("Arkansas will be using the ABAWD trigger
notice specified in the memo from you on …"), with no serial, no form fields, and no FNS
action; SC FY2012 is an Outlook **email chain** in which the state opts into a pre-qualified
regional waiver (criterion and action both null). All four are filed as
`*-abawd-response-*`. Together with the GA FY2007 request/response pair and the GA/KY email
chains, that is now six distinct doc-class failures — `2122` cannot infer `doc_class` from
filenames and must read the documents.

**6. D-12 reproduces outside KY/GA.** Dropped areas again produce no row: AR FY2006 drops
~15 counties from the original 42-county DRA request (notes only), SC FY2000 drops 7
previously-LSA areas, SC FY2003-b drops 3–4, AR FY2004 leaves Perry County requested but
never adjudicated. Against that, SC FY1999 *does* emit two `denied` groups (Colleton,
Edgefield) for exactly the "no longer qualifies as an LSA" fact — the same event, coded
differently, within one state's own document series. The corpus-wide sweep D-12 calls for is
clearly warranted.

**7. D-11 (contiguity) gets two more instances, both self-inflicted by the splitting rule.**
AR FY2002's 19-county 20%-rule group is scattered across the state and not contiguous as
drawn. AR FY2008's 31-county bundle is described as "contiguous" and the *full* 73-county
area is — but once the splitting rule separates the 42 per-unit counties, the residual
31-county group is internally disconnected (Craighead's in-state neighbours all sit in the
other group). That second case is different in kind from KY FY2016-b: the document is right
and the split creates the discontinuity. `bundle_contiguous` cannot be computed on the
emitted group without recording which units were split away from it.

**8. A denied group with zero units, again.** SC FY2004-c denies a retroactive LSA
relabelling of waivers #970044/#970112 and never names the counties, so the group carries no
units — the D-06 shape (DE FY2026, WI FY2009) for the third time. Also the corpus's only
purely *procedural* denial: FNS refuses under 7 CFR 272.3(c)(2)(i) because the regional
office's own email showed the purpose was to rebuild an exhausted 15% exemption balance.

**9. One serial spans a decade.** AR waiver **980013** carries every AR response from FY1999
through FY2008 — ten documents, repeatedly modified and extended. `(state, FY)` and
`(state, serial)` are both lossy keys here; D-04's `(serial, coverage-interval, area)` tuple
is the only one that separates these actions.

**Blinding.** All 29 returned compliance lines. Six agents disclosed running `ls`/`find` on
the output directory before writing and thereby seeing sibling *filenames* (never contents),
in every case after their extraction judgment was formed and always of other states'
documents. Identical to the KY/GA pattern; the self-reporting worked. The forbidding
language was already in every prompt this run, which suggests it needs to be more prominent
rather than merely present — consider stating it in the write step itself, not only in the
blinding block.

**Per-document items to verify against the source PDFs** are listed in the *verification
checklist — SC/AR run* at the end of `222_open_decisions.md`.

### KS + NE + MS extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-14)

Three more Tier 1 states (see the state-priority ranking): **KS 9 docs, NE 9 docs, MS 10
docs, 88 pages, 7 image-only scans.** Run under the unchanged v1_5 spec, so these join the
existing arm — same `run_id`, same `1022_extractions/claude_v1_5_adjud` root as
WV/WY/KY/GA/SC/AR. One blinded sonnet subagent per PDF.

**28/28 schema-valid.** 192 groups, 304 unit-rows. Flat CSV (gitignored):
`1022_extractions/ks_ne_ms_extractions_v1_5_flat.csv`, 304 rows x 66 cols.

| | docs | groups | unit-rows | criterion mix (unit-rows) |
|---|---|---|---|---|
| MS | 10 | 149 | 164 | LSA 142, percent_20 16, EUB 3, ARRA 1, null 2 |
| KS | 9 | 21 | 115 | percent_20 108, LSA 4, EUB 1, ARRA 1, null 1 |
| NE | 9 | 22 | 25 | LSA 19, percent_10 4, percent_20 2 |

`group_action`: approved 300, null 4 (two state-authored letters, one email, one deferred
disposition — see below). `qualification_level`: per_unit 169, joint_aggregate 124,
statewide 9, unknown 2. `qualifying_basis`: own_designation 165, carried_by_group 54,
unknown 39, own_rate 38, statewide 8. `document_type`: fns_response_only 273,
full_application 26, state_request_only 5. `fiscal_year` non-null on all 304 rows — no D-03
instances. Zero denied, rejected or withdrawn groups anywhere in the three states.

**Neither KS, NE nor MS has a gold sheet**, so nothing here is scored. Hand-eval /
run-to-run only.

**1. Kansas is the densest threshold-hugging state in the corpus.** Every joint set KS
filed between FY2005 and FY2008 lands on its printed threshold (counts computed from the
extracted unit rates, not from agent prose):

| doc | bundle | aggregate | threshold | members below it |
|---|---|---|---|---|
| KS FY2008 | 27 counties ("Sub-region") | **5.6** | **5.6** | **20 of 27** (+4 exactly at; min 3.7) |
| KS FY2007 | 25 counties ("Sub-region") | **6.1** | **6.1** | **15 of 25** (+3 exactly at; min 4.0) |
| KS FY2006-a | 10 counties (LWIA Two+Three) | **6.5** | **6.5** | **6 of 10** (min 4.1) |
| KS FY2006-a | 9 counties (LWIA Five) | **6.5** | **6.5** | **4 of 9** (+1 exactly at; min 5.1) |
| KS FY2006-a | Hutchinson city (per_unit) | **6.5** | **6.5** | — (own rate == threshold) |
| KS FY2005 | LWIA Two+Three (6 cty) | **6.8** | **6.8** | **3 of 6** (min 4.6) |
| KS FY2005 | LWIA Four (3 cty) | **7.0** | **7.0** | **2 of 3** (min 6.6) |
| KS FY2005 | LWIA Five (4 cty) | 7.2 | 7.1 | 2 of 4 (clears by 0.1; min 5.4) |

Seven exact-threshold sets in four documents from one state, plus one clearing by a single
tenth. FY2008 is the strongest single observation after AR FY2008: only 3 of 27 counties
clear 5.6 on their own rates, four sit exactly at it, and the remaining twenty — down to
Clay at 3.7 — ride an aggregate equal to the threshold at the printed precision.

What Kansas adds is a **time series of the same construction**: the state re-drew the bundle
every year against a threshold moving 7.0 → 6.8 → 6.5 → 6.1 → 5.6 as the national rate fell,
and hit the number every time. Harder to explain as coincidence than a single well-fitted
bundle, and the cleanest evidence yet that the bundle is chosen *given* the threshold rather
than a pre-existing region happening to clear it. With ND FY2006, GA, KY and AR the
regularity holds in **six states across three decades**. Caveat: KS FY2004 prints no
per-county rates at all (22 units `qualifying_basis = unknown`), so the sample is documents
that printed unit rates — not all of them.

**2. Nebraska is a pure tribal-geography series and exposes a coding gap — D-14.** All nine
NE documents are one serial (**970152**, FY1998→FY2013) covering the Omaha, Winnebago and
Santee Sioux Reservations, plus Thurston County from FY2008. The Omaha and Winnebago
exemptions rest entirely on **Thurston County's** LSA designation — neither reservation is
ever DOL-designated — and eight blinded agents encoded that one recurring sentence three
incompatible ways (two `per_unit`/`own_designation` groups, six documents; one
`joint_aggregate` group, FY1998; one group with the county `own_designation` and the
reservations `carried_by_group`, FY2013-a). See D-14: the spec's LSA rule covers lists of
*designated* areas and says nothing about an area qualifying by **containment**. NE is also
the only state so far where every unit is non-standard geography (22 of 25 rows) and where
the same residents are waived twice from FY2008 (county + reservations), which
`possible_double_counting` does not catch because the named units differ.

**3. Mississippi splits cleanly into two regimes at FY2006.** FY2003–FY2005 are pure LSA
county lists (47, 47, 48 counties, one group per county under the per-unit LSA rule) — 142
of MS's 164 unit-rows and the reason MS's group count (149) is seven times Kansas's on
comparable page counts. From FY2006 the state goes statewide on a single unit (EB trigger
FY2006, 20%-rule FY2007/FY2009, EUC trigger FY2016), then returns to sub-state bundling in
FY2023. Two documents extend AND modify in one action (FY2004 adds 3 counties to 45,
FY2005 adds 2 to 45); both were kept as one `approved`/`lsa` set rather than split, since
neither the action nor the criterion differs.

**4. First "deferred" disposition — D-15.** `ms-abawd-response-fy2023` approves the
14-county Delta bundle (6.6 vs a 5.4 threshold, all 14 contiguous per the reference) and
says of Monroe and Montgomery — requested on a Stafford Act disaster declaration — that FNS
asked for more justification and **will decide in a separate letter**. The agent emitted the
group with `group_action = null`, correctly refusing the enum. But `null` is also what the
three state-authored letters produce, so "explicitly deferred" and "no FNS action in this
document" are currently indistinguishable in the flat file.

**5. The blanket-national event now spans ten documents and three criterion codes — D-07.**
KS filed a state-authored adoption letter in FY2011, FY2012 AND FY2013; MS in FY2011 and
FY2013. Blinded agents coded the criterion `null` (KS FY2011 — the letter names no rule,
deferring to an unattached All States Letter), `federal_suspension` (KS FY2012, MS FY2011 —
the letters say "suspension") and `eb_trigger` (KS FY2013, MS FY2013 — the letters say
"trigger state"). Each agent read its own page correctly; the field is tracking **the
letter's vocabulary, not the mechanism**. KS FY2012's period (through 2012-09-30) sits
outside both canonical suspension windows and its agent flagged the tension rather than
reclassifying — the v1_5 waiver-period anchoring working as designed, on a document class
the spec does not yet name.

**6. Doc-class failure count reaches ten.** Five more `*-abawd-response-*` files are not FNS
responses: KS FY2011, FY2012, FY2013 and MS FY2011 are state-authored letters TO FNS, and
MS FY2013 is an Outlook email forwarding a trigger-notice memo (the attachment itself is not
in the PDF). With the GA FY2007 request/response pair, the GA/KY email chains, the AR
FY2011–13 notices and SC FY2012, `2122` inferring `doc_class` from filenames is now refuted
ten times over.

**7. The `state` column carries `Florida` for 47 Mississippi rows.** MS FY2003's Waiver
Response form prints "Florida" in field 5; the agent transcribed it verbatim and coded
`state_name`/`state_code` as Mississippi on the surrounding evidence. Worst instance yet of
the unnormalised-`state`-column trap already flagged for `2224` — see the verification
checklist.

**8. D-11 gets a fourth instance.** KS FY2004's "Other Areas" group bundles Geary County
(north-central) with Finney and Kearny (southwest), ~200 miles apart and non-contiguous as
drawn; the same group also double-counts Finney, listed both on its own line and inside the
"Finney-Kearny LMA" component of the same total. Kept as printed, tension recorded.

**Blinding.** All 28 returned compliance lines. **One** agent (KS FY2011) disclosed running
`ls` on its output directory and seeing a single sibling filename from a different state
(`ar-abawd-response-fy2011.json`), after its judgment was formed and without opening it —
down from roughly a dozen in the KY/GA run and six in SC/AR. The forbidding language was
moved into the write step itself this run, as the SC/AR writeup recommended; the improvement
is consistent with that change. Keep the placement.

**Per-document items to verify against the source PDFs** are listed in the *verification
checklist — KS/NE/MS run* at the end of `222_open_decisions.md`: 9 items that would change
extracted values (a form naming the wrong state, an impossible date, a rate printed twice,
and the KS FY2006 Sumner sentence), 9 internal count/citation mismatches including the same
`274.24`-for-`273.24` typo on four Kansas forms, and 5 recurring traps for `2224`.

### IN extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-14)

Tier 2's next state (see the state-priority ranking): **IN 16 docs, 65 pages, 5 image-only
scans.** Run under the unchanged v1_5 spec, so these join the existing arm — same `run_id`,
same `1022_extractions/claude_v1_5_adjud` root as WV/WY/KY/GA/SC/AR/KS/NE/MS. One blinded
sonnet subagent per PDF.

**16/16 schema-valid on the first pass, no re-dispatch.** 148 groups, 276 unit-rows. Flat
CSV (gitignored): `1022_extractions/in_extractions_v1_5_flat.csv`, 276 rows × 66 cols.

| criterion (unit-rows) | | `qualification_level` | | `qualifying_basis` | |
|---|---|---|---|---|---|
| percent_20 | 196 | joint_aggregate | 156 | own_rate | 100 |
| LSA | 76 | per_unit | 112 | own_designation | 86 |
| EUB | 3 | unknown | 4 | carried_by_group | 49 |
| null | 1 | statewide | 4 | unknown | 31 |

`group_action`: approved 268, rejected 5, null 3. `document_type`: fns_response_only 263,
full_application 10, state_request_only 3. `area_type`: county 217, city 54, statewide 4.
`fiscal_year` non-null on all 276 rows — no D-03 instances. `state` is normalised to
`Indiana` on every row — no repeat of the MS `Florida` trap. Only 1 row carries
`non_standard_geography`; IN is entirely standard counties plus LAUS cities, as the tier
registry predicted.

**IN has no gold sheet**, so nothing here is scored. Hand-eval / run-to-run only.

**1. Threshold-hugging reaches a seventh state — and Indiana supplies the tightest case in
the corpus.** Sub-Region 12 lands *exactly* on its threshold in two consecutive years, and
in both years only because labor-force weighting pulls it down off the unweighted mean:

| doc | bundle | aggregate | threshold | note |
|---|---|---|---|---|
| IN FY2007 | Sub-region of Planning Region 12 | **5.9** | **5.9** | unweighted mean of members ≈ 6.45 |
| IN FY2008 | Sub-region of Planning Region 12 | **5.6** | **5.6** | unweighted mean of members ≈ 6.1 |
| IN FY2005 | Sub-Region 1 | 6.8523 | 6.9076 | **below threshold, approved** |
| IN FY2005 | Sub-Region 6 | 6.8847 | 6.9076 | **below threshold, approved** |

The FY2005 pair is the strongest single observation in the corpus on this point. Both
bundles are arithmetically *under* the threshold FNS itself recomputed, and both are
approved — they round to 6.9% at one decimal, matching the printed threshold, but the
document never states a rounding convention. Threshold-hugging at the fourth decimal, with
approval apparently turning on the rounding rule. Adding IN to ND/GA/KY/AR/KS, deliberate
bundle construction now holds in **seven states across three decades**.

**2. The decision rule itself is contested, twice, in one state.** IN FY2005 is the corpus's
clearest instance: FNS declares the state's *averaging method* erroneous, recomputes the
national rate from raw data (5.66% → 5.76%), and moves the threshold for the entire request
(6.8% → 6.9%). 29 unit-rows carry `data_nonstandard_averaging = true` as a result. IN FY2004
is the companion: FNS refuses Indiana's attempt to qualify Lake County through the
multi-state **Chicago labor market area**, then runs its own 20%-above-national backstop and
denies Portage City and Lake County on the arithmetic. With AR FY2005/FY2002 this is now a
cross-state pattern, and the Chicago-LMA refusal is the corpus's first rejection of a
*multi-state* LMA claim.

**3. A denied residual — set-packing caught in the act.** IN FY2005's Sub-Region 4 was
originally three counties. White was carved out and approved under the LSA rule; Benton and
Warren, the remainder, were **denied** as a joint set. AR FY2008 showed a state bundling the
exact residual that could only pass jointly; here the residual fails and the failure is on
the record as a denial rather than vanishing into a note. Note the document does not say
whether the test was reapplied to the two-county remainder or to the original three-county
figure (6.82%, which already fails) — the denial is arithmetically sound either way.

**4. Containment inverted — D-14's mirror image, twice.** FNS **denies Lake County** in
FY2003-b (own rate below threshold) and again in FY2004, while East Chicago, Gary and
Hammond — all inside Lake — are approved in those same documents, and East Chicago and Gary
hold approvals continuously from FY1999. D-14 (NE) asks whether an area qualifies *by*
containment in a designated area; Indiana poses the reverse, a contained city qualifying
while its container is refused. **Any panel build that assigns a county's disposition down
to its cities will get Indiana wrong**, and this is a repeated feature, not a one-off.

**5. D-12 gains a third shape, and IN supplies three more instances.** Dropped areas again
produce no row: FY1999 drops Terre Haute/Vigo, Fayette and Sullivan (left to expire, no
group); FY2001 drops Vermillion *because it "no longer meets the criteria"* — the identical
fact SC FY1999 encoded as two `denied` groups; FY2003-b treats Gary as case (c) because it
sits on a prior waiver. The new shape is **FY2002's Randolph**, which is neither dropped nor
denied: the state declines to extend it under LSA ("no longer meets the criteria") and
re-wins it under the 20% rule in the same document. The rule migration leaves no trace in
the emitted data. Note also that FY2006 restores Vermillion, Fayette and Sullivan — coverage
churns back, so a drop is not an exit, which is precisely why the sequence needs its own row
to be legible.

**6. Additions are as invisible as drops.** IN FY2008 folds its three modification counties
(Huntington, Lagrange, Floyd) directly into the existing Region 3 and Region 12 aggregate
tables. There is no "newly added" group, so a real event — the state expanding a bundle —
has no representation at group level. Same defect as D-12, opposite sign.

**7. Doc-class failures reach thirteen, and IN's three are consecutive.** FY2011, FY2012 and
FY2013 are all state-authored and contain no FNS decision: FY2011 is a forwarded email chain
carrying Indiana's request, FY2012 is an email chain in which the state notifies FNS it will
adopt the waiver ("Indiana is on the trigger list"), FY2013 is a letter from IN FSSA
referencing an FNS memo — **not attached** — that reportedly named Indiana one of **46
states** qualifying at once. That last is D-07's blanket-national-action event in a third
state, alongside the IA FY2011/12/13 memo and SC FY2011's broadcast memo.

**8. D-07's vocabulary problem reproduces inside a single state.** FY2012's agent read "on
the trigger list" → `eb_trigger`; FY2013's agent read "qualify for suspending ABAWD time
limits" → `null`, explicitly refusing to infer a rule the letter never states. Two adjacent
years, same document class, two codes, each correct on its own page. Identical to the KS/MS
split — the field tracks the letter's vocabulary, not the mechanism.

**9. The v1_5 disposition-based suspension rule held on every document that tested it.**
Four independent blinded agents declined `federal_suspension` where the calendar invited it:
FY2021-a and FY2021-b (waiver periods inside the FFCRA window, dispositions resting on DOL
Trigger Notice 2020-21 → `eb_trigger`), FY2011 (ARRA's 2010-09-30 end cited as the *reason* a
new request is needed → recital, no group), and FY2013 (suspension-flavoured vocabulary,
FFY2013 outside both windows → refused). This is the exact failure mode that produced the WI
FY2021 v1_4 error, not recurring. Positive control for the spec bump.

**10. Two documents, one coverage sequence, different serials.** FY2021-a (serial 2210002)
approves statewide coverage for 5 months, 2020-10-01→2021-02-28; FY2021-b (**no serial
printed at all**) extends the same coverage to the full 12 months on the same trigger notice.
Straight D-04 material — fiscal year cannot separate the two actions, and serial cannot join
them.

**11. A serial conflict that this run can resolve but should not resolve unilaterally.**
FY2003-a prints `970088` in field 1 and in the handwritten header stamp, but its own page-1
footer reads `DIR:I:\CPB\Waiver\970155-03 Indy ext`; FY2003-b (same state, same FY) prints
`970155`, and FY1999/2000/2001/2002/2004/2005/2006/2007/2008 are all `970155`. Almost
certainly an FNS stamping error on FY2003-a. Both agents transcribed their own document
faithfully while blind — the inference is only available at run level. **Needs Josh's ruling
before `2224` keys on serial.** Separately: `970088` is also the serial on the GA FY2007
request/response pair, so **serials are not globally unique** and any join must key on
`(state, serial)`.

**12. Two distinct routes to `qualifying_basis = unknown`, and the split is informative.**
IN FY2004 prints labor-force and unemployed *counts* per county but no per-county rate: the
agent re-derived all seven sub-area combined rates and reproduced the document's own printed
totals **exactly in 7/7 cases**, yet still set `unknown`, because without per-county rates
the load-bearing member cannot be identified. IN FY2007/FY2008 are the harder case — rates
are printed per county *and* per region, but no counts, so the weighting cannot be recovered
at all (unweighted means miss the printed totals by up to ~0.5 pts). That is a genuinely new
variant: **the aggregation method is unrecoverable even where rates are printed.** Both
belong in D-10's "preserve, do not impute" column, for different reasons.

**13. A live coding ambiguity on 11 of 19 groups in FY2002.** Field 9 cites two national
reference rates in one sentence — "20 percent above the national average of 4.4 percent for
calendar years January 2000 through December 2001, and above 4.8 percent for fiscal year 2000
through 2001" — and the second clause never repeats "20 percent above." Under 4.4 × 1.2 =
5.28 every area clears alone (`per_unit`); under 4.8 × 1.2 = 5.76 five areas fail alone,
which is the spec's *strongest* `joint_aggregate` signal. The agent chose `per_unit` on
grammatical parallelism, the absence of any set-level total or bundle name, and geographic
dispersion, and preserved the alternate reading verbatim on every affected group. Correct
behaviour, but it is a coding decision on 11 groups that only a human reading of the PDF can
settle. Top of the verification checklist.

**14. The geography reference earned two catches and exposed a corrupt text layer.** FY2002
prints "Green" twice for Greene County — a one-character repair of exactly the kind the
reference was added for. FY2007's narrative roll-calls print "Dekalb"/"Dearbon" while its own
tables print "DeKalb County"/"Dearborn County"; the reference settled an *intra-document*
inconsistency. Separately, FY2002's extracted text layer renders "Perrv" where the page image
plainly shows "Perry" — the text layer is corrupt on a PDF that is not a scan, which is an
argument for image-reading even text-bearing documents.

**Blinding.** All 16 returned compliance lines and **zero agents disclosed listing anything
under `1022_extractions/`** — down from one in KS/NE/MS, six in SC/AR and roughly a dozen in
KY/GA. The forbidding language stayed in the write step where the SC/AR writeup put it; this
run is consistent with that placement being the fix. Two agents disclosed benign, in-scope
deviations (one read `002_rules_machine.yaml` to confirm criterion effective windows; one
skipped the rules KB as redundant with `2220b`), and one noted a tooling fallback
(pdfplumber/PyPDF2 absent from `snap`, fell back to the Read tool).

**Protocol deviation, disclosed.** The 16 agents were dispatched in two batches of 8. The
second batch's prompts carried a generic DOC-CLASS WARNING — that the `*-abawd-response-*`
filename convention is unreliable and `document_type`/`group_action` must be coded from what
the document actually is — which the first batch did not receive. It names no document and
supplies no answer, and it was added because three of the second batch are 1-page files where
the request/response/email-chain distinction is decisive. It is nonetheless an asymmetry
between the two batches: FY2011/2012/2013's clean doc-class calls were made with a hint the
FY1999–2005 agents did not have. Recommend making it standard prompt language for all future
runs so the asymmetry does not recur.

**Per-document items to verify against the source PDFs** are listed in the *verification
checklist — IN run* at the end of `222_open_decisions.md`.

### MO extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-15)

Tier 2 (see the state-priority ranking): **MO 19 docs, 78 pages, ~3 image-only scans.** Run
under the unchanged v1_5 spec, so these join the existing arm — same `run_id`, same
`1022_extractions/claude_v1_5_adjud` root as WV/WY/KY/GA/SC/AR/KS/NE/MS/IN. One blinded
sonnet subagent per PDF, dispatched in two batches of 10 and 9 with identical prompts.

**19/19 schema-valid on the first pass, no re-dispatch.** 282 groups, 392 unit-rows. Flat
CSV (gitignored): `1022_extractions/mo_extractions_v1_5_flat.csv`, 392 rows × 66 cols.

| criterion (unit-rows) | | `qualification_level` | | `qualifying_basis` | |
|---|---|---|---|---|---|
| percent_20 | 204 | per_unit | 250 | own_designation | 179 |
| LSA | 181 | joint_aggregate | 138 | own_rate | 145 |
| EUB | 4 | statewide | 4 | carried_by_group | 54 |
| percent_10 | 3 | | | statewide / null | 4 / 10 |

`group_action`: approved 380, `withdrawn_by_state` 7, rejected 3, null 2. `document_type`:
fns_response_only 389, state_request_only 2, full_application 1. `area_type`: county 375,
independent city 10, statewide 4, city 3. `fiscal_year` non-null on all 392 rows — no D-03
instances. `state` is normalised to `Missouri` on every row — no repeat of the MS `Florida`
trap. Only 1 row carries `non_standard_geography`.

**MO has no gold sheet**, so nothing here is scored. Hand-eval / run-to-run only.

**1. Threshold-hugging reaches an eighth state, and MO FY2004 is the densest single
document in the corpus.** Five of the state's eight named sub-areas land *exactly* on the
operative 6.3 cutoff in one letter:

| doc | bundle | aggregate | threshold | members below it |
|---|---|---|---|---|
| MO FY2004 | Sub-area of Springfield Region (6 cty) | **6.3** | **6.3** | 3 of 6 (min 4.2) |
| MO FY2004 | Sub-area of West Central Region (7 cty) | **6.3** | **6.3** | 3 of 7 (min 5.7) |
| MO FY2004 | Sub-area of Lake Ozark-Rolla Region (6) | **6.3** | **6.3** | 3 of 6 (min 5.0) |
| MO FY2004 | Sub-area of Lower East Central-Cape (7) | **6.3** | **6.3** | 1 of 7 (min 3.9) |
| MO FY2004 | Sub-area of North Central Region (4) | **6.3** | **6.3** | 2 of 4 (min 3.8) |
| MO FY2007-a | Sub-region of Greater Kansas City (6) | **6.0** | **6.0** | **4 of 6** (min 4.7) |
| MO FY2007-a | Sub-region of West Central (2) | **6.0** | **6.0** | 1 of 2 (5.8) |
| MO FY2007-a | Sub-region of Greater St. Louis (2) | **6.0** | **6.0** | 1 of 2 (5.8) |
| MO FY2007 | Sub-region of Greater Kansas City (7) | **5.9** | **5.9** | **5 of 7** (min 4.6) |
| MO FY2007 | Sub-region of Greater St. Louis (3) | **5.9** | **5.9** | 2 of 3 (min 5.7) |
| MO FY2008 | Sub-region of Greater Kansas City (10) | **5.7** | **5.7** | 4 of 10 (min 4.7) |
| MO FY2008 | Sub-region of Greater Upper Southeast (17) | **5.7** | **5.7** | 4 of 17 (min 5.0) |

Twelve exact-threshold sets across four documents, plus the FY2007-b re-filing of the same
six sub-regions and FY2007's per-unit Schuyler County at 5.9 against a 5.9 threshold. Like
Kansas, Missouri supplies a **time series of the same construction** — the Greater Kansas
City sub-region is re-drawn every year against a threshold moving 5.9 → 6.0 → 5.7 and lands
on the number each time, with membership changing (7 counties → 6 → 10) as it does. With
ND/GA/KY/AR/KS/IN the regularity now holds in **eight states across three decades**.

**2. Missouri names its own aggregation rule out loud.** FY2004 field 8 prints that the state
"decided to **combine the contiguous subareas** to calculate the eligibility for ABAWD
exemption based on the area's aggregate average unemployment rate." Every prior
threshold-hugging finding has been inferred from arithmetic; this is the first document in
which the state *states the strategy as its method*. Direct quotable evidence for the paper's
set-packing argument, and it makes the FY2004 exhibit self-documenting.

**3. Containment supplies a third distinct shape — extends D-14.** Buchanan County is
approved in FY1998-b and FY1999 not on its own designation but because **St. Joseph city,
contained within it, is the LSA** (the letters cite 1990 census data putting 86.4–87% of the
county's population in the city). Both agents independently coded it `lsa` / `per_unit` /
`own_designation` and both flagged that `qualifying_basis` has no value for "qualifies by
containing a designated area." The corpus now holds three directions of the same gap: NE
(contained reservations qualify via their container county), IN (contained cities approved
while the container county is denied), MO (container county approved via a contained city).
D-14's fix has to cover the relation, not one direction of it.

**4. D-04 gets its sharpest case: three FNS actions, one FY, one serial.** All three FY2007
documents carry serial **2070002** and are distinct actions with distinct coverage:
FY2007-b approves a 5-month window (2006-11-01→2007-03-31) that FNS deliberately split off
into a new serial because it could not align with 970129's 2-year term; FY2007-a approves
2007-04-01→2008-03-31 for two counties and six sub-regions; the unsuffixed FY2007 is a
February *modification* adding Clinton, Montgomery and Schuyler to that same period. Neither
`(state, FY)` nor `(state, serial)` separates them. Serial **970129** then runs FY1998→FY2006
(296 unit-rows, nine years) and **2070002** runs FY2007→FY2013 — the AR 980013 pattern
reproduced twice in one state.

**5. D-12 reproduces, and both codings appear inside MO's own series.** Dropped areas are
encoded two ways here: as `withdrawn_by_state` groups (FY2005 — Kansas City as an individual
LSA candidate plus a 4-county-and-city "cluster" the state pulled before FNS acted; FY2006 —
Henry County, with `state_alternative_coverage = discretionary_exemption_273_24_g`, the v1_5
field working exactly as designed), and as **no group at all** (FY1999 six counties that lost
LSA status; FY2000 five; FY2001-a seven removed from the prior waiver). That is ~18 areas
with no row, next to 7 areas that got one, for the same class of event in one state. SC did
this within a document series; MO does it within a decade of one serial.

**6. The `soft_criterion_invoked` flag earns its keep for the first time on a denial.** MO
FY2002 denies Bates, Caldwell and Chariton, which the state added by fax on a "trend of
rising unemployment" theory, because their rates cleared neither candidate threshold. Three
`rejected` rows, all `soft_criterion_invoked = true` — the cleanest available case of a soft
argument being made and refused.

**7. Doc-class failures reach fifteen.** MO FY2011 and FY2012 are both **state_request_only**
under `*-abawd-response-*` filenames — a DSS cover letter plus a Waiver Request form, with no
FNS decision anywhere, so both carry `group_action = null`. MO FY2013 is the mirror case: a
bundled **full_application** (FNS approval letter on page 1, the state's cover letter and
Waiver Request form on pages 2–5). The blanket EB-trigger era again produces the ambiguity —
these four late documents are MO's only statewide rows and its only `EUB` rows.

**8. `possible_double_counting` is document-scoped in the flat file.** All 37 FY2005 rows
carry `true` because Kansas City appears in two groups within that document (as an individual
LSA candidate and inside the withdrawn cluster). The note is accurate and correctly explains
that neither instance was approved, but the flag fires on every row of the document rather
than the two rows involved — a `2224` trap, since a row-level read of the column overstates
the affected units by ~18×.

**9. Missouri is Mountain Plains, and one agent flagged that as an anomaly.** The FY2006 agent
recorded `fns_region = Mountain Plains` and noted it as atypical ("normally Midwest"). It is
not — MO sits in FNS's Mountain Plains region, and every other MO document in the run says the
same. A false positive, recorded here so the flag in that JSON's notes is not chased later.

**Blinding.** All 19 returned compliance lines. **One** agent (FY2006) disclosed running
`ls -la` on its output directory before writing and thereby seeing two sibling *filenames*
from a different state (`ar-abawd-response-fy2005.json`, `ar-abawd-response-fy2006.json`),
after its judgment was formed and without opening either. Up from zero in the IN run, level
with KS/NE/MS. The forbidding language was in the write step as recommended; the residual
appears to be agents confirming the directory exists before writing, so the next iteration of
the prompt should say plainly that the directory is guaranteed to exist and needs no check.

**Protocol note.** The DOC-CLASS WARNING recommended at the end of the IN writeup was carried
by all 19 prompts this run, with no batch asymmetry. It paid off directly: FY2011, FY2012 and
FY2013 are exactly the class it names, and all three were coded from content.

**Per-document items to verify against the source PDFs** are listed in the *verification
checklist — MO run* at the end of `222_open_decisions.md`.

### AL extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-15)

Tier 2 (see the state-priority ranking): **AL 20 docs, 71 pages, several image-only scans.**
Run under the unchanged v1_5 spec, so these join the existing arm — same `run_id`, same
`1022_extractions/claude_v1_5_adjud` root as WV/WY/KY/GA/SC/AR/KS/NE/MS/IN/MO. One blinded
sonnet subagent per PDF, dispatched in two batches of 10 with identical prompts.

**20/20 schema-valid on the first pass, no re-dispatch.** 264 groups, 370 unit-rows. Flat CSV
(gitignored): `1022_extractions/al_extractions_v1_5_flat.csv`, 371 rows x 66 cols (the extra
row is FY2011's zero-unit group).

| criterion (unit-rows) | | `qualification_level` | | `qualifying_basis` | |
|---|---|---|---|---|---|
| LSA | 162 | per_unit | 244 | own_designation | 159 |
| percent_20 | 147 | joint_aggregate | 118 | own_rate | 145 |
| percent_10 | 53 | unknown | 7 | carried_by_group | 46 |
| null | 7 | statewide | 2 | null / unknown / statewide | 12 / 7 / 2 |

`group_action`: approved 357, rejected 10, `withdrawn_by_state` 3, null 1. `document_type`:
fns_response_only 369, state_request_only 1, other_nonstandard 1. `area_type`: county 361,
city 7, statewide 2. `fiscal_year` non-null on all 371 rows — no D-03 instances. `state` is
normalised to `Alabama` on every row. **Zero** rows carry `non_standard_geography`,
`soft_criterion_invoked` or `possible_double_counting` — AL is entirely standard counties plus
seven LAUS cities, as the tier registry predicted.

**AL has no gold sheet**, so nothing here is scored. Hand-eval / run-to-run only.

**1. Alabama runs TWO waiver serials concurrently for five years — the corpus's first, and it
breaks the denial rate.** This is the run's headline finding and it opened **D-18**.

| serial | rule | FY1999 | FY2000 | FY2001 | FY2002 | FY2003 | FY2004→2009 |
|---|---|---|---|---|---|---|---|
| **970043** | `pct10_statutory` | 12 | 9 | 11 | 12 | 15 | — (ends) |
| **970225** | `lsa` | 18 | 24 | 19 | 23 | 27 | 37 → 43 → 36 → 22 → 15 → 32 |

Counties migrate between them as their own rate crosses 10%, in both directions. When a county
drops below 10% it leaves 970043 and FNS moves it onto 970225, where its LSA designation
carries it — **coverage never lapses**. Three blinded agents hit this in three separate
documents (FY1999-a ×5 counties, FY2000-a ×1, FY2001-a ×2) and all three coded it
`group_action = denied`, each flagging that the enum has no home for a transfer.

Consequence: **8 of Alabama's 10 `rejected` unit-rows are not denials.** The only genuine
merits denials in the state are Mobile and Morgan (FY2005, own rate 6.9% against a 7.0%
threshold). A naive read of the flat file overstates AL's denial population by 5×, and the
denial rate is the panel's dependent variable.

**2. The bridge extension — an approval resting on no rule at all (D-19).** The flip side of
the transfer: rather than move a county immediately, FNS extends its 970043 coverage a few
months until 970225 can pick it up, while the county's own rate sits *below* 10%. FY2002-a
does this for Butler and Greene; FY2003-a for Clarke (9.5), Pickens (9.3), Sumter (9.8) and
Winston (9.3), all against a 10% threshold. Two blinded agents independently coded both as
`approved` / `criterion_code = null` / `qualification_level = unknown` and both refused to
invent a basis. Six unit-rows that are approvals but not qualifications — currently
indistinguishable from "criterion undeterminable."

Taken together, items 1 and 2 say something the corpus has not shown before: **FNS is
administering continuity of coverage as an objective separable from the eligibility test.**
That is discretion of exactly the kind the paper is trying to locate, and Alabama is where
it is legible because the two instruments are visible side by side.

**3. FNS recomputes to APPROVE — the missing sign.** Every prior "FNS recomputes rather than
accepts" case (IN FY2004/FY2005, AR FY2002/FY2005) ends in a denial. AL FY2000-a runs the
other way: Dallas County prints **9.95%**, the state rounds it up to "10 percent," FNS
**rejects the round-up** on the ground that the rule requires unemployment *above* 10% — then,
because current BLS county data is unavailable for Dallas, recomputes on an **older 12-month
window** (Nov 1998–Oct 1999, against Dec 1998–Nov 1999 for the other seven counties) and
approves. Stricter than asked on the rounding, then a methodological substitution that
reverses the outcome. Feeds D-16, which had only recompute-to-deny evidence.

**4. Threshold-hugging reaches a ninth state, and AL FY2006 goes past the threshold.**
FY2009's 31-county sub-region lands at **5.7 against a 5.7 threshold** with **15 of 31**
members below it — the textbook shape. But FY2006's "Sub-region of Region 4" is the stronger
observation: its own printed totals (156,822 / 2,284,825) compute to **≈6.86%**, *below* the
document's stated 6.9% threshold and further below the correctly-derived **6.96%**
(5.8 × 1.2), with **4 of 6** members below threshold — **and it was approved.** The 6.9-for-6.96
mis-rounding recurs across four groups in that document. This is the AL analogue of the IN
FY2005 pair (bundles approved arithmetically under the threshold FNS itself set), and it is
now a two-state pattern rather than an Indiana curiosity. Unit-level hugging too: FY2007 has
Lamar County, Birmingham city and Gadsden city sitting **exactly at** 6.3, and FY2006 has
Jackson County exactly at 6.6. With ND/GA/KY/AR/KS/IN/MO the regularity holds in **nine states
across three decades**.

**5. A state asking for LESS than it was entitled to.** FY2016-b records that Alabama's EUC
trigger eligibility ran a **full 12 months** (Dec 2014 → Dec 2015) but the state requested, and
FNS approved, only a **3-month** extension (2015-10-01→2015-12-31). Direct revealed-preference
evidence of a state declining available coverage — the mirror of the set-packing behaviour
documented everywhere else, and worth pairing with it in the paper.

**6. D-17 is resolved by AL's own two documents.** FY2011 (forwarded email chain, no rule
named anywhere, referenced memo not attached) → **zero units**. FY2013 (SERO broadcast,
`eb_trigger`) → **one statewide unit**. Two blinded agents, same document class, opposite
choices, each correct. That is exactly the criterion-scoped rule proposed in D-17's MO update
— emit a statewide unit iff the stated criterion has state-level scope — and it now reproduces
**7 of 7** codings across IN, MO and AL with no counterexample.

**7. D-07 gains a REGIONAL broadcast, which the flag's name does not cover.** AL FY2013's
underlying message is an FNS **Southeast Regional Office** broadcast to ABAWD contacts across
FL, NC, MS, TN, SC, KY, GA and AL — "All SERO states qualify for a continuation of the ABAWD
waiver for FY 13" — with the trigger notice not included. So the blanket event is not purely
national, and SC FY2012's opt-in to a "pre-qualified SERO-wide waiver" is retroactively the
same shape. `blanket_national_action` should become `blanket_action` with a `scope` and an
issuing office. The event now spans **fourteen documents across seven states**.

**8. D-12 reproduces in adjacent years of one serial — and AL's documents distinguish the
sub-cases the schema cannot.** 970225's FY2001 response drops **7** counties and the agent
coded all 7 as case (c), **no group**; the FY2002 response drops **3** on the same form in the
same words and that agent emitted **3 `withdrawn_by_state` groups**. What makes AL sharper than
MO is that FY2001's document separates *designation lapsed* (Lawrence, Talladega, Winston)
from *state declined to renew though still eligible* (Marengo, Perry, Pickens, Sumter) — and
case (c) discards the distinction because it has no row to carry it.

**9. Doc-class failures reach seventeen.** AL FY2011 (`state_request_only`, forwarded chain)
and AL FY2013 (`other_nonstandard`, SERO broadcast) are both filed as `*-abawd-response-*`
and neither is an FNS response to Alabama. The DOC-CLASS WARNING caught both.

**10. The v1_5 disposition-based suspension rule held again.** FY2009's waiver period
(2009-04-01→2010-03-31) sits wholly inside the ARRA window, and the agent kept
`pct20_above_natl` because the disposition rests on the 20% rule and the letter was finalised
before ARRA's enactment. Another positive control.

**11. "Insufficient jobs" resolves toward D-13's option (1), and the FNS form explains why.**
AL FY2003-b prints the bare statutory phrase in field 9 and the "does not have a sufficient
number of jobs" boilerplate in field 10, while naming LSA designation in field 8; the agent
coded `lsa`. FY1999-b and FY2000-b share that layout. **The form routinely prints the parent
prong in the decision field and the route in the request field** — so the D-13 rule should key
on the whole document, not the criterion field alone.

**Blinding.** All 20 returned compliance lines and **zero agents disclosed listing anything
under `1022_extractions/`** — matching the IN run and improving on MO's one. The write step
carried the MO writeup's recommended addition, that the output directory is *guaranteed* to
exist and needs no check; since MO's single residual was exactly an existence check, that
addition appears to have closed it. **Keep this wording.** Two agents disclosed reading
`002_rules_machine.yaml` (in scope, on the allowed list).

**Protocol deviation, disclosed.** The FY2011 and FY2013 prompts carried an extra
vintage-specific sentence — that FY2011/FY2013 files in this corpus have repeatedly proved to
be state-authored notices rather than FNS responses — which the other 18 prompts did not. It
names no document and supplies no answer, but it is a hint given precisely to the two
documents where it was decisive, and both were then classified correctly. Same class of
asymmetry the IN run flagged. **Recommend making it standard for all prompts or dropping it;
the middle position is the problem.**

**Per-document items to verify against the source PDFs** are listed in the *verification
checklist — AL run* at the end of `222_open_decisions.md`, along with the full *agent
judgment calls and deviations* list. Two items there are load-bearing for the findings above:
the FY2006 arithmetic (item 1) and the FY2000-a Dallas window substitution (item 3).

### UT + LA extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-15)

Tier 2's remaining pair (see the state-priority ranking): **UT 21 PDFs, LA 24 PDFs, 165 pages**,
plus one Utah legacy `.doc` the worklist cannot see (see the note at the end of this section).
Run under the unchanged v1_5 spec, so these join the existing arm — same `run_id`, same
`1022_extractions/claude_v1_5_adjud` root as WV/WY/KY/GA/SC/AR/KS/NE/MS/IN/MO/AL. One blinded
sonnet subagent per PDF, dispatched in a rolling fan-out against the 20-concurrent cap.

**45/45 schema-valid on the first pass, no re-dispatch.** 455 unit-rows. Flat CSV (gitignored):
`1022_extractions/ut_la_extractions_v1_5_flat.csv`, 455 rows x 66 cols. A **46th** document, the
Utah `.doc`, was found during reconciliation and extracted separately (6 more groups / 6 more
unit-rows, schema-valid); it is **not** in the ledger or the flat CSV, because both key off the
PDF-only work-list. Every count in this section is the 45-PDF figure unless stated otherwise.

| | docs | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|---|
| LA | 24 | 322 | percent_20 162, LSA 138, EUB 10, percent_10 10, null 2 | approved 314, null 3, rejected 3, withdrawn 2 | per_unit 161, joint_aggregate 143, statewide 17, null 1 |
| UT | 21 | 133 | LSA 83, percent_20 43, EUB 2, null 5 | approved 116, null 9, rejected 6, withdrawn 2 | per_unit 93, joint_aggregate 33, unknown 3, statewide 2, null 2 |

`qualifying_basis`: own_designation 220, own_rate 106, carried_by_group 64, unknown 41,
statewide 17, null 7. `document_type`: fns_response_only 426, full_application 24 (all UT,
mostly the FY2003 bundled packet), state_request_only 5. `area_type`: parish 287, county 114,
statewide 19, city 29, balance of county 3, MSA 1, null 2. `fiscal_year` non-null on all 455
rows — **no D-03 instances**, and both period-named `approval-*` files parsed correctly. `state`
is normalised to `Louisiana`/`Utah` on every row. **Zero** rows carry `non_standard_geography` or
`soft_criterion_invoked`; 15 carry `possible_double_counting` (all UT FY2001, and for a temporal
reason — see the checklist).

Serials: LA runs **970025 → 970075 → 2020121 → 2160020**; UT runs **970138** (FY1998–FY2009) then
**2140019** (FY2015–FY2020).

**Neither state has a gold sheet**, so nothing here is scored. Hand-eval / run-to-run only.

**1. FNS reverses its own denial by changing the rounding convention — the run's headline.**
`la-abawd-response-fy2001` is a bundled packet in which the Waiver Response denies Calcasieu
(balance), Livingston and West Feliciana against a stated "national rate" of 5.28%, and two
later FNS documents *in the same PDF* establish that 5.28% was never the national rate — it was
**120% of** national, mislabelled — recompute the threshold to 5.24%, round both sides to one
decimal, and **approve all three**. Calcasieu lands at exactly 5.2 against 5.2; Livingston's 5.25
becomes 5.3 under a round-half-up convention the document never states.

Same areas, same data, same rule; what changed was the rounding convention and a label error.
IN FY2005 showed an approval apparently turning on a rounding rule — here FNS *changes the
convention* and the outcome flips. This is the strongest evidence in the corpus that the
arithmetic is administered rather than applied, and it is a supersession case whose superseding
action shares a `document_id` with the action it supersedes (a shape D-02 does not currently
model).

**2. FNS recomputes to APPROVE, for the second time and without the excuse.** AL FY2000-a was
the first instance — FNS substituted an older data window for Dallas County because current data
was unavailable. `la-abawd-response-fy2003` does the same thing with no such constraint: the
state's submitted CY2001–2002 average (**6.04%** against a **6.08%** threshold) fails, FNS says
so in terms ("the State would not qualify for the waiver based on the data submitted"), and then
approves on an **earlier** window (CY2000–2001: 5.7% against 5.2%). The current data existed and
simply lost. Two states, five years apart, feeding D-16.

**3. Approvals that do not clear the stated rule now span four states.** Adding LA FY2001's
Plaquemines (5.05% against a cited national 5.04% = 100.2%, under a "Greater Than 120% of
National" heading), UT FY2009-a's San Juan (5.6/4.7 = 119.1%, literal threshold 5.64%) and LA
FY2024 (threshold stated 5.2% where 4.4 × 1.2 = 5.28 → 5.3, and the bundle's rate is 5.2%) to
IN FY2005 and AL FY2006. **LA FY2024 reproduces AL FY2006's mis-rounding exactly**, and in both
the error runs in the direction that grants coverage — worth counting corpus-wide, because a
systematically permissive rounding convention would be a finding in its own right.

**4. Threshold-hugging reaches a tenth and eleventh state — and the largest carried populations
yet.** UT FY2016 lands at 7.7 against a 7.7 threshold; UT FY2005/2006/2007/2017 and
approval-2018 all carry at least one below-threshold member. But Louisiana supplies the scale:
**LA FY2008 carries 25 of 54 rated parishes below its 6.3 threshold** (whose aggregate is
6.3 = 120% of 5.25 exactly) and **LA FY2009-a carries 27 of 48 below 5.8**. Every prior instance
has been a region; these are set-packing at the scale of a whole state. With
ND/GA/KY/AR/KS/IN/MO/AL the regularity now holds in **eleven states across three decades**.

**5. The bridge extension (D-19) is not an Alabama artifact.** Two UT documents reproduce it
under a single serial. UT FY1999-b extends Kane County ~3 months *after* stating Kane is not on
the FY1999 LSA list, "to … develop additional data to justify a further extension." UT FY2009
**denies** the state's reconsideration and extends the existing waiver through 2009-01-30 anyway
so coverage does not lapse. Both agents coded `approved` / `criterion_code = null` /
`qualification_level = unknown` and refused to invent a basis — four independent agents in two
states now converging on that encoding. Utah adds a sub-shape: AL's bridges hold coverage until a
sibling instrument picks the county up; **UT's run alongside an adverse decision**, i.e. FNS
buying the state time against its own denial.

**6. D-12's sharpest instances yet: the same COUNTY both ways, and both codings in one
document.** Utah's serial 970138 codes Uintah `denied` in FY2000 (absent from that year's LSA
list) and drops Uintah and Wayne with **no group** in FY2002 for the same fact — same county,
same serial, two years apart. And `la-abawd-response-fy1999` does both inside one letter: Acadia
gets a `withdrawn_by_state` group ("the State agency does not wish a continuation") while
Ascension and West Baton Rouge get no group ("no longer qualify as LSAs"), the split turning
purely on which verb the letter used. Bossier City is a third thing again — requested in field 8,
absent from field 9's approved list, never mentioned again. Corpus running total for the sweep is
now **≈104 areas with no row**.

**7. A waiver that rests on no labor-market rule at all — new decision D-24.**
`la-abawd-response-fy2009` approves a statewide exemption under **Stafford Act §402** and **FNA
§5(h)** after Hurricanes Gustav and Ike, on disaster impact and strained state-agency resources.
The agent grepped the rules KB for a disaster code, found none, and set `criterion_code = null`
rather than force `other` (which `2220b` scopes to soft *insufficient-jobs* evidence). First
document in the corpus whose waiver is not about the labor market in any form — and one that must
be visible enough to *exclude* from a revealed-preference measure, which `null` does not achieve.

**8. Aggregate geography as a unit — new decision D-20.** LA FY2008 and FY2009-a print the same
**New Orleans-Metairie-Kenner MSA** row on the same serial in adjacent years. FY2008's agent
expanded it into its 7 named constituent parishes (rates null, basis `unknown`) to reach the
document's own stated 61-parish count; FY2009-a's held it as one MSA unit and reported 49 units
for 55 parishes. Both reasoned explicitly. It is D-01's question arriving through Census geography
rather than a stated complement — and unlike D-01, the arithmetic cannot settle it, because no
sub-parish rates are printed. 7 of 61 and 7 of 55 parishes, sitting on the state's largest ABAWD
caseload.

**9. D-17 is now tested: 12 of 12.** Five more state-authored documents (LA FY2011/12/13, UT
FY2011/12), all stating `eb_trigger`, all emitting **one statewide unit** with
`group_action = null`. No counterexample across IN, MO, AL, LA and UT. Several agents said
explicitly that they were extending the spec's `federal_suspension` statewide-unit convention *by
analogy* because `2220b` does not name the `eb_trigger` case — the rule is doing the work while
going unstated, which is the argument for writing it down. Note all three LA letters also cite a
count of simultaneously-qualifying states (49, 46, 46), so under D-07 they are the blanket event,
not independent applications.

**10. Three new splits that are pure spec gaps, each with agents evenly divided.** `qualifying_basis`
for a lone statewide unit under a rate rule (LA 2–2: `own_rate` vs `statewide` — **D-21**);
`data_nonconformance` where the criterion has its own statutory data regime (LA 2–2: flag the
EB-trigger SA/DOL TUR as non-conforming with an explanatory note, vs leave the object null —
**D-22**); and whether a per-unit rate *derivable* from printed counts belongs in
`unemployment_rate` (UT 2–2 — **D-25**, which determines whether D-10's carried-vs-own margin is
computable on the whole count-printing document class).

**11. Partial approval on the TIME margin has no representation — new decision D-23.** LA FY2002
grants 12 of 17 requested months; UT FY1998 caps a 2-year ask at 1 year; UT FY2007 grants 17
months "as an exception" *because* the state "did not provide us with the data for a two-year
waiver approval." All three read `approved`. That last one is a graded FNS response to evidence
quality — closer to the discretion the paper is chasing than a binary approve/deny — and it is
currently recoverable only by comparing two date pairs that agents populate inconsistently.

**12. The page-header serial is corrupt in both states, and `274.24` reaches a third.** UT
FY1999-b and UT FY2000 print `907138` for `970138` in the page-3 running header; LA FY2000 prints
`907775` for `970075` in the same position. This is a property of the form's running header —
**no serial should be read from one.** Separately, the `7 CFR 274.24`-for-`273.24` typo already
recorded on four Kansas forms appears on UT FY2003 (both copies) and LA FY2009-a.

**13. A page from another state inside a state's PDF.** Page 5 of `la-abawd-response-fy2001` is a
spreadsheet headed "**ARKANSAS** ABAWD WAIVER REQUEST FOR FY 2001 UNEMPLOYMENT." The agent
recognised it and used nothing from it, but a text-only extractor would have merged Arkansas
rates into a Louisiana document. Distinct from the doc-class problem: the *file* is right, one
*page* is not. Cheap corpus-wide sweep recommended.

**14. A false-flag class the spec should close: 24-month cumulative counts.** The modern Waiver
Response BLS tables print **summed** unemployed and labor-force counts over the 24-month window,
so the labor force reads ~24x the true figure. **Four agents flagged this as document
corruption** — LA FY2017-b ("25x Louisiana's actual labor force"), UT FY2007 (West Valley City
1,450,924), UT approval-2018 (Carbon County 203,897, "probable extra-digit error") and LA FY2020
(derived the x24 relationship correctly and still filed it under flags). Only LA FY2008's agent
named the convention and verified it by summing the columns against the document's own printed
rate. Every one of the others is a false verification-checklist item costing a human a PDF
re-read. One sentence in `2220b` removes the class.

**15. `2220b` and `2220c` contradict each other on `criterion_other_explanation`.** The v1_5
two-label tie-break (from the ND FY2006 Rolette adjudication) says to record a unit's secondary
criterion label there; the schema restricts that property to `criterion_code = "other"`. Two
agents hit it independently (UT FY2005's Garfield/Duchesne, which FNS explicitly moved off the
LSA list into the 20%-rule sub-districts "to avoid having the same counties listed as approved
for both"; UT FY2007's San Juan) and both dumped the second label into free text. The v1_5
tie-break currently has no queryable home for its output. A bug, not a decision.

**16. Positive controls.** The **drop-the-unit-and-recompute tie-break** fired unprompted and
correctly on UT FY2007: prose attributes San Juan's qualification to LSA designation, but Emery +
Grand without it come to ≈6.05 against a 6.3 threshold, so the agent kept the three-county bundle
and recorded LSA as the secondary label — the Rolette rule working in a new state and in the
opposite direction. The **v1_5 disposition-based suspension rule** held on every document that
tested it: LA FY2022 (period wholly inside the FFCRA window, disposition on DOL Trigger Notice
2020-34 → `eb_trigger`) and LA FY2011 (ARRA cited as a recital about the *prior* waiver, FFY2011
outside the window → no group for the recital).

**Blinding — a regression, and the run's main procedural finding.** All 45 returned compliance
lines. **Seven disclosed a deviation**: four `ls`/`ls -la` of the output directory (each seeing
one or two Alabama sibling *filenames*, none opened) and three `mkdir -p` (revealing nothing).
All seven state the action followed their extraction judgment. Against zero in the IN and AL runs
— **with AL's "the directory is guaranteed to exist" wording carried forward verbatim**, so that
wording is not what closed AL's gap, or not the only thing. The leading hypothesis is the prompt
refactor below, and it is testable.

**Protocol deviation, deliberate and disclosed.** All 45 agents received a short dispatch pointing
at one shared task file holding the full spec-reading order, geography rules, DOC-CLASS WARNING,
blinding block and write step, plus their own PDF/GEO/OUT/PAGES; prior runs inlined the whole task
in every prompt. The motive was the asymmetry the IN and AL writeups both flagged and both asked
to be fixed — and it worked: every agent provably received byte-identical instructions, and the
DOC-CLASS WARNING was generic across all vintages, naming no document and no fiscal year. **There
is no prompt asymmetry in this run.** The cost may be the blinding regression above. Recommend
keeping the identical-instruction property but inlining the *write step and blinding block* while
leaving the rest in the file, and comparing against this run.

**17. The corpus's only non-PDF document was invisible to every prior run — and it contradicts
its own final version.** The progress table showed Utah at 21/22. The missing file is
`ut-abawd-response-fy1999-a.doc`, a complete 2-page Waiver Response in Word-for-Windows-95
format: `fna_extraction_results.build_worklist` globs `*.pdf` and `*.PDF` only, so it has never
been enumerated. It is the sole non-PDF among the manifest's 1,135 rows (the other three
exceptions are uppercase `.PDF`, which the second glob catches). Converted with `textutil` and
extracted by a blinded agent, it turns out to be **the same FNS action as
`ut-abawd-response-fy2000.pdf`** — serial 970138, state request 1999-09-30, RO transmittal
1999-11-05, the same six counties, the same five approvals, the same denial of Uintah, the same
`907138` header typo, the same 14-months-requested / 1-year-granted mismatch — and the two
extractions are structurally identical **except for the granted expiry: 2000-01-31 in the Word
file, 2001-01-31 in the PDF.** A full extra year of coverage for five counties.

Three consequences. It is a **natural replication experiment** (same action, two agents, two
source formats, everything but the disputed field agreeing) and so is direct evidence on
extraction fidelity. It is a D-02 supersession pair that no FY-keyed or serial-keyed dedupe can
find, since the two files are filed under *different* fiscal years and neither contains
"replaces"/"supersedes" language. And because the Word file is invisible to the work-list, the
corpus would otherwise have carried the PDF alone with nobody aware a conflicting version
existed. The tooling fix (a non-PDF branch, plus an assertion that the work-list reconciles
against the manifest) is recorded as non-decision item 7. The agent also flagged that the
conversion may have dropped a signature block, so UT FY1999-a's official-name fields are
**unknown, not absent**.

**Per-document items to verify against the source PDFs** are listed in the *verification
checklist — UT/LA run* at the end of `222_open_decisions.md`, along with the full *agent judgment
calls and deviations* list. Six new decisions were opened by this run: **D-20** (aggregate
geography as a unit), **D-21** (statewide `qualifying_basis`), **D-22** (`data_nonconformance`
scoping), **D-23** (duration trims), **D-24** (disaster-relief basis) and **D-25** (derived
per-unit rates).

### MT + SD extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-15) — resumed after a budget-cap interrupt

The first Tier 2.5 pair (see the state-priority ranking): **MT 27 PDFs, SD 30 PDFs**. Run under
the unchanged v1_5 spec, so these join the existing arm — same `run_id`, same
`1022_extractions/claude_v1_5_adjud` root as the fourteen states before them. **295 documents in
the arm.**

**Provenance — read this before trusting the run as a single event.** An earlier session hit a
budget cap mid-fan-out and stopped without collating, flattening, or writing any record. That
session left **41 of 57** documents extracted, **15 never dispatched**, and one
(`mt-abawd-response-fy2017`) written but **structurally invalid JSON** — an array/object nesting
break at line 546 that `collate` would have caught as `bad_json` had it ever run. This session
re-dispatched the 15 missing documents and re-ran the corrupt one (deleting the bad file first,
so the replacement agent could not read its own prior answer), then collated and flattened the
whole 57-document slice. The corpus itself was never at issue: all 57 PDFs are present on disk
and `status=ok` in the download manifest, so **nothing was re-collected**. Every count below is
the full 57-document slice.

**57/57 schema-valid.** 872 unit-rows. Flat CSV (gitignored):
`1022_extractions/mt_sd_extractions_v1_5_flat.csv`, 872 rows x 66 cols.

| | docs | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|---|
| MT | 27 | 436 | percent_20 334, LSA 61, percent_10 32, other 4, EUB 4, null 1 | approved 427, withdrawn 4, rejected 3, null 2 | joint_aggregate 241, per_unit 184, unknown 6, statewide 5 |
| SD | 30 | 436 | percent_20 300, LSA 48, percent_10 43, other 31, null 14 | approved 378, rejected 33, withdrawn 25 | per_unit 238, joint_aggregate 161, null 21, unknown 16 |

(The 436/436 split is coincidence, not a bug — the two states' document counts differ.)

`qualifying_basis`: own_rate 367, unknown 172, carried_by_group 175, own_designation 109,
statewide 5, null 44. `document_type`: fns_response_only 869, state_request_only 3 (all MT).
`area_type`: county 573, reservation area 289, statewide 5, economic area 3, county-remainder 2.
Serials: MT runs **970089/970090/970146 → 2140013**; SD runs **970139 → 980061/980062 → 990047 →
2060050**. **Neither state has a gold sheet**, so nothing here is scored — hand-eval and
run-to-run only.

**Flags, and why this pair looks unlike every prior run.** `non_standard_geography` fires on
**291 of 872 rows** (MT 116, SD 175) and `possible_double_counting` on **245** (MT 24, **SD 221**)
— against *zero* non-standard-geography rows in the whole UT/LA run. This is the reservation
corpus arriving, and it is the substantive story of the pair.

**1. Reservation–county territorial overlap: D-14's shape, but as double-coverage rather than
containment.** SD's 221 flagged rows are overwhelmingly one relation: a reservation approved as
its own unit whose territory *is* one or more counties approved separately in the same document.
SD FY2025 is the cleanest instance — Crow Creek ↔ Buffalo, Cheyenne River ↔ Dewey/Ziebach, Pine
Ridge ↔ Oglala Lakota/Bennett, all approved, the document never acknowledging the overlap. FY2011
and FY2012 print the same relation against Pine Ridge; FY2008 requests 12 counties a second time
as reservation-area groups; FY2002 splits Bennett and Marshall into a reservation portion and an
explicit "remainder of" carve-out (the only clean, non-overlapping treatment in the state).

This is **not** the schema's core double-counting case (the same unit named twice) and every
agent said so in `double_counting_note` before setting the flag. It is D-14's containment
relation seen from the panel's side: for a county-year panel, the same territory carries two
independent grants, and a naive unit-count double-counts it. D-14 asks how the *unit* should be
coded; this asks what the *panel* should do with two units covering one place. The two need to
be answered together.

**2. Threshold-hugging reaches a twelfth and thirteenth state, and MT does it with whole
bundles.** MT `approval-2018` carries **9 of 14** counties in Group 1 and **10 of 11** in Group 2
below the 5.8% threshold; MT FY2016's two 7-county bundles are sharper still — **every single
member** of both falls below the 8.1% threshold (Flathead 7.1 down to Liberty 3.3), and the sets
clear only in aggregate at 8.1/8.07. SD FY2016 carries 5 of 8 in one bundle; SD FY2025's
"Combined Area 2" sits exactly at its printed threshold (4.4 vs 4.4), as does SD FY2020's Yankton
(4.8 vs 4.8). With ND/GA/KY/AR/KS/IN/MO/AL/UT/LA the regularity now holds in **thirteen states**.

**3. South Dakota is the corpus's soft-criterion state.** 29 of the 33 `soft_criterion_invoked`
rows in this pair are SD, and they are not incidental: SD FY2024 puts **5 of 11 groups** and
FY2023 **6 of 9** on the §273.24(f)(2)(ii) "array of evidence" route — EPOP ratios, ACS 5-year
estimates, published articles — rather than any rate test, and FY2016 approves Yankton and Lake
Traverse on an EPOP-decline rationale coded `other`. Lake Traverse is **denied** on that route in
both FY2023 and FY2024 while Standing Rock is approved at 21.9%. Any revealed-preference measure
built on rate thresholds silently drops this whole class, and it is concentrated in exactly the
tribal geographies the rate data cannot measure — the D-10/`unknown` problem and the soft-criterion
problem are the same problem here. The FY2016 agent also flagged that `qualifying_basis = own_rate`
is only the closest enum fit for EPOP, which has no fixed numeric threshold.

**4. A denial and its reversal on one serial (extends D-12/D-16).** SD serial 990047 **denies**
Standing Rock in FY2020 and **approves** it in FY2021. Unlike the D-12 cases where an area simply
vanishes, both years give it an explicit row, so the sequence is recoverable — a useful positive
control for whatever D-12 rules. SD FY2023 adds a field-level defect worth noting: field 8 reads
as a blanket approval and never mentions the Lake Traverse denial, contradicting both field 7 and
the letter's own "Partial Approval" subject line.

**5. A contiguity claim the reference refutes (extends D-11).** MT FY2017's 5-county bundle
(Big Horn, Petroleum, Prairie, Rosebud, Treasure) is called "contiguous" by the state, but Prairie
borders none of the other four per the adjacency lists. The agent kept the set as drawn and
flagged it, per spec.

**6. The geography reference cannot support the check the spec asks for, on reservations.**
Neither `mt_geo_context.md` nor `sd_geo_context.md` maps reservations to parent counties, so the
contiguity test `2220b` requires is **unperformable** on any reservation bundle — the SD FY2022
agent said so explicitly rather than inventing an answer. This is a gap in the geo-context build,
not in the extraction, and it will recur in every Tier 2.5/3 state that names reservations
(ID, OR, WA, AK, NM, AZ). Recorded as non-decision item in the checklist.

**7. D-03's requested sweep is done, and the mechanical half is fixed.** D-03 asked for a scan of
the full manifest for every file whose `fiscal_year` parses null. Result: **18 documents across 18
states**, every one in the `FY2015-2019` batch, every one an `approval-<YYYY>` variant —
AZ, CT (`-2018-revised`), GA, ID, IL, KY, MA, MD, MI, MT, NH (`10.2017%20-9.2018`, where URL-encoding
defeats `_PERIOD_RE`), NV, NY (`-47-2018` and `-plus1-2018`), OR, PA, WA, WV. The bug is confined to
that filename shape exactly as D-03 predicted. `_fy_from_name` now falls back to the last plausible
year in the stub (guarded to 1997–2029 so a serial can never be read as a year), and `_PERIOD_RE`
tolerates `%20`; corpus-wide null `fiscal_year` is now **0 of 1134**, with all existing shapes
unchanged. This is D-03 option (1) — a stopgap, not the recommended fix. **(2) and (3) are still
open**, and (3) especially: the sweep only found this class because MT tripped it, which is the
fourth time this bug has surfaced by accident. `fna_extraction_results.py` does not hash into
`run_id`, so this changed no arm.

**Per-document items to verify against the source PDFs** are listed in the *verification checklist
— MT/SD run* at the end of `222_open_decisions.md`, along with the *agent judgment calls and
deviations* list. **No new D-nn was opened.** The run instead adds evidence to **D-03** (sweep
complete, mechanical fix applied), **D-11** (MT FY2017), **D-12/D-16** (SD Standing Rock),
**D-14** (the SD overlap corpus, which materially widens it) and **D-25** (MT splits 3–1 the same
way UT split 2–2).

### MD + MI extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-16)

The first Tier 3 pair: **MD 25 PDFs, MI 22 PDFs**. Run under the unchanged v1_5 spec, so these join
the existing arm — same `run_id`, same `1022_extractions/claude_v1_5_adjud` root as the sixteen
states before them. **342 documents in the arm.**

**47/47 schema-valid**, dispatched blind in three batches (the 20-agent concurrency cap bounced two
prompts, which were re-dispatched as slots freed; no document was extracted twice), plus one document
recovered afterwards — see item 10. 751 unit-rows. Flat CSV (gitignored):
`1022_extractions/md_mi_extractions_v1_5_flat.csv`, 751 rows x 66 cols.

| | docs | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|---|
| MD | 25 | 237 | percent_20 116, other 64, LSA 47, EUB 5, percent_10 4, null 1 | approved 141, **rejected 94**, null 2 | per_unit 159, joint_aggregate 72, statewide 5, null 1 |
| MI | 22 | 514 | percent_20 474, percent_10 29, EUB 7, null 4 | approved 511, null 3 | **joint_aggregate 456**, per_unit 43, statewide 14, unknown 1 |

`qualifying_basis`: unknown 262, own_rate 179, carried_by_group 170, own_designation 47 (all MD LSA),
statewide 17, null 76. `area_type`: county 679, independent city 16 (all MD), city 17, statewide 18,
reservation area 18 (all MI, FY2025–26). `document_type`: fns_response_only 744, state_request_only 6.
Serials: MD runs **970073 → 980052 → 2060034 → 2150044**; MI runs **2040025/2040026 → 2150032**, then
stops printing serials entirely from FY2020 on. **Neither state has a gold sheet**, so nothing here is
scored — hand-eval and run-to-run only.

**The two states are near-opposites, and that is the run's finding.** MD is the corpus's denial state
and MI its bundling state; almost every aggregate below separates them rather than pooling.

**1. Michigan's bundles sit *exactly* on the threshold — the sharpest revealed-preference signal in
the project so far.** Computing `local_rate − 1.2 × national_rate` over every `percent_20` group in
the flat CSV, **all six of MI's `joint_aggregate` bundles land within ±0.06**: FY2017 +0.036, FY2018
−0.040, FY2019 −0.020, FY2020 −0.020, FY2024 −0.060, FY2025 −0.020. That is pure rounding noise
against a threshold the documents print to one decimal. The two modern statewide computations do the
same (FY2016 −0.040, FY2023 +0.060); the two pre-2010 statewide ones, which predate the bundling
regime, do not (FY2007 −0.400, FY2008 +1.140). So the hugging is a property of the constructed-bundle
era specifically, not of Michigan generally — which is what makes it evidence about construction
rather than about the labor market.

This is a stronger claim than the threshold-hugging recorded for the thirteen states before: those
found *members* below threshold inside a passing bundle, which is consistent with a state drawing a
natural region and getting lucky. Michigan's *aggregate itself* is on the line in six consecutive
bundles under six different national rates. The bundle is being solved for, not drawn and then
tested. MD's margins by contrast run from −0.06 to +0.62 and look like genuine regions that happen to
clear. Note also that Michigan's per_unit grants — the FY2025 cities and reservations — are nowhere
near the line (+0.38 to +34.18), so this is not an artifact of how the margin is computed.

The mechanism is visible in the unit counts: MI's bundles are 69, 77, 79, 80 and 82 counties out of 83
— the state includes essentially everything and then *removes* the few counties that would push the
aggregate under. FY2020 excludes exactly Allegan, Kent, Livingston, Oakland, Ottawa and Washtenaw —
Michigan's highest-employment counties. Any measure treating bundle membership as an unemployment
signal will read these as noise; they are a choice variable.

**2. Michigan constructs the anti-D-14 case — deliberate non-overlap.** FY2024 approves 82 counties
(all but Oakland) as one bundle *and* Oak Park city, which sits inside Oakland, as its own per_unit
group. FY2025 does the same with three cities, excluding each city's parent county from the 80-county
bundle. Where SD stacked a reservation grant on top of the counties it covers and never acknowledged
it, MI carves the parent out so no territory is granted twice. This is the clean positive control D-14
lacked: the same containment relation, handled correctly, in the same corpus. Whatever `2224` rules for
SD's overlaps should reproduce MI's row counts unchanged. (One unexplained residual: FY2025 also drops
Livingston, which is nobody's parent county.)

**3. Maryland is the denial state, and its denials are all soft-criterion denials.** 94 of 237
MD rows are `rejected` — 40%, against 3 rejected rows in MI and a corpus norm nearer 5%. Every one
falls in FY1999–FY2003, and the pattern is identical each year: the state requests a large block of
counties under the §273.24(f)(2)(ii) "insufficient jobs" route (low or declining E/P ratio, job
deficit, lagging job growth), FNS declines to adjudicate those criteria individually, runs its own
20%-above-national check on each county instead, and denies the ones that fail. All **96
`soft_criterion_invoked` rows in the run are MD**, and unlike SD — where the soft route was the road
to *approval* — in MD it is uniformly the road to denial. The two states bracket the criterion: it is
not that soft evidence is weak, it is that FNS treats it as weak in the Mid-Atlantic region and as
sufficient in the Mountain/Plains one. That regional split is worth checking directly before any
revealed-preference measure conditions on criterion type.

**4. All 42 `possible_double_counting` rows are MD, and they are a new shape.** They come from one
document (`md-abawd-response-fy2003`), where 18 counties each appear twice — once denied under `other`
(the soft request) and once evaluated under `pct20_above_natl` (FNS's own supplementary check), per the
splitting rule. This is neither the schema's core case (same unit named twice in one grant) nor D-14's
territorial containment: it is **criterion-track duplication**, one place adjudicated under two rules
in one letter with two different outcomes. A panel that counts unit-rows will double-count it; a panel
that dedupes on unit will silently drop whichever track it sees second — and for Cecil County the two
tracks disagree (denied under `other`, approved under `pct20`). `2224` needs an explicit rule here.

**5. Six documents named `*-response-*` are actually state letters.** MD and MI FY2011, FY2012 and
FY2013 — all six, the entire `FY2010-2014` batch for this pair — are `state_request_only`: outgoing
state notifications of intent to waive, with no FNS action anywhere on the page. Three of them state no
criterion at all (`criterion_code = null`) and three carry no serial. This is not an extraction
failure; the agents read the content and overrode the filename, which is correct. But it is a corpus
fact worth checking at the download/pairing layer before `2224` treats an FY as covered: for these six
state-years the response PDF is simply absent from the archive, and the request letter has been filed
under its name.

**6. Michigan switches regimes in FY2026.** After nine years of one giant `pct20_above_natl` bundle,
FY2026 is 29 separate `pct10_statutory` per_unit grants (15 counties, 6 cities, 8 reservation areas).
The 10%-rule is per-area by construction, so the bundling question disappears entirely. Any
specification with a state fixed effect and a post-2025 window will be identifying off a change in
FNS's *criterion menu*, not off Michigan's labor market.

**7. Sub-county geography arrives in force, as the tier registry predicted.** MD carries Baltimore city
plus Annapolis, Hagerstown, Salisbury, College Park and Laurel (16 `independent city` + 7 `city` rows);
MI carries Detroit, Flint, Grand Rapids, Pontiac, Oak Park and Bay City. Both states' warts in
`2226a_state_tier_registry.csv` are confirmed. The 18 MI reservation rows hit the **same geo-context
gap flagged in the MT/SD run** — `mi_geo_context.md` maps no reservation to a parent county, so the
contiguity test `2220b` mandates is unperformable on them. That gap has now recurred in a third state
and will recur in ID, OR, WA, AK, NM and AZ.

**8. Baltimore city + Harford County recurs as a non-contiguous bundle (extends D-11).** MD pairs them
as a "combined area" in FY2017, FY2018, FY2019 and FY2020; per the adjacency lists they share no
border, only the common neighbour Baltimore County, which is never in the waiver. Four agents
independently flagged it and all four kept the set as drawn, per spec. MD FY2024's four-county Eastern
Shore bundle has the same defect (Kent is adjacent to none of the other three), and MD FY2016-a's
seven-county set is broken by Kent sitting between Cecil and the rest. The documents call these
"economic regions," which the spec accepts in place of adjacency — but MD does it four times more than
any prior state, so if `2224` ever wants a contiguity-based check, MD is where it fails.

**9. Multi-serial documents, again.** MD FY1999 and FY2000 each bundle two complete Waiver Response
forms (970073 + 980052) behind one cover memo; FY2006 bundles 970073 + 2060034. Both agents emitted a
single JSON with an array `waiver_serial_number` and concatenated the request-level narrative fields
with `[serial]` labels — the convention established earlier in the arm, applied here without prompting.

**10. A Michigan document that no worklist could ever select.** Reconciling the run against
`1020_download_manifest.csv` after collating showed manifest MI = 22 against worklist MI = 21.
`mi-response-abawd-fy2008.pdf` transposes the doc class and "abawd" relative to every other file in
the corpus, so `_state_from_name`'s `^([a-z]{2,4})-abawd` returned `None` and the row was dropped
from `build_worklist` silently — `--states MI` could never reach it. One file in 1135, but the same
silent-filename-parse failure D-03 has now surfaced five times by accident. Fixed (optional middle
token, code still validated against `STATE_CODE_TO_NAME`); verified corpus-wide as 1133 → 1134
worklist rows, 0 unresolved state codes, no existing stub changed. `fna_extraction_results.py` does
not hash into `run_id`, so no arm moved. The document was then extracted under the same v1_5 spec,
which is why **MI is 22 documents here and the arm totals 342**. Details and the D-03 argument are in
`222_open_decisions.md` § E of the MD/MI deviations list; the same reconciliation also found
`ut-abawd-response-fy1999-a.doc`, a real UT response in Word format that no arm has extracted and
that UT's ✅ status currently hides.

**Per-document items to verify against the source PDFs** are listed in the *verification checklist —
MD/MI run* at the end of `222_open_decisions.md`, along with the *agent judgment calls and deviations*
list. **No new D-nn was opened.** The run adds evidence to **D-03** (a fifth accidental find, and the
strongest case yet for its option (3)), **D-11** (four MD non-contiguous bundles),
**D-14** (MI's deliberate parent-county exclusion, the missing positive control) and **D-25**, and
raises two items that will need a ruling if they recur: criterion-track double counting (item 4) and
mislabelled request-only documents (item 5).

### FL extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-16)

A Tier 3 single state: **FL 15 PDFs, 72 pages, 6 image-only scans.** Run under the unchanged v1_5
spec, so these join the existing arm — same `run_id`, same `1022_extractions/claude_v1_5_adjud`
root as the eighteen states before them. **357 documents in the arm.** One blinded sonnet subagent
per PDF, all 15 dispatched in a single batch (under the 20-agent cap, no bounces, no re-dispatch).

**15/15 schema-valid.** 201 groups, 228 unit-rows (229 CSV rows — the FY2006 zero-unit group emits
one). Flat CSV (gitignored): `1022_extractions/fl_extractions_v1_5_flat.csv`, 229 rows x 66 cols.

| docs | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|
| 15 | 228 | percent_20 83, LSA 79, other 23, percent_10 21, null 21, EUB 2 | approved 194, rejected 35 | per_unit 184, joint_aggregate 38, unknown 4, statewide 3 |

`qualifying_basis`: own_designation 79, own_rate 73, unknown 44, carried_by_group 22, statewide 3,
null 8. `area_type`: **county 195, city 25, balance-of-county 5**, statewide 3, null 1.
`document_type`: fns_response_only 227, other_nonstandard 2. `fiscal_year` non-null on all 229 rows.
Serials: **970133 + 970134 together carry the entire 1998–2009 run** (970134 alone on 123 rows, the
pair jointly on 103), then 2150027 for FY2016 and no serial at all in the two email documents.
**FL has no gold sheet**, so nothing here is scored — hand-eval and run-to-run only.

**1. The run's main structural finding: Florida qualifies areas using carrying sets that span
groups.** In four separate documents an area is approved on a combined rate computed over a set of
counties that are *not* the members of its emitted group:

| doc | area approved | own rate | carried by | combined | note |
|---|---|---|---|---|---|
| FY1999 | Broward | not printed | "Dade/Broward Labor Market Area (SMSA)" | 6.08 | Dade is a *separate* per_unit group on its own 6.98 |
| FY2000-a/b | Broward | not printed | Dade/Broward SMSA | 5.35 | Dade's own 6.15 also clears independently |
| FY2002 | Polk | 4.775 (below 4.90 threshold) | Polk+DeSoto+Highlands+Hardee | 5.13 | the other three are each approved elsewhere on their own bases (DeSoto pct20, Highlands/Hardee LSA) |
| FY2004-b | 3 joint bundles | — | bundles include 9 counties approved in the prior July-2004 action | 6.3 / 6.4 / 6.6 | the carrying counties are not decided by this document at all |

This is not D-20 (aggregate geography treated as a unit) and not the D-11 splitting-rule artifact
where a bundle becomes disconnected once units are split away. It is a distinct shape: **the
group's qualifying arithmetic depends on units outside the group**, either because they were
adjudicated separately in the same letter or because they were approved in an earlier action.
Consequences: (a) any threshold margin recomputed from group membership in the flat CSV is wrong
for these groups; (b) `qualifying_basis = carried_by_group` is true but underspecified — the
carrying set is unrecoverable from the row; (c) a panel that treats bundle membership as the unit
of observation will mismeasure exactly the areas whose coverage was *purchased* by bundling.
The four agents each recorded the carrying set in `qualification_level_evidence` prose, which is
the right behaviour under the current spec but leaves the fact unqueryable. **Recommend opening a
new decision item** (a `carrying_set[]` field on the group, or an explicit rule that carrying units
be emitted as zero-action members). FL is the first state where this is systematic rather than
incidental — it appears in four of the nine substantive documents.

**2. Threshold-hugging is present but weaker than MI's, and it separates by qualification level.**
Computing `local_rate − 1.2 × national_rate` over every approved `percent_20` group:

| level | n groups | min | median | max | within ±0.11 |
|---|---|---|---|---|---|
| joint_aggregate | 11 | −0.060 | +0.100 | +0.420 | **7 of 11** |
| per_unit | 29 | −0.080 | +0.508 | +1.800 | 7 of 29 |

The bundles cluster on the line; the individual grants do not. That is the same contrast MI showed,
with the same interpretation — bundles are constructed against a known threshold, individual grants
are whatever the county's rate happens to be — but FL's bundle distribution has a real right tail
(+0.30, +0.42) where MI's six bundles were all inside ±0.06. So FL is corroborating evidence for
the regularity, not a second instance of MI's sharp version. Sharpest individual cases: FY2009's
6-county "Central Florida Region" at **5.6 against a 5.6 threshold** with 4 of 6 members below it
(DeSoto 4.7, Glades 4.7, Okeechobee 5.1, Indian River 5.5), and FY2004-b's 4-county bundle plus
Daytona Beach City and Holmes County all landing at **exactly 6.3 against a 6.3 threshold**.
With the thirteen states already recorded the regularity now holds in **fourteen**.

**Caveat on these margins**: on a joint group `local_unemployment_rate_cited` is the bundle's
combined rate, and per item 1 that rate is sometimes computed over a larger set than the group.
The margins above are the documents' own printed figures, not recomputed from unit rates.

**3. The sub-county wart in the tier registry is confirmed, and it is the largest in the corpus so
far — but most of it is invisible at unit level.** 25 city rows and 5 balance-of-county rows, spread
across six documents. Two mechanisms:
- **Cities as their own grants.** FY2004-a approves 7 cities as per_unit LSA groups alongside 8
  counties; FY2005 approves 8 (5 in Miami-Dade, 3 in Palm Beach); FY2007 grants Ft. Pierce City on
  its own rate.
- **Cities nested inside a county row, with no unit of their own.** FY1998's field 8 requests 15
  cities but only Miami, Melbourne and Riviera Beach get dedicated decision lines; the other 12
  (Panama City, Ft. Lauderdale, Hallandale, Lauderdale Lakes, Hialeah, Homestead, Miami Beach,
  North Miami, Boynton Beach, Delray Beach, Lake Worth, West Palm Beach) appear only parenthetically
  inside their parent county's row. FY1999 and FY2000-a/b do the same. The agents folded them into
  the parent's `orig_text` — defensible, and the arithmetic corroborates it (3 dedicated + 12
  parenthetical = the stated 15) — but **the corpus's densest city coverage is therefore recorded
  as county rows**, in the one state where the LAUS-cities-vs-counties mismatch was flagged in
  advance. Needs a ruling before `2224`: fold, or emit the nested cities as units.
- **And the reverse operation.** FY2000-a/b deny Lakeland and Winter Haven while approving "Polk
  County less the cities of Lakeland and Winter Haven" — cities carved *out* of a county grant, with
  **no rate printed for the balance area**. Both agents set `qualification_level = unknown` there
  rather than guess. FY1999 has a "balance of Palm Beach" excluding Riviera Beach; FY1998 has
  "Balance of Dade" and "Balance of Palm Beach".

**4. Soft-criterion denials, in volume, in a second region.** 43 `soft_criterion_invoked` rows, and
in FL — as in MD — the soft route is the road to *denial*: FY1999 denies Jackson, Madison, Putnam
and Washington on a declining employment-to-population argument for lack of supporting data, and
FY2005 denies **15 of 16** EPOP groups (Hamilton is the sole approval). That is 19 of the state's
35 rejected rows. MD is the Mid-Atlantic instance and SD the Mountain/Plains counter-instance where
the same route wins approvals; FL is the Southeast instance and it sides with MD. The regional read
suggested by the MD/MI run therefore survives one more state, but it is now two-against-one rather
than a clean split, and it should be tested directly rather than assumed.

**5. Two more doc-class failures, both email chains.** `fl-abawd-response-fy2011` is an internal FNS
email exchange (specialist asks FL DCF to confirm continuation; state replies "Florida will be
operating under the statewide waiver for FFY 2011"; forwarded internally with "Last state...
Florida"), and `fl-abawd-response-fy2013` is a one-page email reading in full "Florida will adopt
the ABAWD waiver for 2013" over a forwarded regional broadcast to FL/NC/MS/TN/AL/SC/KY. Neither
carries a serial or an FNS approval verb. Both agents coded `document_type = other_nonstandard` and
then coded `group_action = approved` **by inference from the state's own statement of intent** —
explicitly flagged as a judgment call in both JSONs. This is the D-15 ambiguity from the other
direction: `null` currently means "deferred", "state letter" and "no FNS action visible", and here
two agents declined `null` and chose `approved` instead. Worth a rule. Running corpus total for
`*-abawd-response-*` files that are not FNS responses: **twelve**.

**6. A duration-only action with no geography (D-06 / D-23).** `fl-abawd-response-fy2006` is an
internal FNS memo that extends waiver 970134's *approval period* from one year to two (through
2007-09-30) and names no areas and no criterion. The agent emitted one group with zero units,
`criterion_code = null`, `qualification_level = unknown` — the third distinct thing a zero-unit
group has meant in this corpus (DE FY2026 = unenumerated denied areas; SC FY2004-c = procedural
denial; here = a pure duration action). Separately, FY2007 is a clean **duration trim**: FNS cuts a
requested 2-year approval to 1 year because the state supplied 24 months of labor-market data where
36 are required. D-23 now has both directions of the duration margin in one state.

**7. D-12 reproduces three more times**, all as silent drops: FY2001 (Franklin, Holmes — in the
prior year's approved set, absent here, note only), FY1999 (Melbourne, no longer LSA-designated and
not requested), FY2005 (Dania Beach, Hallandale Beach and Lauderdale Lakes identified by the state
as meeting LSA thresholds and then deliberately excluded from the request). The FY2005 case is the
cleanest revealed-preference observation in the FL corpus and it currently produces no row.

**8. Document-internal contradictions are unusually common in this state** — nine flagged across
the run, and two of them change what is extracted:
- **FY2000-a**: the narrative denies Polk on the whole-county rate (5.15 < 5.24) while the table
  approves Polk-less-two-cities; no rate is printed for the balance.
- **FY2005**: Dixie is a member of the approved "Upper Gulf Coast Region" *and* is swept into the
  EPOP denial, because the four-county carve-out from that denial names DeSoto/Hardee/Highlands/
  Taylor and omits Dixie. Coded literally into both groups with `possible_double_counting = true`.
- Lesser: FY2001's background says 970133 covered four counties then says "only one county
  qualified"; FY2000-b's cover memo cites a 5.22 cutoff where the form states 5.24 for the identical
  calculation (4.37 × 1.20 = 5.244); FY2002's field 17 dates the state request 2002-01-29 while the
  letter narrates requests of Feb 1 and Feb 14; FY1999's cover memo says Jan 27 where field 17 says
  Jan 22; FY2005's cover letter says "14 counties" where the tables enumerate 12; FY2001's field 18
  (RO transmittal of response) predates the amended request it answers.

**9. `possible_double_counting` fires on 38 rows and is a *third* distinct shape.** Not SD's
territorial overlap and not MD's criterion-track duplication: here it is mostly FL's own
cross-group data reuse (item 1) plus the FY2005 Dixie contradiction. Three states, three unrelated
mechanisms, one boolean — the flag is now clearly overloaded and `2224` cannot act on it without
`double_counting_note`.

**10. Data-nonconformance flags earn their keep.** `nonstandard_averaging` 8 rows,
`older_vintage` 5, `non_bls_source` 2. The two `non_bls_source` rows are FY2001's Broward+Dade
bundle, computed from **state Department of Labor** data and by summing 24 months of CLF/employed/
unemployed levels rather than averaging monthly rates — the only non-BLS source recorded in the arm
so far. `older_vintage` catches FY2004-b's Jan-2000–Dec-2001 window, which FNS itself rejects as
predating the ETA LSA-designation period under §273.24(f)(2)(iii), and FY2000-a/b's Jackson County
approval on a CY1997-98 average inside a document that states it used CY1998-99 throughout.
FY2004-b also contains the corpus's first **rejected grandfathering argument** (the state argues
the counties still meet the *previous* threshold; FNS applies the current one and denies).

**Blinding.** All 15 returned compliance lines and **none disclosed any listing or reading of a
forbidden path** — the first run in the arm with zero disclosures. The prompt carried the
`1022_extractions/` no-listing sentence inside the write step rather than only in the blinding
block, which is the change suggested after the SC/AR run; on one state's evidence that appears to
have worked. One deviation worth recording: the FY2016 agent did not consult the geography
reference, on the grounds that its single group is statewide and no adjacency question arose. That
is defensible but it means the reference-before-PDF ordering was not actually exercised on that
document.

**Per-document items to verify against the source PDFs.** Highest value first: the FY2000-a Polk
narrative/table contradiction and the FY2005 Dixie double-membership (both change extracted values);
FY1998's 12 parenthetical cities (a modeling call, not a transcription one); the FY2002 Polk
carrying set; FY2004-a's field 8 printing **"Panama"** (almost certainly Panama City) and
"Hallandale" (pre-1997 name of Hallandale Beach), both kept verbatim; the FY2001 OCR flag on a Dade
1999 unemployed figure printed as ~6,777,702 where CLF−employed implies ~677,659 (did not affect the
extraction, which used the document's own combined rate); FY2004-a and FY2004-b both printing
**"7 CFR 73.24(f)"** with a digit dropped, i.e. a form defect on serial 970134 rather than a
one-off; FY2002's Table 2(e) captioned "DeSoto County Employment Rate" where the values are
unemployment; FY2006's source text reading "a period greater than ___ years" with the number
missing in the original. **One new decision item is recommended (cross-group carrying sets, item 1);**
the run otherwise adds evidence to **D-06/D-23** (item 6), **D-11** (FY2009 DeSoto is non-adjacent
to the other five in its bundle; FY2004-a's Miami-Dade/St. Lucie correctly split as non-adjacent),
**D-12** (item 7), **D-15** (item 5) and the overloaded-`possible_double_counting` question (item 9).

### TN extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-16)

A Tier 2 single state: **TN 23 PDFs, 101 pages, 10 image-only scans** — the registry's only listed
wart for TN is OCR cost, not geography, and that held. Run under the unchanged v1_5 spec, so these
join the existing arm — same `run_id`, same `1022_extractions/claude_v1_5_adjud` root as the
nineteen states before them. **380 documents in the arm.** One blinded sonnet subagent per PDF,
dispatched 12 + 8 + 3 as slots freed under the 20-agent cap (no document extracted twice).

**23/23 schema-valid.** 312 groups, 839 unit-rows (840 CSV rows — FY2004-a's zero-unit group emits
one). Flat CSV (gitignored): `1022_extractions/tn_extractions_v1_5_flat.csv`, 840 rows x 66 cols.

| docs | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|
| 23 | 839 | percent_20 574, LSA 220, percent_10 35, EUB 4, null 7 | approved 792, rejected 25, `withdrawn_by_state` 21, null 2 | joint_aggregate 554, per_unit 275, unknown 6, statewide 5 |

`qualifying_basis`: own_rate 324, carried_by_group 228, own_designation 220, unknown 60, statewide 5.
`area_type`: county 823, balance-of-county 6, city 5, statewide 5. `document_type`: fns_response_only
834, full_application 4, state_request_only 2. `fiscal_year` non-null on all 840 rows (the D-03
stopgap resolves `approval-2.2018-1.2019`). Serials: **970084 and 970085 run in parallel from FY1999
until FY2004 merges them into 970084**; then 2150055 (FY2016-a), 2160026 (FY2016-b → FY2020).
**TN has no gold sheet**, so nothing here is scored — hand-eval and run-to-run only.

**1. Tennessee is the corpus's best single-state bundling case, and it predates Michigan's by a
decade.** Four constructed near-statewide bundles, three of them landing on the threshold at printed
precision and one approved despite missing it:

| doc | bundle | aggregate | threshold | members below it | excluded |
|---|---|---|---|---|---|
| FY2007 | 91 of 95 counties | **5.9** | **6.0** — *fails, approved anyway* | not determinable | Davidson, Knox, Rutherford, Williamson |
| FY2008 | 91 of 95 counties | **5.7** | **5.7** | **11 of 91** (min 4.1) | same four |
| FY2016-b | 86 of 95 counties | **7.7** | **7.7** | **29 of 86** (min 5.87) | + Sumner, Wilson, Cheatham, Lincoln, Moore |
| FY2017 | 86 of 95 counties (85 distinct) | **6.8** | **6.8** | **29 of 86** | same nine |

This combines the two mechanisms recorded separately before it: **Kansas's time series** (the same
construction re-drawn year after year against a threshold moving 6.0 → 5.7 → 7.7 → 6.8, hitting the
number each time) and **Michigan's include-everything-then-remove-the-metros** (the exclusions are
Nashville/Davidson, Knoxville/Knox, and the Nashville collar counties, i.e. the state's highest-
employment jurisdictions — a choice variable, not an unemployment signal). TN reaches it in FY2007,
where MI's series starts in FY2017.

**FY2007 is the sharper observation of the two mechanisms**: the printed aggregate 5.9 is *below*
the document's own printed 6.0 threshold, and field 9 nonetheless asserts the set is "20 percent
above the national average" and approves it. That is the bundle being solved for and the arithmetic
being asserted rather than checked.

**Margins over the whole state, computed as `local_rate − 1.2 × national_rate` from the flat CSV**
(restricted to `percent_20` groups where BOTH rates print numerically — 25 of the state's joint
bundles; FY2007 prints no national rate and FY2008 states it only in prose, so the two headline
documents above are *not* in this table and their figures are the documents' own):

| level | n groups | min | median | max | within ±0.11 |
|---|---|---|---|---|---|
| joint_aggregate | 24 | −0.06 | +0.14 | +1.12 | 8 of 24 |
| per_unit | 10 | −0.74 | +0.13 | +0.52 | 4 of 10 |

So TN's *routine* sub-state bundles (the FY2004–06 workforce-area sets) are not especially tight —
it is specifically the near-statewide constructions that sit on the line. Same contrast MI and FL
showed between constructed bundles and individual grants, but here it separates by bundle SIZE
rather than by qualification level. With the fourteen states already recorded the threshold-hugging
regularity now holds in **fifteen**.

**2. Three documents assert a qualifying claim the printed numbers refute — all in the approval
direction.** FY2007 (above); FY2000-b approves Weakley at **5.5 against a 5.2 national rate**, which
clears the raw national average but not the 20%-above test (6.24 required), while the same field
quotes the state citing "120 percent above"; FY2002-b claims "all of the areas … had rates greater
than 20 percent above" and the arithmetic falsifies it for many members (Putnam 4.5 vs a 4.92
threshold, Hickman 5.0 vs 5.28, **14 of 24** counties in the FY2000-01 panel below 5.76). Against
AR FY2005 and AR FY2002 — where FNS recomputed and *denied* — TN is the mirror case: the decision
rule is contested in the grant direction. Both belong in whatever exhibit isolates rule-contestation.

**3. D-12 gets its first WITHIN-state contradiction, and its largest single instance.** "Area was in
the prior waiver, is not in this one" is coded three ways inside Tennessee alone: FY2001 emits **21
explicit `withdrawn_by_state` groups**; FY2000-a, FY2002-b and FY2006 emit **no group** (Dyer and
Franklin; 13 counties; Bedford/Carter/Trousdale/Unicoi + Memphis and Morristown cities — notes
only); and `approval-2.2018-1.2019` narrows serial 2160026 from **86 counties to 16** with **no rows
for the ~70 dropped**. All prior D-12 evidence was cross-state and so attributable to agent
variation; a single state's own document series splitting three ways under one spec is not. The
86 → 16 contraction is also the largest dropped-area event in the corpus and currently the least
visible.

**4. The Michigan anti-D-14 pattern reproduces — in FY2007.** Knoxville City is granted as its own
`per_unit` group on its own rate while its parent county, Knox, is excluded from the 91-county
bundle. Same deliberate non-overlap MI ran FY2024/FY2025, ten years earlier, and a second positive
control for whatever `2224` rules on SD's stacked reservation grants.

**5. `possible_double_counting` acquires a FOURTH and FIFTH distinct mechanism.** FY2000-a: five
counties (Lauderdale, Haywood, Houston, Lake, Stewart) appear **denied under serial 970084 and
approved under 970085** — cross-serial rule migration within one PDF. FY2005: Greene, Obion and
Smith each appear in **two approved** `pct20` groups, Greene's figures an exact duplicate
(899,767/64,375/7.2%), with no reassignment language of the kind the document supplies for
Clay/Haywood/Lauderdale/Tipton. Neither is SD's territorial overlap, MD's criterion-track
duplication, or FL's cross-group data reuse. **271 of 840 TN rows carry the flag** — by far the
highest share in the arm — across mechanisms that call for opposite handling in `2224`. The flag
cannot be acted on without `double_counting_note`, and that is now demonstrated five ways.

**6. FY2005 shows the two qualifying channels substituting, and FY2004-b shows it again.** FY2005:
Monroe, Morgan and Scott print individual `pct20` rates (7.9, 11.4, 11.4) that clear the 7.1
cluster threshold outright, but FNS's stated cluster-inclusion-first policy evaluates them **only**
as members of the failing 6-county Sub-area of Workforce Area 4 (7.0 vs 7.1, denied) and they are
rescued solely by their independent LSA designation — their own qualifying rate is never credited.
FY2004-b: **WIA Seven is denied as a bundle (6.1 vs 6.3) while all seven members are approved
individually via LSA in the same letter.** These are direct observations of the constructed-bundle
route and the designation route substituting for one another on identical territory, which is the
margin the paper measures. Both currently survive only as prose in `qualification_level_evidence`.
Same unqueryability problem as FL's carrying sets.

**7. The FL cross-group carrying-set shape reproduces (supports the new decision item recommended
in the FL run).** FY2005-a approves Campbell and Cumberland on a combined 7.5% computed over a set
that also contains Monroe, Morgan and Scott — counties adjudicated in an *earlier* action and not
members of the emitted group. Both counties' own rates (6.10, 5.71) are below the 7.1 threshold, so
the grant depends entirely on units outside the group. Second state, so the shape is not
Florida-specific.

**8. D-11: the same broken bundle recurs across three documents and three independent agents.**
Workforce Sub-Area 4 (Campbell, Cumberland, Monroe, Morgan, Roane, Scott) is disconnected as drawn —
Monroe's only neighbours are Blount, Loudon, McMinn and Polk, none of them members, so Monroe reaches
the set only through non-member Loudon. Flagged independently in FY2004-b, FY2005-a and FY2006. This
is different from every prior D-11 instance: not a splitting-rule artifact and not a one-document
error, but a **persistent state-constructed region carried across years with a stable defect**.
Separately FY2002-b's 27-county `pct20` set spans Bedford (Middle TN) to Carter (far NE) and is
plainly non-contiguous, though the document never claims contiguity for it. Against that, FY2016-b's
agent *verified* contiguity properly — showing the 9 excluded counties form three fully-enclosed
enclaves, so the letter's "86 contiguous counties" claim holds.

**9. Multi-serial documents are the TN norm, not the exception.** FY1999, FY2000-a and FY2001 each
bundle two complete Waiver Response forms (970084 for the 10%-rule counties, 970085 for the LSA
counties) behind one memo; FY2004-b records FNS **merging** the two serials into 970084 going
forward. 240 of 840 rows carry the array serial `970084; 970085`. The convention established in the
MD/MI run (array `waiver_serial_number`, concatenated request-level narrative) was applied here
without prompting. TN is the cleanest demonstration that `(state, FY)` and `(state, serial)` are
both lossy — D-04's `(serial, coverage-interval, area)` tuple is what separates these actions.

**10. Two more doc-class failures, both state letters.** `tn-abawd-response-fy2011` is a printed
email from TN DHS to FNS ("Tennessee wishes to continue our ABAWD waiver for the entire state through
September 30, 2011"), and `tn-abawd-response-fy2013` a one-page TN DHS letter adopting the statewide
EUC-trigger waiver. Neither carries a serial or any FNS action; both coded `state_request_only` with
`group_action = null`. As in the MD/MI FY2011–13 case, the FNS response for those two state-years is
simply absent from the archive. Running corpus total for `*-abawd-response-*` files that are not FNS
responses: **fourteen**.

**11. A conditional expiration date (extends D-23).** FY2020's approval expires "August 31, 2021,
**or the date at which the new waiver standards become effective, whichever occurs earlier**" —
the then-pending 2019 ABAWD final-rule litigation. `waiver_expiry_date` records 2021-08-31, which
asserts an end date the document deliberately refused to fix. First conditional-duration instance
in the arm.

**12. TN never invokes the soft criterion.** `soft_criterion_invoked` is true on **0 of 840 rows**,
against MD's 96 and FL's 43. The MD/FL/SD regional reading (soft evidence = denial in the
Mid-Atlantic and Southeast, approval in the Mountain/Plains) gains a Southeast state that simply
never uses the route — which is a different fact from using it and losing, and weakens any
inference drawn from denial *rates* conditional on criterion type. TN's 25 rejected rows are all
FY2000-b and FY2004-b, on ordinary 20%-rule arithmetic.

**13. The geography reference earned its keep on the OCR state, as designed.** Repairs made against
the reference: `Dekalb`/`De Kalb` → **DeKalb** (FY1999, FY2001, FY2007), `Monore` → **Monroe** and a
prose `Putman` → **Putnam** (FY2002-b), `Grranger` → **Grainger** and `Blesoe` → **Bledsoe**
(FY2004-b). Six repairs across five documents, all on image-only or dense-table sources — the
largest spelling-channel yield of any state in the arm, which is what the Tier 2 OCR wart predicted.

**14. OCR quality check passed on the hardest document.** FY2008 is image-only and prints a
91-county table of labor-force and unemployment counts. The agent's transcription sums **exactly**
to the document's printed sub-region totals (LF 53,631,457; UE 3,046,321 → 5.68 → 5.7). An
independent internal check that the scanned-PDF path holds on dense numeric tables, and the
strongest such evidence in the arm. FY2016-b's agent likewise caught two typesetting defects in a
totals table (`371,6497` → 3,716,497; Wayne LF `15,5281` → 155,281).

**Blinding.** All 23 returned compliance lines and **none disclosed any listing or reading of a
forbidden path** — second consecutive run with zero disclosures, with the `1022_extractions/`
no-listing sentence again placed inside the write step. One spec observation worth recording: the
FY2019 agent cited the LSA rule's abstract example ("Counties A…G … based on their designation as
LSAs") as controlling, and FY2019 happens to have exactly seven LSA counties. No leak — the example
carries no real names since the sweep — but an abstracted example that still fixes a **count** can
anchor. Consider variable-length phrasing when `2220b` is next touched.

**Per-document items to verify against the source PDFs.** Highest value first, all of them things
that change or could change an extracted value: **FY2000-a's `Lauderdale`/`Lawrence` substitution**
(field 8 says the state asked to add Lauderdale; field 9 and the sibling form both act on Lawrence —
the agent followed the action text, and the two counties are non-adjacent, so this reads as a typo,
but it determines which county is coded); **FY2001's Monroe County, created by arithmetic rather
than prose** (49 − 16 + 6 = 39 requires sixteen removals, the document names fifteen plus Weakley —
an inferred `withdrawn_by_state` row, defensible under the ND Rolette precedent but inferred);
**FY1999's 46-vs-45 count** (field 9 says "the 46 counties requested," the enumeration names 45 and
omits Marion — the agent extracted the literal 45); **FY2017's duplicate Hancock row** (identical
4,887/49,847 figures, so the letter's "86 areas" are 85 distinct counties and the combined rate
double-weights Hancock); **FY2006's duplicate Marion row** (identical 311,160/19,877 in Sub-Area 5
and in an additions table — the duplicate is exactly what reconciles the document's stated "70
counties requested" against 69 distinct); **`approval-2.2018-1.2019`'s field 12 printing January 1,
2019** where the prose says January 31 and calls it "the requested 12-month period" (dropped "31");
**FY2005-a's doubled totals row** (the "unemployment divided by labor force" row prints exactly
double the totals row above it — scales equally so the 7.5% is unaffected, but the figures are
wrong); **FY2009's item 9 stating the period "will expire October 31, 2008"** against a
2008-11-01 effective date and a 2009-10-31 expiry in item 13; **FY2002-b's "36 counties" prior
waiver** against 22 continuing + 13 dropped + 2 elsewhere = 37; **FY2005's field 8 category counts**
(4+39+5+16+2 = 66 against a claimed 76); and **FY2016-b's field 2 "Initial"** against field 12's
"waiver extension" boilerplate.

**No new D-nn was opened.** The run adds evidence to **D-04** (item 9), **D-06** (FY2004-a's
zero-unit extension group, a fourth thing a zero-unit group means: an unenumerated *continuation*),
**D-11** (item 8, and a new sub-kind: a stable multi-year defect), **D-12** (item 3 — the strongest
evidence yet, and the item this run most argues for resolving), **D-14** (item 4), **D-23** (item 11),
the **overloaded-`possible_double_counting`** question (item 5, now five mechanisms) and the
**cross-group carrying-set** item recommended in the FL run (item 7, now two states). Items 2 and 6
are analysis findings rather than schema ones and belong with the paper's bundling exhibit.

### VA + OH extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-17)

Two Tier 3 states, both flagged in the registry for sub-county geography: **VA 20 PDFs, OH 19 PDFs,
150 pages, 9 image-only scans.** Run under the unchanged v1_5 spec, so these join the existing arm —
same `run_id`, same `1022_extractions/claude_v1_5_adjud` root. The ledger now holds **451 documents**
in the arm (ID and OK entered it on 2026-08-16/17 and have no section in this file; that gap is not
filled here). One blinded sonnet subagent per PDF, dispatched 13 + 7 + 7 + 4 + 6 + 2 under the
20-agent cap; no document extracted twice.

**39/39 schema-valid.** 370 groups, 1,038 unit-rows. Flat CSV (gitignored):
`1022_extractions/va_oh_extractions_v1_5_flat.csv`, 1,038 rows x 66 cols.

| | docs | groups | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|---|---|
| VA | 20 | 117 | 561 | percent_20 450, LSA 79, EUB 3, percent_10 2, null 27 | approved 551, `withdrawn_by_state` 8, null 2 | joint_aggregate 433, per_unit 98, unknown 27, statewide 3 |
| OH | 19 | 253 | 477 | percent_20 448, percent_10 13, other 11, EUB 2, null 3 | approved 460, rejected 14, null 3 | joint_aggregate 256, per_unit 216, statewide 5 |

`qualifying_basis`: VA carried_by_group 277, own_rate 126, own_designation 79, unknown 70; OH own_rate
266, carried_by_group 129, unknown 63. `document_type`: `fns_response_only` 1,025, `full_application`
7, `state_request_only` 6. Serials: VA **970283** (FY1998–FY2008) then **2140016** (FY2014→);
OH **2030065** (FY2004–FY2008) then **2160001** (FY2016→). `fiscal_year` non-null on all 1,038 rows.
**`possible_double_counting` is true on ZERO rows in both states** — the first pair in the arm with
none, against TN's 271 of 840. **Neither state has a gold sheet**, so nothing here is scored.

**1. Virginia is the sharpest bundling state in the corpus — every bundle lands on the line.**
Computing `local_rate − 1.2 × national_rate` over approved `percent_20` groups where both rates print
numerically:

| level | n groups | min | median | max | within ±0.11 |
|---|---|---|---|---|---|
| joint_aggregate | 14 | −0.08 | **−0.05** | +0.02 | **14 of 14** |
| per_unit | 15 | −0.06 | +0.28 | +1.24 | 6 of 15 |

**Fourteen of fourteen**, spanning FY2006 → FY2024 and both serials. MI's six bundles inside ±0.06 was
the previous best; VA more than doubles the count and covers nineteen years. The per_unit grants show
the usual dispersion, so this is the same constructed-vs-inherited contrast MI, FL and TN showed, in
its cleanest form. With the fifteen states already recorded the threshold-hugging regularity now holds
in **seventeen** (OH is the sixteenth, item 2).

**The sign is the interesting part, and it identifies the mechanism.** Thirteen of the fourteen margins
are ≤ 0: the printed aggregate sits AT or a hair BELOW the true 1.2 × national product and is approved
anyway. That is not FNS being lax — it is that FNS *prints* the threshold rounded to one decimal
(FY2016: national 5.8, printed threshold 6.9, true product 6.96) and the state solves against the
printed number. So the bundle is fitted to a threshold that is on average ~0.05 points below the
statutory one, and the rounding convention is itself part of the choice set. Examples: FY2019
"Combined Area 1" 5.4 vs 4.5 (54 units, margin exactly 0.000), FY2024 "Combined Area 2" 4.8 vs 4.0
(2 units, 0.000), FY2023 "Combined Area" 5.5 vs 4.6 (9 units, −0.020).

**2. Ohio runs a different and previously unseen construction: take the official region, and if it
fails, take a sub-region of it.** FY2006-b and FY2007 decompose the whole state into named Economic
Development Regions (EDRs) and, where an EDR will not clear, a **"Sub-Region of <X> EDR"**. The margins
separate the two perfectly:

| doc | full EDRs | margins | "Sub-Region of …" | margins |
|---|---|---|---|---|
| FY2007 | North Central, Northwest, East Central, Southern, Southeast, Northeast | +0.29 … +2.19 | Northern, West Central, Southwest Central, Central | **−0.108 … −0.008** |
| FY2006-b | North Central, Northwest, East Central, Southeast, Southern, Northeast | +0.24 … +1.14 | Southwest Central, West Central, Central | **−0.06 … +0.04** |

Every carved sub-region is on the line; every inherited full region clears comfortably. This is the
choice variable made visible *within a single document* — the state is not redrawing an arbitrary
bundle, it is truncating an official planning region down to the members that make the arithmetic
work. Distinct from KS's annual redraw, MI/TN's remove-the-metros, and VA's one big region. OH
overall: joint_aggregate 9 of 22 within ±0.11, per_unit 15 of 162 — the aggregate/individual contrast
holds, weaker than VA's because the loose full-EDR groups sit in the same denominator.

**3. OH FY2008 files the entire state as one 20%-rule bundle, and the arithmetic does not clear.**
88 counties, one group, printed aggregate **5.7 against a 4.8 national rate** — i.e. a 5.76 threshold
that the aggregate misses — and **37 of 88 counties print rates below it** (Mercer 3.9, Delaware 4.1,
Auglaize 4.5, Warren 4.8). FNS approved on the finding that "all of the data submitted by the State
meets the requirements of approval." The document calls it a "2-year state-wide waiver"; the agent
coded `joint_aggregate`, not `statewide`, which is correct under the spec (`statewide` is reserved for
rules with no area test). Two things follow: (a) after TN FY2007 this is the **second** case of an
asserted 20%-rule claim the printed numbers refute in the approval direction, in a second state; and
(b) `2224` needs to know that *de facto* statewide coverage can arrive as an all-county
`joint_aggregate` and will not be found by filtering on `qualification_level == statewide`.
A third, smaller instance: OH FY2007's "Sub-Region of Northern EDR" (Cuyahoga, Lake, Lorain, Geauga —
all four newly added that year) prints **5.7 against the document's own 5.8 threshold** and is approved
without comment.

**4. D-11 gets its largest instance, and the state's own label is the thing that is wrong.**
Virginia's big bundle is labelled "southern Virginia" / "Southern Region" in every year, and its
membership is not southern and not contiguous: it carries the **Eastern Shore** (Accomack,
Northampton), the **Northern Neck** (Lancaster, Northumberland, Richmond County, Westmoreland),
**northwestern mountain** counties on the WV line (Highland, Bath, Alleghany, Craig, Covington City)
and **Hampton Roads** (Hampton, Portsmouth, Williamsburg). Williamsburg city and Franklin city are
outright exclaves in several years — neither has a single in-set neighbour. **Eight documents, eight
independent blinded agents, all flagged it** (FY2006, FY2007, FY2008, FY2014, FY2016, FY2017, FY2019,
`approval-5.2018-4.2019`), every one keeping the set as drawn and recording the tension in
`qualification_level_evidence`. TN's Workforce Sub-Area 4 was the previous "stable multi-year defect";
VA's is the same kind at 54 units and nineteen years. FY2017's two-county "Shenandoah Valley …same
economic region" bundle (Bath + Page) is a clean small case: the two counties share no border.

**5. NEW — `area_type` splits `city` vs `independent city` for the same units, in three states,
and twice inside a single document. → D-26.** `2220c` defines `area_type` as free text whose
description offers **both** `city` and `independent city` as acceptable values and never says which
governs a Virginia/Maryland/Missouri independent city. Corpus-wide result:

| state | `independent city` | `city` | notes |
|---|---|---|---|
| VA | 118 rows / 15 docs | 24 rows / 2 docs | `fy2006` and `approval-5.2018-4.2019` are the outliers |
| MD | 16 rows / 16 docs | 7 rows / 4 docs | **FY1999 and FY2000 use BOTH inside one document** |
| MO | 10 rows / 10 docs | 3 rows / 2 docs | St. Louis city |

Same physical units — Danville, Martinsville, Petersburg, Baltimore, St. Louis — carry different
`area_type` in different years, and in MD's case in the same letter. Any `2224` join or filter on
`area_type` therefore silently drops or double-classifies the corpus's county-equivalent cities. This
is not agent variation to be tolerated: the spec's own vocabulary list is the cause.

**6. D-15 gets a within-state, within-series, three-document split — the sharpest instance yet.**
`va-abawd-response-fy2011`, `-fy2012` and `-fy2013` are three near-identical one-page Virginia DSS
letters to the same FNS Regional Director adopting the statewide EB-trigger waiver. **FY2011's agent
coded `group_action = approved`** (reasoning the EB route is self-executing, so the state's statement
of intent IS the disposition); **FY2012's and FY2013's coded `null`** (reasoning the spec mandates
`approved` only for `federal_suspension`, and this document contains no FNS action). All three cite
`2220b`. Every prior D-15 instance was cross-state or cross-document-class; this is one state, one
document template, three consecutive years, opposite encodings. FL FY2011/FY2013 chose `approved` on
the same shape; MD/MI, KS, MS and TN chose `null`. The field is unusable as filed.

**7. D-07: the identical document class gets `eb_trigger` in VA and `null` in OH.** VA FY2011/12/13
coded `eb_trigger` on all three; OH FY2011/12/13 coded `criterion_code = null` on all three. Each state
is internally consistent and the two are opposite. The mechanism is the same event — a state adopting a
nationally-broadcast DOL trigger determination — and the difference is purely what the letter happens
to print: Virginia's letters name "extended unemployment benefits," Ohio's cite only "7 CFR 273.24"
and an unattached FNS memorandum (Jan-2010, May-2011, and the Mar-2012 "Silbermann memo"). This is the
KS/MS finding reproduced with the vocabulary channel isolated: **the criterion field is tracking the
letter's wording, not the mechanism**, and the two states differ only in wording. OH's three agents
each declined to infer the rule from the referenced-but-absent memo, which is the right call and
leaves three documents with no criterion at all.

**8. Doc-class failures reach twenty.** Six more `*-abawd-response-*` files are not FNS responses:
VA FY2011/12/13 and OH FY2011/12/13, all state-authored letters TO FNS with no serial and no FNS
action. As with MD/MI and TN, the FNS side of those state-years is simply absent from the archive.

**9. The cross-group carrying-set shape reproduces in a third state — and in OH it is structural, not
incidental. → D-27.** OH FY2006 and FY2006-a print EDR tables that include counties labelled
**"currently waived"** — covered by a prior, separate action, not adjudicated here — whose labor-force
and unemployment numbers **feed the printed regional aggregate that carries the newly-requested
members**. Both agents excluded them from `geographic_units` as case (c) and recorded them in notes,
which is correct under the spec; FY2006's agent corroborated the exclusion arithmetically (25 bundled +
Stark = the document's own stated 26). The consequences are the FL/TN ones, sharper: any threshold
margin recomputed from group membership is wrong for these groups, and `carried_by_group` is true but
the carrying set is unrecoverable from the row. OH FY2006's **Northwest, Southern and Southeast EDR
decided-subsets are also internally non-contiguous** — they connect only through the excluded
already-waived counties, so the splitting rule and the exclusion rule together manufacture a D-11
violation out of a document that is geographically coherent. FL was "four of nine documents"; here it
is how Ohio files.

**10. Soft-criterion denials arrive in the Midwest, in volume, and coded `other`.** `oh-abawd-response-
fy2006-a` denies **11 counties** — Ohio's metros (Franklin/Hamilton/Montgomery/Summit as one group;
Cuyahoga/Geauga/Lake/Medina/Stark as another; Athens and Lorain individually) — on an ARC "distressed"
designation, a regional economic-indicator report, two maps and an MSA-ranking study. The agent coded
`criterion_code = other` for all eleven. That is the MD/FL pattern (the soft route is the road to
denial) in a fourth region, and it is 11 of OH's 14 rejected rows. But note the coding: OH FY2023
denies Belmont, Lorain and Meigs under `percent_20`. **One state's own series codes the criterion of a
denied group two different ways** — the denial's *requested* basis in FY2023, the *dispositive* basis
in FY2006-a. Direct evidence for **D-16**, within a single state.

**11. `pct10_statutory` can be filed jointly.** VA FY2000 evaluates **Henry County + City of
Martinsville on one combined 6-month rate of 12.85%**, never printing an individual rate for either,
and the letter reasons explicitly from the combination ("a combined 6-month average unemployment rate
for the City and County is still over 10 percent"). The agent coded `pct10_statutory` /
`joint_aggregate`, overriding the spec's "per_unit by the nature of the rule" default and documenting
why. The data is also non-conforming twice over: a 6-month window, from the Virginia Employment
Commission and a state website rather than BLS. The county/independent-city pair is the natural unit
here, which is a Virginia-specific fact `2224` should expect.

**12. D-12 again, both directions.** VA FY2000 drops six counties from the prior waiver (Bath,
Highland, Nottoway, Pittsylvania, Washington, Wythe) and its agent emitted six `withdrawn_by_state`
groups with `criterion_code` null; VA FY2015-a emits two more (Covington City, Lexington City, the
state having said it was "unlikely to adopt the waiver" for them). Eight rows in VA. Against that,
VA FY1998 drops Allegheny/Alleghany, Page and Covington City and its agent emitted **no group** —
notes only. Same state, same event, both encodings, thirteen years apart.

**13. The registry's Tier 3 wart for Ohio never materialised, and Virginia's did so benignly.**
OH is Tier 3 because it has "71 LAUS cities against 88 counties." Across 19 documents and 477 unit-rows
Ohio **never once names a sub-county area** — `area_type` is county on 472 rows and statewide on 5,
`non_standard_geography` is true on zero. Virginia's wart is real but harmless: 142 city rows, all of
them independent cities, i.e. county equivalents with their own LAUS series, and again zero
non-standard geography. Both states cost far less than their tier implied. The LAUS-cities-vs-counties
heuristic in `2226a` predicts *exposure*, not *incidence*, and for these two it over-predicted; ID and
the town-level New England states are where the tier ordering still has to prove itself.

**14. `fiscal_year` resolved on both period-named files, and two agents noticed why that is odd.**
`va-abawd-approval-5.2018-4.2019` and `oh-abawd-approval-10.2017-9.2018` both resolve (D-03 stopgap
holding, trailing-year rule). But the VA file covers **May 2018 – April 2019**, i.e. 5 months of FY2018
and 7 of FY2019, and the trailing-year rule assigns it wholly to FY2019 — defensible, arbitrary, and
exactly the lossiness D-04 is about. Separately, **both agents reported that `2220c` has no
`fiscal_year` field at all**: FY is derived from the filename by `_fy_from_name`, never extracted. That
is worth stating plainly in the spec, because two independent agents spent effort looking for a field
that does not exist and one considered adding it (which `additionalProperties: false` would have
rejected at collate time).

**Blinding — the one failure in this run was mine, and it is instructive.** All 39 returned compliance
lines. **Six VA agents disclosed running `ls`/`find` under `1022_extractions/`** and thereby seeing
sibling *filenames* (always other states' — `al-abawd-response-*`), in every case after their
extraction judgment was formed. **Zero OH agents disclosed anything.**

The cause is not the blinding language, which was identical to the FL and TN runs that returned zero
disclosures. **I gave the five pre-2005 VA agents a batch directory that does not exist**
(`FY1998-2004`; the corpus uses `FY1997-1999` and `FY2000-2004`), so the assigned READ path was wrong
and the only way to complete the task was to go looking — which is precisely the forbidden operation.
Three of those agents then wrote correctly-formed JSON into a `FY1998-2004` directory the worklist
never uses (`fy2000`, `fy2001`, `fy2004`); the files were moved to `FY2000-2004` and re-collated, and
no document was extracted twice or overwritten. The OH batch was dispatched with every path copied
from the worklist output and with the no-listing sentence moved into the write step plus an explicit
"do not verify the directory first; just write" — and 19 of 19 complied silently.

**The operational rule this earns: every path in a fan-out prompt must be copied from the `worklist`
output, never reconstructed.** A wrong path does not merely fail — it converts the blinding rule into
an instruction the agent cannot satisfy, and a well-behaved agent will break blinding to finish the
job. The `worklist` command prints the exact READ and WRITE paths for this reason; the failure here
was reading a truncated worklist and inferring the rest.

**Per-document items to verify against the source PDFs.** Highest value first: **OH FY2008's aggregate
5.7 against its own 4.8 national rate** (the 20%-rule claim the arithmetic refutes on 88 counties — the
single largest such case in the corpus); **OH FY2007's Northern EDR sub-region, 5.7 vs a printed 5.8
threshold, approved** (and all four members newly added that year); **OH FY2006/FY2006-a's
"currently waived" columns** (confirm the aggregates are computed over the union, not the decided
subset — this determines whether every FY2006/FY2007 OH margin above is comparable to the rest of the
arm); **VA FY2000's Henry/Martinsville 12.85% combined 6-month rate** from Virginia Employment
Commission data (nonstandard window and non-BLS source on a `pct10_statutory` group); **VA FY2005's
"20% Threshold" column printing 7.1 where the combined rate is also 7.1**, with no per-county rates
anywhere (49 units, `qualifying_basis` unknown throughout); **VA FY2004's Giles County at 6.3 against
5.3 × 1.2 = 6.36** (approved on a rate that misses by 0.06); **VA FY2015-a's Richmond County printed at
exactly 8.1 against an 8.1 threshold** while the narrative says "exceeding"; **VA FY2006's third group**
(19 counties/cities approved with no criterion and no rate at all — a two-month administrative bridge
so staff could retrain, the second instance of D-19's no-criterion extension); **VA FY2006's
Williamsburg labor force printed as 113,008** for a city of ~12,000 (almost certainly a labor-market-
area figure, kept verbatim); **OH FY2006-b's "Definace" and "Mahonig"** and **OH FY2007's "Definace"**
and prose "Lorian", **OH `approval-10.2017-9.2018`'s "Perrv"**, **OH FY2017's "Ottowa"**, and
**OH FY2016's badly garbled text layer** (the agent transcribed from the rendered images instead and
reported all 18 names clean — worth one spot check, since it is the only document in the run where the
text layer and the image disagree systematically); **VA FY2023's tables dated "extracted from bls.gov
on April 18, 2022"** against a Nov-2022 window end and an April-2023 request (stale boilerplate);
**OH FY2004/FY2005's field 18**, whose printed label ("transmittal of response to national office")
contradicts the cover letter's account of what the date means, and whose FY2005 value (May 2) predates
the state request it answers; and **VA FY2004's cover memo dating the state request March 29** where
field 17 says March 16 and field 18 says March 29.

**New decisions opened: D-26** (`city` vs `independent city`, item 5) and **D-27** (cross-group
carrying sets, item 9 — recommended in the FL run, corroborated in TN, and structural in OH). The run
also adds evidence to **D-04** (item 14), **D-07** (item 7), **D-10/D-25** (VA FY2005 and OH FY2006-b
print no per-unit rates at all, so 63 OH and 70 VA rows carry `qualifying_basis = unknown`),
**D-11** (item 4, largest instance), **D-12** (item 12, both directions in one state), **D-15**
(item 6, sharpest instance), **D-16** (item 10, within one state), **D-19** (VA FY2006's
no-criterion bridge group) and **D-21** (item 3 — a *de facto* statewide grant filed as an all-county
`joint_aggregate`). Items 1, 2 and 3 are analysis findings and belong with the paper's bundling
exhibit; item 2 in particular is a mechanism the exhibit does not yet have.

### WA extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-20)

One Tier 3 state, the reservation-and-LAUS-heavy one: **WA 35 PDFs, ~153 pages, FY1998–FY2025** —
the longest continuous FNA record in the corpus so far and the largest single-state document count
yet extracted. Run under the unchanged v1_5 spec, so WA joins the existing arm — same `run_id`, same
`1022_extractions/claude_v1_5_adjud` root. One blinded sonnet subagent per PDF, dispatched 12 up
front and then backfilled one-for-one as slots freed; no document extracted twice.

**35/35 schema-valid.** 369 groups, 846 unit-rows. Flat CSV (gitignored):
`1022_extractions/wa_extractions_v1_5_flat.csv`, 846 rows x 78 cols.

| | docs | groups | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|---|---|
| WA | 35 | 369 | 846 | percent_20 533, LSA 151, percent_10 83, other 51, null 24, EUB 4 | approved 798, null 38, rejected 10 | joint_aggregate 485, per_unit 340, unknown 12, statewide 9 |

`qualifying_basis`: own_rate 289, unknown 272, own_designation 124, carried_by_group 113, null 39,
statewide 9. `document_type`: `fns_response_only` 808 rows / 32 docs, `state_request_only` 38 rows /
3 docs. `area_type`: county 624, **reservation area 146**, city 31, **census tract 25**, statewide 9,
balance of county 7, **administrative service area (Community Service Office) 4**. Serials run
**970032 / 970063 / 970153 / 970163 / 970164** (FY1998–FY2002, five concurrent series), then
**2030027** (FY2003–FY2009), then **2150021 → 2150022** (FY2016→); FY2011 carries only the document
control code `SNAP-10-6-WA-Waivers` and **six documents (FY2012, FY2013, FY2021-b, FY2022, FY2023,
FY2024, FY2025) print no serial at all** — the post-2020 FNS form dropped the field.
`possible_double_counting` is true on 110 rows, concentrated in the FY1998/FY2002 multi-serial filings.
**WA has no gold sheet, so nothing here is scored.**

**1. King County is excluded from every county bundle in the entire record, and Snohomish is the
swing member.** Taking the thirteen `joint_aggregate` county groups FY2007→FY2025, the union of all
counties ever bundled is **38, not 39** — King never appears once, in nineteen years:

| bundle size | documents | excluded |
|---|---|---|
| 38 | FY2017, FY2018, FY2019, FY2020, FY2021-a, FY2024, FY2025 | King only |
| 37 | FY2008, FY2009, FY2017-a, FY2023 | King, Snohomish |
| 36 | FY2016-a | King, Snohomish, Pierce |
| 35 | FY2007 | King, Whatcom, Whitman, San Juan |

This is a different construction from every state recorded so far. KS redraws annually, MI/TN remove
the metros, OH truncates official planning regions, VA carries one big mislabelled region. WA does
none of these: it takes **the whole state minus Seattle**, and trims the next-tightest labor markets
(Snohomish, then Pierce) only when the arithmetic needs them. The choice variable is the exclusion
set, not the inclusion set, and it is a nested sequence — exactly what a state solving for the
threshold from the top down would produce.

**2. The bundles hug the threshold, and the aggregate/individual contrast holds.** Computing
`local_rate − 1.2 × national_rate` over approved `percent_20` groups where both rates print
numerically:

| level | n groups | min | median | max | within ±0.11 |
|---|---|---|---|---|---|
| joint_aggregate | 13 | −0.06 | **+0.064** | +0.42 | **8 of 13** |
| per_unit | 15 | +0.02 | +1.16 | +4.80 | 2 of 15 |

Eight of thirteen on the line, spanning FY2007 → FY2025 and three serial series; the per_unit grants
show the usual dispersion (median +1.16, an order of magnitude looser). Tightest: FY2021-a (−0.020),
FY2023 (−0.020), FY2008 (−0.060), FY2009 (−0.040), FY2016-a (−0.040), FY2007 (+0.040). This is
weaker than VA's 14-of-14 but covers a longer span, and it is the **eighteenth** state in which the
threshold-hugging regularity holds.

**Sign note.** Unlike VA, WA's margins are not systematically ≤ 0 — five of thirteen are negative,
eight positive. The two loosest (FY2020 +0.42, FY2025 +0.26) are the years where the bundle is
already the full 38 and cannot be trimmed further, which is consistent with the mechanism in item 1:
when the exclusion set is exhausted the state stops being able to fine-tune and the margin drifts up.

**3. Sub-county units below the city level — census tracts and welfare-office catchments — appear
here and nowhere else in the corpus.** WA FY1998-b (serial 970163) waives **25 individually numbered
King County census tracts** (80–82, 84, 99, 111, 85–95, 101, 103, 107–110, 112, 265). The state had
asked FNS to waive whole **Community Service Offices** — Rainier, Belltown, West Seattle, and
"65.5% of Capitol Hill" — and **FNS refused, granting tract-specific coverage instead** (4 of the
run's 10 denials). This is a unit type the geography pipeline has no representation for: the
`area_type` vocabulary absorbed them as `census tract` (25 rows) and
`administrative service area (Community Service Office)` (4 rows), both free-text inventions by the
agents. `2224` cannot join these to any county-equivalent, and they are not
`non_standard_geography` in the reservation sense — they are *sub*-county administrative geography.
**Opens D-28.** Note this also means King County, excluded wholesale from every bundle FY2007→FY2025
(item 1), is the one county whose waiver coverage in the early record is tract-level.

**4. Reservations are adjudicated one at a time, with four different criteria, for five years.**
Serial 970153 runs FY1999→FY2002 as a reservation-only track: FY1999-b 27 groups, FY2000-b 25,
FY2001 25, FY2002-b 28 — each reservation its own group, each with its own basis. FY2002-b's mix is
LSA 13, percent_10 9, percent_20 4, other 2. The `other` groups are **BIA employment-to-population
ratios** (Puyallup 22.03%, Sauk-Suiattle 30.35%, against an FNS cutoff around 50%), a soft criterion
that appears in 53 rows and is the basis on which Tulalip is **denied three separate times**
(FY1999-b, FY1999-c, FY2001) and Suquamish once (FY2000-b). Two agents independently flagged
`non_bls_source = true` on these, citing FNS's own statement that it requires BLS or BLS-methodology
data — the FY1999-c denial turns explicitly on the state having submitted "Tribal Data Resources"
figures. By FY2005 the whole track is gone: the statewide grant "includes all recognized American
Indian reservations," and from FY2016 on only **Muckleshoot** (and sometimes Tulalip) is filed
individually, on ACS-share-of-county-BLS estimates. That is a clean within-state transition from
per-reservation adjudication → blanket inclusion → single-reservation exception, over 25 years.

**5. D-15 and D-07 get another data point, and WA sides with VA against OH.** FY2011
(`SNAP-10-6-WA-Waivers`) is the EB-trigger letter; its agent coded `criterion_code = eb_trigger` and
`group_action = approved`. FY2016-b, FY2021-b and FY2022 do the same on the standard form (DOL
trigger notices 2013-49, 2020-21, 2020-7). That is VA's encoding, not OH's — but see item 6 for the
opposite call inside the same state.

**6. FY2012 and FY2013 are state-authored "we will continue the suspension" letters, and both agents
coded them all-null.** Two near-identical one-page WA DSHS letters to the FNS Western Region
Director, no serial, no citation, no data, no named area, saying the state "will continue the
suspension of time limits on ABAWD SNAP recipients through at least September 30, 201X." Both agents
independently coded `criterion_code = null`, `group_action = null`, `document_type =
state_request_only`, and both explicitly declined `federal_suspension` on the grounds that FY2012/13
falls outside both the ARRA and FFCRA windows. **So WA codes the DOL-trigger letters `eb_trigger` and
the suspension-continuation letters `null` — internally coherent, and the reasoning is written out in
both records.** The value here is that the two shapes sit in one state one year apart, which isolates
what the field is actually tracking: the presence of a cited authority, not the presence of a waiver.

**7. FY2020 is a partial approval driven by a regulation change, and FY2021-a by that regulation's
vacatur.** The Dec-2019 letter grants **3 months of a 12-month request** (2020-01-01→2020-03-31),
cut off at the effective date of the revised 7 CFR 273.24(f) standards — not on any area test, and
FNS says so. FY2021-a (Jan-2021) then approves a full year but conditions expiry on "or the date at
which new waiver standards become effective, whichever occurs earlier," the 2019 rule having been
vacated 2020-10-18. Neither is an area-level denial, and a `2224` that reads short windows as
tightening will misread both. This is the cleanest instance in the corpus of the **rule change itself
showing up as a truncated waiver period**.

**8. A near-complete state application survives, and its FNS answer sits beside it.** FY1998-a is
`state_request_only` — the WA DSHS filing, 36 groups, all `group_action = null` (38 of the run's
null-action rows). It layers **Section B (LSA)** and **Section C (20%-rule / employment-ratio)**
claims over the *same* Benton, Walla Walla and Kitsap units deliberately, giving the run its
`possible_double_counting = true` concentration. FY1999 is FNS's response to it: 31 groups, and FNS
**de-duplicates the layering by hand** — folding Walla Walla City's LSA designation into the
Walla Walla County 20%-rule group, treating Benton as one whole-county request. Kitsap is denied on
employment-to-population grounds with a rate FNS notes came "from the State website," not BLS. Having
request and response as separate documents in one state is rare in this corpus and makes the
state's *ask* separable from FNS's *grant* — worth knowing for any bundling exhibit that wants to
measure how much of the constructed set is state-chosen versus FNS-permitted.

**9. `waiver_serial_number` is a list in five documents, and the schema allows it.** FY1998-a,
FY1998-c, FY1999, FY2000-a and FY2002-a each carry 3–4 concurrent serials in one letter
(`["970032","970063","970164"]`, and FY1998-c adds 970153). `2220c` types the field as
`["string","array","null"]` by design, so this is conforming — but a naive flat-CSV build silently
drops every list-valued cell, which is exactly what happened on the first pass here (317 rows read as
null serial until the builder was fixed to join on `|`). **`2224` must handle both shapes**; the same
trap applies to any per-serial panel key.

**Transcription and document-defect notes.** Both FY1999-b and FY2000-b print an expiration of
**"April 31, 2000" / "April 31, 2001"** — not a calendar date; both agents preserved it verbatim
rather than repairing. FY1999 prints "expires 3/3/2000" in a table footer against "March 31, 2000"
in the prose, and FY1998-c prints "expires 3/3/99" against "March 31, 1999" — the same defect twice,
four years apart. FY1998-b cites the "**Balanced Budget Act of 1977**" twice and "1997" once.
FY2018's serial is 2150022 in field 1 but **2150021 in the page 3–4 header**. FY2022 is labelled
"Initial" while its own cover letter says it "replaces Washington's current Statewide ABAWD waiver,"
and its granted window (2022-02-01→2023-01-31) does not match the requested one
(2022-02-28→2023-03-01). FY2008 says "35 counties and 2 cities" over a list of 37 counties and zero
cities. FY2002-b's Quinault footnote says "Only Stevens is a designated LSA" when Quinault's parent
counties are Grays Harbor and Jefferson. Recurring OCR/typo spellings normalised against the
geography reference with `orig_text` preserved: "Pende Oreille" → Pend Oreille (twice), "Clallum" →
Clallam, "Whakiakum"/"Wakiakum" → Wahkiakum, "Tualip" → Tulalip, "Kalispell" → Kalispel, "Definace"-
class garbles absent here. **"Suquamish" was left as printed by three separate agents** — the
geography reference lists that tribe's land as *Port Madison Reservation*, and the never-force-a-match
rule correctly stopped all three from substituting it; FY1998-d preserves the document's own
"Suquarmish" typo.

**Blinding.** 34 of 35 agents confirmed clean compliance. **Two self-reported an incidental
infraction**: the FY2005 and FY1998-c agents each ran `ls` on their output directory before writing
and thereby saw *filenames* of other states' extraction JSONs in the arm. Neither opened any file,
and both disclosed it unprompted rather than claiming clean compliance. The prompts issued after the
first report carried an explicit "the output directory already exists — do NOT `ls` it" line, and no
later agent tripped it. Judgement: **non-consequential** — a filename carries no extraction content —
but it is the second mechanism (after the v1_3 gold-sheet reads) by which an agent can touch the
arm's own output, and the fix is one line in the task prompt, so it should be standing text in the
protocol rather than a per-run patch.

**New decision opened: D-28** (sub-county census tracts and welfare-office catchments as waiver
units, item 3). The run also adds evidence to **D-07** and **D-15** (items 5 and 6, both directions
inside one state), **D-10/D-25** (272 of 846 rows carry `qualifying_basis = unknown`, almost all from
bundles that print a combined rate and no per-county rates), **D-19** (FY2020's regulation-driven
3-month grant), and **D-21** (WA's bundles are *de facto* statewide-minus-King and will not be found
by filtering on `qualification_level == statewide`). Items 1, 2 and 7 are analysis findings and
belong with the paper's bundling exhibit; item 1 in particular is a construction the exhibit does not
yet have.

### TX extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-25)

One Tier 3 state, the largest-county-list one: **TX 16 PDFs, 68 pages, FY1998-FY2014**. Run under
the unchanged v1_5 spec, so TX joins the existing arm — same `run_id`, same
`1022_extractions/claude_v1_5_adjud` root. One blinded sonnet subagent per PDF, dispatched 8 up
front and 8 immediately after; no document extracted twice.

**16/16 schema-valid.** 264 groups, 264 unit-rows. Flat CSV (gitignored):
`1022_extractions/tx_extractions_v1_5_flat.csv`, 264 rows x 66 cols.

| | docs | groups | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|---|---|
| TX | 16 | 264 | 264 | percent_10 243, LSA 19, percent_20 2 | approved 264 | per_unit 264 |

`qualifying_basis`: own_rate 245, own_designation 19. `document_type`: `fns_response_only` 194 rows
/ 12 docs, `full_application` 70 rows / 4 docs. `area_type`: **county 264 — the only single-valued
`area_type` distribution in the corpus.** `type_of_request`: Extension 166, Extension and
Modification 98. Serial **970057 runs unbroken FY1998 -> FY2014**, joined for one year each by
**990002** (FY1999) and **990067** (FY2000, both documents). `possible_double_counting` is false on
every row; `soft_criterion_invoked` false on every row; `non_standard_geography` false on every row.
**TX has no gold sheet, so nothing here is scored.**

**1. Texas never bundles. Not once, in seventeen years.** Every one of the 264 groups is
`per_unit`; there is not a single `joint_aggregate` or `statewide` group in the entire record. This
is the first state in the corpus with **zero** aggregate groups, and it means the threshold-hugging
regularity that has now held in eighteen states **cannot be tested here at all** — there is no
constructed bundle whose combined rate could sit on the line. The mechanism is criterion mix rather
than state preference: 243 of 264 rows are `pct10_statutory`, a rule that is per-area by
construction (each county's own rate against a fixed 10%, with no arithmetic that aggregation could
help), so Texas has nothing to solve for. Where other states choose an inclusion set, Texas is
handed a pass/fail test county by county.

> **Correction (2026-08-25, NV run).** The claim that `pct10_statutory` is "per-area by
> construction... with no arithmetic that aggregation could help" is **true of Texas but false in
> general.** Nevada builds joint aggregates under the 10% rule three times (FY2000, FY2001, FY2004),
> twice with members that fail the threshold alone and are carried by the combined rate. Read the
> paragraph above as a statement about the Texas record, not about the rule.

The corollary is that the margin distribution here is a *selection* margin, not a *construction*
margin — what the state chose to request, not what it assembled. It is correspondingly loose:
across 172 approved `percent_10` rows with a numeric rate, median margin over threshold is
**+1.70 points**, with 35 rows within +0.5 and 57 within +1.0. Compare WA's constructed bundles at
a median of +0.064 with 8 of 13 inside ±0.11. Two orders of magnitude, and it is the right
comparison to make: it is roughly what the per_unit arms look like elsewhere (WA per_unit median
+1.16), which is evidence that the tight bundling margins really are an artefact of construction.

**2. The county count tracks the national cycle, and the composition is a stable core plus a
cyclical fringe.** Counties waived per year: 26 (FY1998), 19, 30+20 (FY2000, two documents), 10,
14, 17, 17, 13, 5, 5, **4 (FY2008)**, 22, 27, 23, 12. The trough is FY2006-FY2008 at 5/5/4 — the
pre-recession labor-market peak — and the recovery to 22/27/23 in FY2011-FY2013 is the recession.
**52 distinct counties appear across the record**, but the core is small and permanent:
**Maverick, Starr and Zavala appear in all 16 documents**, Presidio in 15, Willacy 14, Hidalgo and
Newton 13. These are the border and deep-East-Texas counties whose rates never recover. The FY2008
floor is exactly **Loving, Maverick, Starr, Zavala** — three of the four permanent members.

**3. When a county's own rate falls short, Texas moves it to a second serial rather than dropping
it.** FY1999 opens waiver **990002** for Val Verde alone, whose rate was under 10%, and qualifies it
on its DOL Labor Surplus Area designation. FY2000 systematises this: serial **990067** carries the
four counties (Cameron, Jim Hogg, Jim Wells, Winkler) that missed the 10% cut in FY2000-b, plus
El Paso (LSA) and **Hockley and Lamb on the 20%-above-national test** in FY2000-a — the only two
`percent_20` rows in the entire state record. So the LSA and 20% criteria are used here purely as a
**fallback channel for counties that fail the statutory rate**, administratively segregated onto
their own serial number. That is a different use of LSA from the states that treat it as a primary
basis, and it makes the serial number itself informative about why a county qualified.

**4. FY2005 is the one year FNS re-bases the criterion wholesale.** Texas applied for 13 counties
under the >10% rationale; FNS's field 9 explicitly re-grounds the approval on each county's LSA
designation ("designation provides an automatic exemption... all 13 counties are readily
approvable"), and prints no rates at all. The agent coded all 13 as `lsa` on the ground that FNS's
stated basis controls, recording the state's rate rationale in `criteria_summary_text`. This is
worth flagging because it is **the entire LSA mass of the state outside the FY1999/FY2000 fallback
serials** — 13 of 19 LSA rows come from this single document — so any analysis that reads criterion
mix as a state-level behavioural choice will misread FY2005, where the criterion is FNS's choice,
not Texas's.

**5. Three findings opened as decisions.** All are TX-first observations:
- **D-29** — TX FY2000-b approves on the **higher of a 12- and a 6-month average**, and the schema
  stores only one window. Culberson (12-mo 9.8 / 6-mo 10.7) and Kinney (12-mo **8.0** / 6-mo 10.3)
  are approved `percent_10` units whose stored rate *fails* the test they were approved under. A
  downstream assertion that approved `percent_10` implies rate > 10 gets two false positives, and
  the refutation lives only in free text.
- **D-30** — the agents split **5-1** on whether a 12-month window under `pct10_statutory` is a
  `nonstandard_averaging` departure. The minority (FY2012) is the only one that checked
  `002_rules_machine.yaml`, which gives `pct10_statutory` **no fixed-window requirement**; the
  majority reading sets the flag `true` on **129 of 264 rows** for conduct the KB calls conforming.
  Needs a cross-arm sweep, since this construction is not TX-specific.
- **D-31** — TX FY2002 grants four counties **three months instead of twelve** for want of
  documentation supporting a short-window rate, while approving the other ten for the full year.
  A partial denial on the duration margin, invisible to `group_action` (all 14 read `approved`).
  Sibling to WA FY1998-b's refusal on the *geographic* margin, and coded inconsistently with it.

**6. Document-quality note: five separate transcription errors in the source forms, all caught and
none silently corrected.** FY1999 prints serial "970075" for 970057; FY2000-b's field 9 names
**Yoakum** among the approvals where the request list, the rate table and the cover letter all say
**Winkler** (resolved to Winkler on three independent pieces of evidence, erroneous text still
transcribed verbatim); FY2002's letter mis-types the serial as "97005" and strikes Sabine from the
wrong batch; FY2003 carries two mutually inconsistent date pairs; FY2011's field 8 says "4 counties
listed in the table below" above a table of 22. In every case the agent flagged the discrepancy in
`request_level.notes` rather than reconciling it away — the FY2004 Liberty County case is the
cleanest illustration, where the state computed 10.3% and FNS recomputed 10.4%, both printed, both
clearing, and both preserved.

**Blinding.** All 16 agents confirmed compliance. Two disclosed an edge case: `ls` of the output
directory surfaced other documents' JSON **filenames** (not contents) while confirming the write
path. Filenames carry no extraction content and neither agent opened a file, so no re-run was
ordered — but the worklist step already creates these directories, so the task prompt should say so
and remove the reason to list them.

### NV extraction (arm `fe5d1b3c`, sonnet-5, 2026-08-25)

One Tier 3 state, the most tribal-geography-heavy in the corpus: **NV 28 PDFs, 108 pages,
FY1998-FY2026**. Run under the unchanged v1_5 spec, so NV joins the existing arm — same `run_id`,
same `1022_extractions/claude_v1_5_adjud` root. One blinded sonnet subagent per PDF, 14 dispatched
up front and 14 immediately after (one of the second batch bounced off the 20-agent concurrency cap
and was re-dispatched); no document extracted twice.

**28/28 schema-valid.** 257 groups, 300 unit-rows. Flat CSV (gitignored):
`1022_extractions/nv_extractions_v1_5_flat.csv`, 301 rows x 66 cols (the extra row is FY2011, a
zero-group non-conforming document). The arm now holds **649 documents across 34 states**.

| | docs | groups | unit-rows | criterion mix | `group_action` | `qualification_level` |
|---|---|---|---|---|---|---|
| NV | 28 | 257 | 300 | percent_10 142, percent_20 75, LSA 49, EUB 7, other 2, null 26 | approved 294, withdrawn_by_state 4, rejected 2 | per_unit 229, unknown 28, joint_aggregate 26, statewide 13 |

`document_type`: `fns_response_only` 298 rows / 25 docs, `other_nonstandard` 2, `state_request_only` 1.
`geographic_unit_qualifying_basis`: own_rate 182, unknown 52, own_designation 49, statewide 12,
carried_by_group 3. **`non_standard_geography` is true on 209 of 300 rows — 70%, by far the highest
in the corpus** (TX was 0%). Serials run 970120/970184/970185 (FY1998-FY2003, plus 970121 in FY1998),
consolidated into **2040058** from FY2004, then 2080023, 2090003, 2002014, and **2150026**
(FY2015-FY2020); FY2021 onward print no serial at all. **NV has no gold sheet, so nothing here is
scored.**

**1. Nevada is a tribal-areas program with a county program attached.** 208 of 300 unit-rows are
reservations, colonies or tribal communities; only 67 are counties and 9 cities. No other state in
the corpus looks like this. The consequence runs through everything below: tribal areas have no BLS
series of their own, so nearly every rate in the NV record is **constructed by apportioning
whole-county BLS unemployment to the tribal area by its Census population share**. `non_bls_source`
is true on 53 rows and `older_vintage` on 14 (FY2004 admits it was still using **1990** Census
shares). The method breaks down at small denominators in both directions: **Goshute Reservation
prints 100.00% unemployment twice** — 55 of 55 in FY2006-a, 111 of 111 in FY2007, two different
vintages, same degenerate result — and the Storey County portion of Pyramid Lake was **denied in
FY2001 because its share ratio was 0**, i.e. no labor force at all. Any rate-based analysis has to
handle NV tribal units explicitly; the 90-point right tail of the `percent_10` margin distribution
is an artefact of this apportionment, not a labor-market fact.

**2. `pct10_statutory` DOES produce constructed bundles — three times — which refutes the TX
generalization.** The TX section concluded that the 10% rule is "per-area by construction, with no
arithmetic that aggregation could help." That is a Texas fact, not a general one. Nevada builds
joint aggregates under it in FY2000, FY2001 and FY2004, and in two of them the arithmetic is
visible and load-bearing:
- **FY2001**, "Washoe Tribe of Nevada and California": Washoe Reservation 6.5%, Carson Colony 9.0%,
  Dresslerville Colony 17.4%, approved on a combined **11.1%** printed as 26/234. **Two of three
  fail the 10% test alone.**
- **FY2004**, "Washoe Reservation": combined **12.9%**, from which the table lets you back out Carson
  Colony ~18.2% (clears alone) and Stewart Colony ~4.7% (fails alone, coded `carried_by_group`).
- **FY2000**, the same Washoe/Carson/Dresslerville set at a combined **12.45%**, no per-member rates
  printed.
So the bundle exists *because* members cannot clear individually. Downstream logic that assumes
approved `percent_10` implies own-rate > 10 gets three false positives here, on top of the two D-29
already documents in TX.

**3. The bundling margins are tight, and one bundle sits exactly on the line.** FY2020-a's
**"Combined Area 1"** bundles 15 counties + Carson City — 16 units — under `pct20_above_natl` at a
combined **4.8%** against a national 4.0%, i.e. a threshold of **exactly 4.8%. Margin 0.000.** No
per-county rates are printed, so the aggregate is the only thing doing the work and no member can
be identified as load-bearing (the agent correctly set all 16 to `qualifying_basis: unknown` rather
than `carried_by_group`). The 2018 statewide approval is the same story to two decimals: state rate
5.9% against 4.9% x 1.2 = 5.88%. Set against the three `percent_10` bundles at +2.45, +1.10 and
+2.90 over threshold, and against per-unit selection margins whose median is +5.70 (`percent_10`,
n=70) and +2.92 (`percent_20`, n=41), the pattern is the one WA showed and TX could not test:
**constructed sets cluster on the threshold, selected sets do not.** n=4 bundles is small, so this
is corroboration, not proof.

**4. Non-standard averaging is Nevada's house style, and FNS states the norm out loud — twice.**
`nonstandard_averaging` is true on 68 rows. NV uses 12-month calendar-year windows (FY2002-b,
FY2003, FY2026), a 36-month window (FY2007's 20%-rule set, FY2016-c's statewide), and standard
24-month windows elsewhere — sometimes **two different windows in the same document** (FY2007).
Two documents carry FNS commentary on the window, and **only one of them bears on D-30** — the
distinction matters, because D-30 is specifically about `pct10_statutory`:
- **FY2002-b — on point.** The 16 tribal groups qualify under serial 970184 (`pct10_statutory`) on a
  12-month CY2001 average. FNS accepts it *this once* and explicitly flags it for correction going
  forward. That is the agency treating a short window as a departure **under the very rule the KB
  says carries no fixed-window requirement.**
- **FY2005 — off point, despite appearances.** FNS rejects the state's single-calendar-year national
  average as a nonconforming "12-month guidepost" and substitutes a 24-month calculation. But that
  test is `pct20_above_natl`, where the 24-month procedure is uncontested and the KB already
  attaches it. It is evidence that FNS polices windows; it says nothing about the 10% rule.
So NV supplies **one** genuine counter-example to D-30's recommended ruling, not two. It is real
counter-evidence — the register currently recommends amending `2220b` to declare 12-month windows
conforming under `pct10_statutory` and re-coding the flag to `false`, and FY2002-b is FNS itself
declining to treat that construction as routinely acceptable. NV's other 12-month `pct10` documents
(FY2003, FY2004, FY2026, 36 further groups) carry no comparable FNS remark either way.
**Recommendation: do not rule D-30 on the TX split alone.** Either reading now has agency text
behind it, and the cheap resolution — flag `true` but rename the field descriptive rather than
nonconformant, the register's option (2) — no longer looks like a compromise so much as the honest
answer.

**5. Two new decisions, both NV-first.**
- **D-32 — LSA qualification by residency has no schema slot.** FY2003 adds three reservations
  (Fallon Paiute-Shoshone, Yerington, Yomba) to the LSA serial *because they sit inside LSA-designated
  counties*, not because they hold designations; FY2005 approves Las Vegas Colony the same way,
  explicitly noting its own rate fails the 10% test. Four instances, two documents, two agents — both
  reached for `own_designation` as the closest fit and both flagged in-field that it is wrong. The
  `qualifying_basis` enum needs a `derivative_designation` value (sibling to `carried_by_group`,
  which covers the arithmetic case but not the residency case).
- **D-33 — `area_type` is free text and NV fragments it six ways.** The schema documents a suggested
  vocabulary in the field description but does not enum it. NV's 208 tribal rows are split across
  `reservation area` (165), `colony` (23), `reservation` (11), `tribal colony` (7), `tribal community`
  (1) and `community` (1). Harmless per-document, but it makes `area_type` unusable as a grouping key
  across the corpus without a normalization pass. Cheapest fix is a controlled vocabulary in `2220c`.

**6. FY2011-FY2013 are not waiver decisions, and the corpus should say so.** Three consecutive
"response" files are nothing of the kind: **FY2011** is a two-message Feb-2010 email chain in which
FNS says states may confirm intent by email and NV replies that it will (0 groups,
`non_conforming_document: true`); **FY2012** is page 5 of Nevada's ABAWD E&T state plan asserting an
already-effective statewide EB exemption; **FY2013** is a one-page state letter electing the
automatic waiver USDA offered 46 states. Only FY2013 carries a decision-like fact, and it is the
state's election, not an FNS action. These are corpus-coverage gaps wearing response-file names —
NV's FY2010 and FY2014-FY2015 are absent outright — and any panel built off `waiver_effective_date`
will read FY2011-FY2013 as covered on very thin evidence.

**7. Two data-integrity items found at collation, neither an agent error worth re-running.**
- **FY2005 stores a threshold in `national_unemployment_rate_cited`.** The document prints a
  "national target rate of 6.90%" — already the 20%-above figure — and the agent recorded 6.90 in the
  national-rate field. Every other document stores the true national rate (3.6%-5.3%, plus 6.7% in
  FY2016). Left as-is it silently double-applies the 1.2 multiplier and makes three approved units
  (Fallon 7.7, Ely 7.7, Yomba 7.8) look sub-threshold. **This one field needs a manual correction.**
- **FY2024 may be a truncated download.** The Waiver Response form skips item 7 to item 9 and page
  footers read "Page 2 of 4" / "Page 3 of 4" on a 3-page PDF. Worth re-fetching from the FNA site
  before the panel build.

**8. Document-quality note: NV's forms are noticeably error-prone, and nothing was silently fixed.**
FY2002-b's field 8 says "seven (6) counties" and prints an expiration date (2002-03-31) that predates
the letter; FY2005's prose says "three Tribal reservations" above a table of four and credits LSA
designation to BLS rather than DOL; FY2004 lists Ely Reservation twice (the only
`possible_double_counting: true` in the state) and prints a combined-labor-force cell that duplicates
one member's figure; FY2006-a approves Pyramid Lake off a table row for an area absent from the
request list; FY2026's narrative claims a minimum rate of "11.9 percent or greater" above a table
whose minimum is 11.4%; FY2007 records FNS observing that the state's rates had been rounded so they
"end in zero," judged immaterial and approved anyway. In every case the discrepancy was flagged in
`notes` or `criteria_summary_text` rather than reconciled away.

**9. A cross-document inference the blinding necessarily prevented — offered as a candidate
adjudication, not applied.** FY1998 and FY1999 leave `criterion_code` null on the 970120 and 970185
groups (26 rows) because both documents define "insufficient jobs" disjunctively — LSA *or*
20%-above-national — without saying which test each area met. FY2000, FY2002-b and FY2003 each print
the mapping explicitly: **970120 = LSA, 970184 = 10% rule, 970185 = 20%-above-national.** Three
independent blinded agents, three documents, same mapping. Adopting it would fill all 26 nulls. It is
an inference across documents rather than anything FY1998/FY1999 state, so it is Josh's call; the
evidence is recorded here rather than acted on.

**Blinding.** All 28 agents confirmed compliance. Two disclosed the same edge case the TX run saw —
an `ls` of the output directory surfaced other documents' JSON **filenames** while confirming the
write path — and one stated explicitly that its judgments were settled before that call. No contents
were opened, so no re-run was ordered. Note the task prompt *already* carried the TX fix ("the output
directory already exists; do NOT list it") and two agents listed anyway, so the instruction is not
sufficient on its own; the durable fix is for the driver to assert the directory as
confirmed-existing in the worklist output.

## Notes / conventions
- **Adversarial cross-check (later):** Extractor A (OpenAI) emits the same schema;
  `2223_adjudicate_extractions.py` (not yet built) will field-compare A vs B and
  route disagreements to a Claude referee, then to `10222_human_review_queue.csv`.
- **Model tag** is recorded in the ledger (`MODEL_TAG` in `fna_extraction_results.py`);
  bump it when the harness model changes so `run_id` versions cleanly.
- **Scope:** this extractor reads response/decision PDFs, which embed the request
  (geography, serial, rule, data, dates), so extraction works from them alone.
  Application-side zips (`1023_application_docs/`) are a later enrichment.
