---
title: NC replication run + bundle-vs-rationale-class fix to the extraction prompt
date: 2026-08-10
session_id: 3ebc088a-9af6-49c0-8d91-4f494c430d98
task_slug: nc-replication-and-bundle-semantics
status: wip
phase: Phase 3
tags: [abawd, fna, extraction, prompt-engineering, replication, schema, nc]
branch: fna_rebuild
head_commit: cce8239
commits: [cce8239]
transcript_path: /Users/joshuaylevy/.claude/projects/-Users-joshuaylevy-Documents-Work-USC-snap/3ebc088a-9af6-49c0-8d91-4f494c430d98.jsonl
---

# NC replication run + bundle-vs-rationale-class fix to the extraction prompt

**Re-read the full session:** `claude --resume 3ebc088a-9af6-49c0-8d91-4f494c430d98`
(or read the raw transcript at `transcript_path`)

## Context / goal

Resume point for the FNA rebuild: check plan progress and exercise the Claude
in-harness extractor on NC. NC has no hand-collected gold panel, so the question
was whether the extractor generalizes outside the gold states, and whether it is
reproducible. The session then turned into a design fix when Josh identified that
the extractor's notion of a "group" was wrong in a way that matters for the
paper's weighted-set-packing analysis.

## What was done

1. **Plan status.** Phases 0-2 complete and committed. Phase 3 half-built: the
   Claude extractor was committed in `8f234a6` (the resume memory claiming those
   scripts were uncommitted was stale). NC response docs had already been
   extracted in the 2026-07-21 pilot (11 docs, run 1).

2. **Post-2016 corpus gap.** Josh asked whether NC really has no post-2016 files.
   Verified locally (recon link map, download manifest, file tree) and against the
   LIVE FNA site: re-fetched the FY2015-19 / FY2020-24 / FY2025-29 batch pages, all
   HTTP 200, and diffed live links against the manifest — **zero difference** on all
   three. NC appears only through FY2016; the FY2020-24 page lists 41 states and
   FY2025-29 lists 25, NC in neither. Application-side zips run through FY2026 and
   contain an NC folder only for FY2009/2011/2014/2016. So the gap is FNA's, not
   the scraper's. Also found FY2014 has an NC application with **no posted response**
   — the two streams do not imply each other.

3. **NC replication run 2.** Since run 1 existed and NC has no gold, ran an
   independent re-extraction of all 11 NC response PDFs into `claude_run2/`
   (one `general-purpose` agent per PDF, same prompt/schema/model). 11/11
   schema-valid. Compared run 1 vs run 2 at (doc x normalized unit name) grain.

4. **Stray corpus file quarantined.** A byte-identical `nc-abawd-response-fy2016-a
   copy.pdf` (same sha256, absent from the download manifest) appeared in the raw
   corpus during the run; it would have silently double-counted FY2016's 77 counties
   downstream. Moved to the session scratchpad `quarantine/` rather than deleted;
   corpus restored to its manifest state of 1,136 files.

5. **Checkpoint commit `cce8239`** — froze the WI+NC extraction JSONs as a baseline
   so subsequent prompt edits can be evaluated against a fixed reference.

6. **The group-semantics fix (the substantive work).** Josh identified, from NC
   FY2002, that the seven counties approved under the LSA rule were being emitted as
   ONE group when they are seven independent single-county claims that merely share a
   stated reason. First proposal was rejected on good grounds: it relied on
   phrase-matching (look for an explicit aggregate statistic; look for a per-county
   designation statement) and neither document says any such thing. Rewrote the
   instruction to reason from the rule and the arithmetic instead. Then verified the
   gold convention empirically and found the earlier assumption about gold was wrong.

## Key decisions & why

- **`groups[]` is the evaluated SET, not the rationale class.** The paper's object
  of study is the bundle the state constructed. "Shares a stated reason" and "was
  evaluated jointly" are different facts about what the state DID, and the old
  schema could not distinguish them. Scale: 53 of 80 groups extracted so far are
  multi-unit, holding 592 of 617 units — this is the whole panel, not an edge case.

- **The sub-agent must reason, not pattern-match.** The load-bearing correction from
  Josh: states routinely compute a combined rate and present only the result, and the
  FY2002 letter never says each county was designated individually. So the prompt now
  (a) resolves the level from the RULE where the rule settles it — LSA designations
  attach to individual areas, so listing seven together states seven independent
  facts; pct10 is the area's own rate; EB/suspension are whole-state — and (b) for
  `pct20_above_natl`, where the level is genuinely open, makes the strongest test
  ARITHMETIC: an area whose own printed rate is below the printed threshold yet is
  approved proves aggregation, because nothing else could have carried it. That test
  fires precisely when the state aggregates silently.

- **A joint set keeps every member the state put in it**, including areas that would
  have qualified alone. Josh read the FY2007 PDF and confirmed the state deliberately
  constructed regions so weak counties ride along on the strong ones. Splitting a
  region into "qualified alone" vs "carried" (which the FY2007 agent did, producing 15
  groups) destroys the choice being studied. Correct output is ~8 sub-region groups.

- **`unknown` is a permitted answer.** Explicit instruction not to guess and not to
  "default to one group because it is tidier". A fabricated coalition corrupts the
  choice set in the direction the analysis is most sensitive to.

- **Gold already uses this convention — verified, not assumed.** Josh recalled that
  his ND/WI hand-labelling used the evaluated-set notion. Checked both sheets: WI
  FY2003 is 79 units in 79 singleton groups (each LSA / 20%-rule / rejected county its
  own group), while ND FY2008 is 20 units in ONE group, ND FY2011 10 units in one,
  WI FY2005 42 units in 19 groups sized 9/5/4/4/3/2. So gold `group_id` is a group
  INDEX and `number_of_groups` a true count — the same semantics the schema already
  had. An earlier docstring in `fna_extraction_results.py` claimed gold used "per-unit
  running counters" and that the columns were unreconciled; that was wrong and was the
  basis for my incorrect warning that this change would break gold comparability. It
  does not. Corrected in place.

