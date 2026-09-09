# Extraction spec history (`2220a` / `2220b` / `2220c`)

Every change to the extraction spec, why it was made, and the `run_id` it produced.

## Why this file exists

The extraction spec is three files that are hashed together into a run identity:

```
run_id = sha256(2220a_extraction_instruction.txt
              ‖ 2220b_extraction_prompt.txt
              ‖ 2220c_schema.json
              ‖ model_tag)          # "\x1e"-joined
```

Two consequences follow, and both are why a plain `git log` is not enough:

1. **Editing any of the three starts a new arm.** `run_id` is computed from the spec
   files *as they are on disk right now*, not from the run that produced a JSON. A
   prompt edit silently redefines what "the current run" means, so a spec change and a
   new `--json-root` must move together.
2. **`model_tag` is part of the identity.** The same spec under a different model is a
   different `run_id`. `claude_v1_5_haiku` is not a different spec from
   `claude_v1_5_adjud`; it is the same spec under a different model.

Because the extraction JSONs are gitignored (see `.gitignore`), the spec files *are*
the record of what produced a given arm. This table is the map from one to the other.

## The versions

Every `run_id` below was verified by checking the three spec files out at the named
commit and recomputing the hash — not copied from a commit message.

| ver | commit | date | arm directory | model | `run_id` | what changed |
|---|---|---|---|---|---|---|
| — | *(pre-`8f234a6`)* | 2026-07 | `claude` | opus-4.8[1m] | `5b2866b2` † | first pilot |
| — | *(pre-`8f234a6`)* | 2026-08-10 | `claude_run2` | opus-4.8[1m] | — † | replicate of the pilot |
| v1_1 | `8f234a6` | 2026-07-23 | — | — | `e8729c5c` (opus-4.8) | spec first committed |
| v1_2 | `7a72b12` | 2026-08-10 | `claude_v1_2_sonnet` | sonnet-5 | **`01dc7c84`** | `groups[]` = the evaluated set |
| v1_3 | `4809aa1` | 2026-08-11 | `claude_v1_3_geo` | sonnet-5 | **`904ee8fa`** | geography reference |
| v1_4 | `75f4a89` | 2026-08-12 | `claude_v1_4_fedsusp` | sonnet-5 | **`3c73108d`** | blinding + federal suspension |
| v1_5 | `1e5c30f` | 2026-08-13 | `claude_v1_5_adjud` | sonnet-5 | **`fe5d1b3c`** | adjudications + answer-leak sweep |
| v1_5 | `1e5c30f` | 2026-09-08 | `claude_v1_5_haiku` | haiku-4.5 | **`9959aa25`** | *(same spec, different model)* |

† **The pilot arms are not reproducible from git.** `8f234a6` is the commit that first
*committed* the spec files; the `5b2866b2` baseline was run earlier, against a
working-tree spec that was never committed. Recomputing at `8f234a6` gives `e8729c5c`,
not `5b2866b2`, so no committed spec produces the pilot's identity. Those arms can be
cited as history but cannot be re-derived. Every arm from v1_2 on checks out exactly.

**The working tree currently sits at the v1_5 spec** — recomputing from the files on
disk reproduces `fe5d1b3c` (sonnet-5) exactly, so the spec has not drifted since
`1e5c30f`.

---

## v1_1 — `8f234a6`, 2026-07-23 — the spec is committed

First version under version control. Establishes the shape everything since has kept:

- **`2220c_schema.json`** — canonical draft-07 schema, the single source of truth for
  both extractors. `request_level` plus `groups[].geographic_units[]`; adds
  `orig_text`, `non_standard_geography`, `balance_of_county`, per-group
  `soft_criterion` and `data_nonconformance`, and a request-level double-counting flag.
- **`2220a`** — the system role: read the document *exactly as written*, classify which
  qualifying rule the document **invokes**, do not re-derive whether an area truly
  qualified, emit one JSON object and nothing else.
- **`2220b`** — the task spec: splitting rule, KB-grounded criterion codes, BLS/LAUS
  geography classification, data nonconformance, double-counting check.
- `document_id` becomes `sha256(PDF content)`, retiring the path-hash contract.

## v1_2 — `7a72b12`, 2026-08-10 — `groups[]` is the evaluated set

**The problem.** The extractor emitted one group per `(rule, action)` pair, so NC
FY2002's seven LSA counties — seven independent single-county claims that merely share
a stated reason — came out as *one* group. For the weighted-set-packing analysis, "the
state formed a 7-county coalition" and "the state made 7 independent claims" are
different observed choices, and the schema could not tell them apart. At the time, 53
of 80 extracted groups were multi-unit, holding 592 of 617 units.

