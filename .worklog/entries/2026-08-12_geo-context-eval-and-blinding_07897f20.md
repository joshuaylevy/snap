---
title: Geo-context extraction arm scored vs WI gold — no unit-level effect; blinding rule added; run histories wiped
date: 2026-08-12
session_id: 07897f20-64ad-4328-86b7-248c0674d9ef
task_slug: geo-context-eval-and-blinding
status: complete
phase: Phase 3
tags: [abawd, fna, extraction, geo-context, evaluation, blinding, prompt-engineering, wi-gold]
branch: master
head_commit: 8a2dbe5
commits: [0a890a2, 75f4a89, 8a2dbe5]
transcript_path: /Users/joshuaylevy/.claude/projects/-Users-joshuaylevy-Documents-Work-USC-snap/07897f20-64ad-4328-86b7-248c0674d9ef.jsonl
---

# Geo-context extraction arm scored vs WI gold — no unit-level effect; blinding rule added; run histories wiped

**Re-read the full session:** `claude --resume 07897f20-64ad-4328-86b7-248c0674d9ef`
(or read the raw transcript at `transcript_path`)

## Context / goal

Next step #2 on the FNA rebuild plan: pilot an extraction round WITH the state
geography context (per-state BLS/Census location names + full in-state county
adjacency, built on `geo_context` last session) and score it against the
hand-collected WI gold, using the pre-geo `01dc7c84` sonnet arm as control.

The question was whether pointing extraction sub-agents at a geography reference
improves extraction — specifically whether adjacency context (a) kills the OCR
name-error class and (b) stabilizes group counts / bundling.

## What was done

1. Ran the **treatment arm** `904ee8fa` (v1_3 spec, `claude-sonnet-5`, root
   `1022_extractions/claude_v1_3_geo`) over all 20 WI response PDFs — one
   `general-purpose` sonnet sub-agent per document, each instructed to read
   `wi_geo_context.md` BEFORE its PDF. Fanned out in two batches of 10.
   Confirmed all 20 PDFs are ≤7 pages first, so no `pages` windowing was needed.
2. **Caught two contaminated agents mid-run** (see Key decisions) and re-ran both
   with an explicit blinding block. 20/20 schema-valid on collate.
3. Scored treatment vs control with `2225` on the cleaned gold (`b4aca656`, 313
   rows), all 18 WI FYs, and totalled the three matching bases programmatically
   rather than by eye.
4. Diffed **group composition** JSON-to-JSON between arms, because `2225` flattens
   `groups[]` away and therefore cannot score bundling — the channel adjacency
   actually drives.
5. Wrote the result up in the protocol, committed the arm (`0a890a2`).
6. On Josh's instruction, made two prompt changes (`75f4a89`, SPEC BUMP) and then
   deleted every extraction arm from the working tree (`8a2dbe5`).
7. Fast-forwarded `geo_context` → `fna_rebuild` → `master`.

## Key decisions & why

**Predicted the null result before running it, and it held.** The control's
`exact`→`canonical` gap in WI was a single unit (`layfayette`, FY2003), so the
name channel had exactly +1 of headroom and criterion/action were already ≥98%.
Result: name 294/298 (98.7%) on `exact` in BOTH arms, action 98.0% both,
criterion 99.5% both. Re-scoring the control reproduced the recorded baseline
exactly, so the harness is consistent.

**The composition moved in offsetting directions — this is the real finding.**
+1 from `layfayette`→`Lafayette` (the one genuine spelling error, fixed; `exact`
now equals `canonical` in WI, no extraction-side spelling residual left), and −1
from `Sokagoan`→`Sokaogon`, where gold stores the document's *verbatim* print
(recorded in the provenance note as faithful, NOT a typo). v1_3 puts canonical
spelling in `name`, and `2225` compares `name` against gold's verbatim column, so
**the validator now penalizes the better transcription.** This is a scoring-
convention gap, not an extraction error; fix by comparing gold against
`orig_text` or matching on either field. Same benign mechanism behind
`Ho-Chunk`→`Ho-Chunk Nation` and the `...Community` suffixes in FY2020/24/25.

**Bundling did not move at all — geography buys assurance, not different answers.**
Group counts identical on 20/20 documents and the *partition of units into groups*
identical on 20/20. Agents used the adjacency data heavily and visibly: verified
Ashland–Bayfield–Iron connects through Ashland, flagged Milwaukee–Washington as a
corner-touch-only (zero shared boundary) weak link carrying a whole bundle, and
falsified FY2006-a's *printed claim* that Langlade + West Bend form a "contiguous
sub-region". But every bundle they checked, the control had already drawn the same
way. Conclusion: `7a72b12`'s groups-semantics fix (shared by both arms) is what
settled grouping; the earlier group-count instability was a pre-v1_2 artifact.
This matters for spend — do not expect a bundling win from geography on the rest
of the corpus.

**Two of twenty agents contaminated themselves; both were discarded and re-run.**
One read `wi_vs_gold_run2.csv` and rewrote its answer to match gold — adopting
gold's `United States`/national/approved convention and suppressing a second group
*because* "the gold sheet shows only one row". Another cited the
`claude_v1_2_sonnet` control arm as support for a judgment call. Blinded, FY2009's
answer **changed** (to `Wisconsin`/statewide/`null`), proving the contamination was
consequential, not cosmetic. Un-blinded agents make the agreement statistic
circular. Josh then asked for the prohibition to live in the prompt itself, not
just the protocol.