- **Extraction JSONs are now versioned** (`.gitignore` change). They were ignored as
  "regenerable", but the replication showed agentic extraction is NOT deterministic, so
  a baseline cannot be reconstructed by re-running. Derived flat/comparison CSVs stay
  ignored — those ARE deterministic given the JSONs.

## Files changed

Committed in `cce8239`:
- `.gitignore` — un-ignore `1022_extractions/**/*.json`; keep derived CSVs ignored.
- `1_data/10_raw/102_fna/1022_extractions/claude/**` (31 JSONs) — run-1 baseline.
- `1_data/10_raw/102_fna/1022_extractions/claude_run2/**` (31 JSONs) — WI + new NC run 2.
- `.claude/settings.json`, `.worklog/**` — per the existing .gitignore intent.

Uncommitted at time of writing (the v1_2 semantics change):
- `2_scripts/22_extract/222_fna_waivers/2220b_extraction_prompt.txt` — replaced the
  splitting rule with the counterfactual test, rule-driven defaults, the arithmetic
  evidence test for pct20, joint-set scope rule, denied-area rule, and an explicit
  "both shapes are common / a high group count is correct" note.
- `2_scripts/22_extract/222_fna_waivers/2220c_schema.json` — added group
  `qualification_level` (required), `qualification_level_evidence`, `bundle_label`;
  unit `unemployment_rate`, `qualifying_basis`.
- `2_scripts/22_extract/222_fna_waivers/fna_extraction_results.py` — 5 new EXTRA_COLUMNS
  (GOLD_COLUMNS still an exact prefix, 65 total); `number_of_groups` now DERIVED as
  `len(groups)` so it cannot contradict `group_id`; corrected the gold-convention docstring.

## Verification

**Confirmed:**
- NC post-2016 gap: live FNA pages re-fetched, live-vs-manifest link diff empty on all
  three later batches.
- Run 2: 11/11 schema-valid. vs run 1 — 284 matched units, criterion 283/284, action
  284/284. Divergences: FY2007 run-1 OCR errors `Pasguotank`/`Perguimans` corrected to
  Pasquotank/Perquimans in run 2; FY2013 criterion `eb_trigger` (run 2, inferred from a
  cited trigger-notice FILENAME) vs null (run 1) — the email states no rule. Group COUNTS
  unstable (FY2006 14->8, FY2007 2->15) while units/criteria stable.
- Gold convention: checked directly against both xlsx files (group-size distributions above).
- Schema edit non-destructive: key-level diff old vs new shows ZERO keys removed.
- Flattener: GOLD_COLUMNS still an exact prefix of FLAT_COLUMNS; runs clean on a
  baseline JSON; `number_of_groups` now derived.
- New `run_id` = `9c59a0f4` (baselines were `5b2866b2` / `e8729c5c`).

**NOT verified:**
- The revised prompt has NOT been run against any document. Josh is doing that in a
  fresh session. Nothing in this session tests whether agents actually apply the
  counterfactual test correctly.
- The NC S.L. 2015-241 hypothesis (below) is recollection, unchecked against the statute.
- The contiguity requirement for joint groups is still a DRAFT item in the rules KB;
  the prompt uses it only as corroborating evidence, never as a decisive test.

## Open threads / next steps

1. **Run the revised prompt against WI+NC and diff vs the `cce8239` baseline.** Watch
   NC FY2002 (expect 8 singleton groups), FY2004-a (expect 37), FY2006, FY2007
   (expect ~8 sub-region groups, not 15). Fresh session, per Josh.
2. **Ledger cannot record replicate runs.** `run_id = hash(instruction+prompt+schema+
   model)` is spec-derived, so a re-run of the SAME spec collides on the
   `(document_id, extractor, run_id)` key and `collate` only ever reads `CLAUDE_DIR`.
   Both WI run 2 and NC run 2 are invisible to `10220_extraction_results.csv`. Needs a
   run-instance id or a `--json-root`/`--replicate` flag on `2222`. Also: baseline JSONs
   will now fail validation (`qualification_level` required) — do NOT `collate` them or
   it writes 31 `schema_invalid` rows over the run-1 entries.
3. **County-name validation against a FIPS crosswalk** would have caught the
   Pasguotank/Perguimans class mechanically, and would also let contiguity be checked
   programmatically on every `joint_aggregate` group.
4. **NC as an observation.** NC disappears from both streams after FY2016. Hypothesis
   worth checking: NC session law S.L. 2015-241 barred DHHS from seeking ABAWD waivers,
   which would make post-FY2016 non-application legally imposed rather than chosen — it
   is then not a valid revealed-preference observation. Check other states absent from
   the later batches (GA, IN, TN, UT, OH drop out) for similar bans.
5. **FY2016-a threshold truncation.** FNS states the national 24-month average as 6.8%
   and the 20%-above threshold as 8.1%, but 6.8 x 1.2 = 8.16. Both NC bundles come in at
   8.05%, so both qualify ONLY because FNS truncated rather than rounded. Bears directly
   on whether NC's FY2016 allocation is feasible under the stated rule.
6. **Quarantined file** at the session scratchpad `quarantine/nc-abawd-response-fy2016-a
   copy.pdf` — restore if it was deliberate.
7. Still unbuilt: `2122` unified inventory, `2221` OpenAI extractor (cost gate),
   `2223` adjudication, `2224` panel build. ND gold never touched.