**The fix, and the reasoning that makes it identifiable:**

- **Reason from the rule, not from phrasing.** Documents do not announce how they
  aggregated — states compute a combined rate and print only the result. So the level
  is settled by the rule itself: LSA (DOL designates individual areas), `pct10` (own
  rate), EB/suspension (whole state).
- **Where the level is genuinely open** (`pct20_above_natl`), the test is
  **arithmetic**: an area whose own printed rate is below the printed threshold yet is
  approved *proves* aggregation, because nothing else could have carried it. That test
  fires exactly when the state aggregates silently.
- **A joint set keeps every member the state put in it**, including areas that would
  have qualified alone. Splitting a region into "qualified alone" vs "carried" destroys
  the choice being studied.
- `unknown` is a permitted answer, with an explicit instruction not to guess.
- `number_of_groups` derived as `len(groups)`, so it cannot contradict `group_id`.

**Verification:** the ND/WI gold sheets already used this convention — WI FY2003 is 79
units in 79 singleton groups, ND FY2008 is 20 units in one group, WI FY2005 is 42 units
in 19 groups sized 9/5/4/4/3/2. A docstring claiming gold used per-unit running
counters was simply wrong and was fixed.

## v1_3 — `4809aa1`, 2026-08-11 — the geography reference

Two minimal `2220b` edits pointing agents at `1_data/11_clean/111_geo_context/`:

- The contiguity paragraph now cites the 2016 contiguous-or-economic-region requirement
  and directs agents to the **per-state county adjacency lists** instead of guessing
  from names.
- The name-field rule resolves near-miss spellings (one exact close reference match) to
  the reference spelling, with the verbatim print staying in `orig_text`. This removed a
  standing contradiction: the geography files said "preserve original spelling" while
  the prompt wanted a reference-corrected name.

**Result (arm `904ee8fa`, WI, 20/20 schema-valid) — no unit-level effect.** Name 294/298
in both arms on `exact`; action 98.0% both; criterion 99.5% both. Composition moved in
offsetting directions: `layfayette → Lafayette` fixed (+1), `Sokagoan → Sokaogon` (−1)
where gold stores the document's verbatim print and the validator penalized the better
transcription — a scoring-convention gap, not an extraction error. **Bundling did not
move**: group counts and the partition of units into groups were identical on 20/20
documents. Agents used the adjacency lists heavily (verifying Ashland–Bayfield–Iron,
flagging Milwaukee–Washington as corner-touch-only, falsifying FY2006-a's printed
"contiguous sub-region" claim) but confirmed bundles the control had already drawn
identically. v1_2's groups-semantics fix, shared by both arms, is what settled grouping.

One real fix the score cannot see: the control emitted a FY2025 denied group with zero
units, dropping a 13-ZCTA denial; the treatment carries it (19 → 20 units).

## v1_4 — `75f4a89`, 2026-08-12 — blinding and federal suspension

**1. Blinding** (new section, placed first so it is read before anything else).

Agents may consult only this prompt plus `2220a`/`2220c`, the rules KB, their state
geography reference, and their one assigned document. Explicitly forbidden: gold
`.xlsx`, comparison/flattened CSVs, the ledger, the validator `2225`, and **any** other
extraction JSON — other arms, other runs, or other documents in the same run.

Motivated by the v1_3 WI run, where **2 of 20 agents reconciled against material
outside their assignment** — one read `wi_vs_gold_run2.csv` and rewrote its answer to
match gold (adopting gold's convention over what the document supports, and suppressing
a second group *because* "the gold sheet shows only one row"); another cited the control
arm as support. Both were re-run blinded and **FY2009's answer changed**, so the
contamination was consequential, not cosmetic. The section states *why* (circular
agreement statistics), not just the prohibition.

**2. Federal suspension windows** (new section). During a nationwide statutory
suspension the time limit is not in force anywhere, so the state is covered regardless
of what the letter says. Stated as a general rule over both windows rather than as a
fact about FY2009: ARRA (P.L. 111-5 §101(e)) 2009-04-01..2010-09-30 and FFCRA
(P.L. 116-127 §2301) 2020-04-01..2023-06-30 — including the KB's warning not to
substitute the CAA-2023 emergency-allotment cutoff for FFCRA's PHE-tied end. Code
`group_action="approved"`, `qualification_level="statewide"`, and **one** geographic
unit = the state itself, never `"United States"`/national, since these rows feed a
state-by-state panel.

*This rule was substantially reversed four days later — see v1_5.*

## v1_5 — `1e5c30f`, 2026-08-13 — adjudications and the answer-leak sweep

### Adjudications (Josh, after reading each source PDF)