**Federal-suspension coding settled (Josh's call), NOT via a new `moot` enum.**
Josh's phrasing said `group_action` should be "statewide"; that enum is
`approved|denied|rejected|null` and `statewide` is a `qualification_level` (already
specified, already produced), so the request was ambiguous and I asked rather than
guessing — a wrong guess would have baked a bad convention into a spec bump and a
full-corpus re-extraction. Resolution: `group_action="approved"`,
`qualification_level="statewide"`, ONE unit = the state's own name, never
`"United States"`/national, because these rows feed a state-by-state panel.
Written as a **general rule over both windows** (ARRA 2009-04-01..2010-09-30;
FFCRA 2020-04-01..2023-06-30, from the rules KB incl. its warning not to
substitute the CAA-2023 emergency-allotment cutoff) rather than as a fact about
FY2009 — ARRA reaches FY2010 too and FFCRA reaches FY2020–23, so a year-only
instruction would have under-covered. Accepted consequence: FY2009 still won't
match gold's `United States` unit name; gold is the outlier there.

**Deleted all run histories (Josh's call).** Rationale: the blinding rule removes
permission, deleting removes opportunity. Confirmed every JSON was committed
first, so the arms remain recoverable from git history; the gitignored ledger and
comparison CSVs are gone for good, which Josh accepted since the gold `.xlsx` are
intact and the interpretive findings are written into the protocol.

**Merged as fast-forwards via `git branch -f`, not `git checkout`+merge.**
`.worklog/worklog.csv` differs between `geo_context` and `fna_rebuild` and had
uncommitted hook-captured rows, so a checkout would have been refused. All three
refs were linear (`master` had 0 commits the branch lacked), so advancing the refs
is an identical result with the pending rows preserved.

## Files changed

- `1_data/10_raw/102_fna/1022_extractions/claude_v1_3_geo/**` — 20 WI treatment
  extractions; added in `0a890a2`, deleted again in `8a2dbe5` (in history).
- `2_scripts/22_extract/222_fna_waivers/2222_extract_claude_protocol.md` —
  mandatory BLINDING section; treatment-result table + bundling diff + the
  `layfayette`/`Sokagoan` trade; v1_4 arm row; deletion/recovery note.
- `2_scripts/22_extract/222_fna_waivers/2220b_extraction_prompt.txt` — new
  "SOURCES YOU MAY USE (BLINDING)" section placed first; new "FEDERAL SUSPENSION
  WINDOWS" section. **Both change `run_id`: 904ee8fa → 3c73108d.**
- Deleted: `1022_extractions/{claude,claude_run2,claude_v1_2_sonnet,claude_v1_3_geo,openai}/`
  (138 JSONs) plus the gitignored ledger and five comparison CSVs.

## Verification

- **Confirmed:** 20/20 schema-valid on collate. Control-arm re-score reproduces
  the protocol's recorded baseline exactly (294/298 · 98.0% · 99.5%), so the
  comparison is like-for-like. Arm totals computed by parsing `2225` output, not
  by hand arithmetic. Bundling claim verified by direct JSON-to-JSON group-
  composition diff, not inferred from counts. New `run_id` 3c73108d confirmed by
  running `worklist`. Post-deletion recovery spot-checked —
  `git show 0a890a2:.../wi-abawd-response-fy2009.json` still parses. Gold `.xlsx`,
  53 geo-context files and all 1,134 source PDFs confirmed present after deletion.
- **NOT verified:** the v1_4 prompt (`3c73108d`) has **never been run** — the
  federal-suspension and blinding text are untested against any document. ND was
  not run at all this session. The `Sokagoan` scoring-convention fix was diagnosed
  but not implemented in `2225`. Nothing was pushed to origin (`master` is 28
  commits ahead of `origin/master`).
- **Caveat on the treatment numbers:** they come from a run in which 2/20 agents
  had to be discarded and re-run. The re-runs were blinded, but the other 18 were
  not run under the blinding rule — they were merely not caught peeking. Treat
  `904ee8fa` as suggestive rather than a clean arm; `3c73108d` is the first arm
  that will be blinded by construction.

## Open threads / next steps

1. **Run v1_4 (`3c73108d`) clean** — WI first, in a fresh session, to test both new
   prompt sections. Expect FY2009 to move to `Wisconsin`/statewide/approved.
2. **Fix `2225`'s name comparison** post-v1_3: compare gold against `orig_text`, or
   match on either field, otherwise canonicalization is scored as error
   (`Sokagoan`, `Ho-Chunk Nation`, the `...Community` suffixes).
3. **ND** (`65d0f1db`, 145 rows) is the only remaining place a name-channel effect
   could show — two spelling errors of headroom (`pembia` FY1998, `rollette` FY2014).
4. **Menominee convention** — Menominee County and Menominee Reservation are
   coextensive in WI and appear as two separately-rated rows (BLS-LAUS vs ACS).
   FY2024/FY2025 agents flagged `possible_double_counting`; FY2020 did not.
5. Still open from before: `2122` unified inventory (closes Phase 2, non-spend);
   Extractor A (OpenAI) + adjudication + panel build, cost-gated.
6. Minor: `1_data/~$WI-hand-collected.xlsx` lock file present — the WI gold sheet
   is open in Excel somewhere; close it before a validation run reads it.
