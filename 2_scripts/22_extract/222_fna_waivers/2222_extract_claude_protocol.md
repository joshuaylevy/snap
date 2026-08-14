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
| **v1_5** (adjudications, below) | `1022_extractions/claude_v1_5_adjud` | `fe5d1b3c` | `claude-sonnet-5` | v1_5 |

**All JSONs from the arms above were deleted from the working tree (2026-08-12, Josh's
call) so that future extraction agents cannot read a prior arm's output. They remain in
git history — `git log --diff-filter=D --stat -- '1_data/10_raw/102_fna/1022_extractions'`
finds the deletion commit, and `git show <commit>^:<path>` recovers any file. The
gitignored comparison CSVs and the ledger were NOT recoverable and are gone for good;
the ledger rebuilds from `collate`. Gold `.xlsx` untouched.**

Control vs treatment differ ONLY in the `4809aa1` prompt edit (contiguity checked
against the adjacency lists; near-miss names resolved to the reference spelling), so
holding `--model-tag claude-sonnet-5` fixed makes the geography reference the single
moving part. Gold sheets now exist for **WI, ND, DE and IA** (DE/IA hand-collected
2026-08-12); NC still has none and can be compared run-to-run but never scored. A state
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

## Notes / conventions
- **Adversarial cross-check (later):** Extractor A (OpenAI) emits the same schema;
  `2223_adjudicate_extractions.py` (not yet built) will field-compare A vs B and
  route disagreements to a Claude referee, then to `10222_human_review_queue.csv`.
- **Model tag** is recorded in the ledger (`MODEL_TAG` in `fna_extraction_results.py`);
  bump it when the harness model changes so `run_id` versions cleanly.
- **Scope:** this extractor reads response/decision PDFs, which embed the request
  (geography, serial, rule, data, dates), so extraction works from them alone.
  Application-side zips (`1023_application_docs/`) are a later enrichment.