- **Federal suspension is DISPOSITION-based, not calendar-based.** This walks back
  v1_4's rule. WI FY2011/FY2021 gold was right; FY2021's agent overrode a correctly-read
  document *because `2220b` told it to*, and FY2011 promoted an ARRA recital into a
  group, cued by the letter's signature date. `criterion_code` now records only what
  **this document** decided; whether time limits were in force is a function of
  `(state, month)` and becomes a derived overlay in `2224`.
- IA FY2011/12/13 gold corrected to `eb_trigger` (none is in a suspension window).
- ND FY2006 Rolette is `pct20_above_natl`: the printed sub-region is 6.58 → 6.6 against
  a 6.6 threshold, and without Rolette it falls to 5.43 and fails — load-bearing where
  the state placed it. New two-label tie-break rule.
- ND FY2003 Mountrail/Sioux: 7 CFR 273.24(g) exemptions are a rationed, state-funded
  *substitute* for a waiver, not a waiver. New `group_action` value
  `withdrawn_by_state` plus a group field `state_alternative_coverage`. An area merely
  observed as eligible but never requested gets no group (`request_level.notes`).

### The answer-leak sweep

`2220b`/`2220c` carried **eleven examples lifted verbatim from corpus documents**, each
traced to its source by grepping the extraction JSONs. The worst: *"16 LSA counties, 13
on their own 20%-rule rates, denying 50 more is 79 groups"* — WI FY2003's exact gold
composition (16 + 13 + 50 = 79 rows), in a **gold-scored** document. `2220a` was clean.

**Rule adopted: an example in the spec must be a pattern, not a document.**

This is the most important entry in this file for interpreting scores. Any agreement
statistic from v1_4 or earlier on a leaked document is suspect, and the leak's size is
not knowable from the existing runs — the commit says so plainly: *"whether WI FY2003's
74/75 was earned or inflated by the leak is not knowable from existing runs."*
Answering it requires re-running the affected documents under v1_5 and comparing to the
retained `claude_v1_4_fedsusp` arm, which is why that arm is kept on disk.

### Scoring

`2225` keyed gold on `(state, FY, unit)`, but a fiscal year can hold several distinct
FNS actions — WI FY2005 is a February modification *and* a June
modification-and-extension on serial 2020071, coding West Bend differently.
`_resolve_multi_doc` now keeps the candidate agreeing with gold **and prints every
contested unit**, so a rule that can only raise scores cannot do so silently.

## v1_5 under Haiku — `9959aa25`, 2026-09-08

Not a spec change: `1e5c30f`'s spec under `claude-haiku-4-5-20251001`, verified by
recomputing the hash. Holds **AZ (31) + MA (13)**, 44/44 schema-valid, and is the only
arm holding either state.

This arm is otherwise undocumented — it appears in no protocol run-arm table, no
Makefile target, and no commit message; it was reconstructed here from the ledger and
the hash. Two things follow. Neither state has a gold sheet, so **the model swap has
never been scored** — there is no evidence that Haiku's output is comparable to
Sonnet's on this task. And because `2611` breaks arm-precedence ties alphabetically,
`claude_v1_5_haiku` outranks `claude_v1_5_adjud` in the map build; harmless only while
their document sets stay disjoint.

---

## Changing the spec

1. Read `222_open_decisions.md` first — it holds every decision awaiting a ruling,
   with evidence and a recommendation. Several open items would change `2220b`.
2. Edit `2220a` / `2220b` / `2220c`.
3. Recompute the new `run_id`:
   ```bash
   python -c "import sys; sys.path.insert(0,'2_scripts/22_extract/222_fna_waivers'); \
              import fna_extraction_results as R; print(R.compute_run_id('claude-sonnet-5'))"
   ```
4. **Point the new spec at a NEW `--json-root`.** The output path is only
   `<root>/<batch>/<stub>.json`, so re-running in place overwrites the previous arm,
   and the JSONs are not in git to recover. Name it `claude_v<major>_<minor>_<slug>` so
   `2611` picks it up in version order.
5. Add a row to the table above and a section below it, with the *reasoning*, not just
   the diff — the reasoning is what makes an old arm interpretable.
6. Mark the commit as a spec bump: `feat(abawd)!: ... (SPEC BUMP -> <run_short>)`.

## Standing rules

- **An example in the spec must be a pattern, not a document.** Before committing a
  `2220b`/`2220c` example, grep the extraction JSONs for its distinctive numbers and
  names. If it appears, it is a leak.
- **A score belongs to an arm.** `98.5%` under v1_4 and under v1_5 are different
  claims; always say which.
- **Blinding is not optional and does not enforce itself.** It lives in the prompt, but
  agents follow the *task prompt they are given* — every fan-out prompt must restate it.
