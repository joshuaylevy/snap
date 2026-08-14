---
title: v1_5 spec bump — four adjudications, answer-leak sweep, document-level scoring join
date: 2026-08-13
session_id: 2e85e5c7-b3b6-4046-9c7b-8ccba50e1764
task_slug: fna-v1-5-adjudications-leak-sweep
status: complete
phase: Phase 3
tags: [abawd, fna, extraction, prompt-spec, gold-standard, blinding, validator]
branch: master
head_commit: fda3855
commits: []
transcript_path: /Users/joshuaylevy/.claude/projects/-Users-joshuaylevy-Documents-Work-USC-snap/2e85e5c7-b3b6-4046-9c7b-8ccba50e1764.jsonl
---

# v1_5 spec bump — four adjudications, answer-leak sweep, document-level scoring join

**Re-read the full session:** `claude --resume 2e85e5c7-b3b6-4046-9c7b-8ccba50e1764`
(or read the raw transcript at `transcript_path`)

## Context / goal

Started as a status request — summarize the last eval run (the four gold states +
NC) and tabulate tier progress. It turned into settling the four open adjudications
that the v1_4 run had surfaced, and then into a wider audit of the spec files after
one of those adjudications exposed that the extraction prompt had been quoting the
corpus back at the agents.

Entering state: arm `claude_v1_4_fedsusp` (`run_id 3c73108d`, sonnet-5), 63 docs
across WI/ND/NC/DE/IA, all schema-valid, with four unresolved gold disagreements and
a "headline finding" that the v1_4 federal-suspension rule was being applied
inconsistently across agents.

## What was done

**1. Re-scored the v1_4 arm from the JSONs on disk** (did not trust the recorded
numbers). Reproduced the protocol's figures exactly: WI 294/298 name, 290/294
action, 198/202 criterion; ND 145/145, 143/145, 142/145; DE 4/5, 4/4, 4/4; IA 7/7,
7/7, 3/6.

**2. NC run-to-run comparison.** NC has no gold. Restored the `01dc7c84` control arm
from git history (`git archive 8a2dbe5^`) into job tmp, flattened both arms via
`2223`, and compared: 288 rows each, **286/286 criterion, 286/286 action, group
partition identical on 11/11 documents**. The only divergences are two v1_4
improvements — control's OCR `Pasguotank`/`Perguimans` corrected to
`Pasquotank`/`Perquimans`. Deleted the restored control from tmp afterward for
blinding hygiene. Notable because NC's group counts had been the *unstable* channel
in the earlier replication (FY2006 14→8, FY2007 2→15); they are now stable.

**3. Read the source PDFs for all four open adjudications** and assessed ground
truth. Josh then adjudicated. See Key decisions.

**4. Wrote the v1_5 spec changes** — three prompt edits, three schema additions,
flattener support, and a validator join fix.

**5. Answer-leak sweep.** Josh asked to anonymize the `WI FY2003 (serial 2020071)`
example in `2220b`; the sweep found **eleven** such leaks across `2220b` and `2220c`,
including one worse than the flagged one. Each was traced back to its source document
empirically (not from memory) by grepping the extraction JSONs. `2220a` was clean.

**6. Re-evaluated** after each round of changes. Confirmed the prompt/schema edits
cannot move scores until re-extraction, and that the observed movement came only
from Josh's gold edits and the scorer fix.

**No re-extraction was run.** That is the next step.

## Key decisions & why

**(1) Federal suspension is disposition-based, not calendar-based.** WI FY2011 and
FY2021 gold (`EUB`) is correct; the extraction (`ARRA`) was wrong. FY2011's waiver
period (Oct 2010–Sep 2011) lies wholly *outside* the ARRA window, and the letter's
"ARRA allows … **However** … **because** the State meets extended unemployment
benefits criteria" recites ARRA only to establish it has expired. FY2021's FNS letter
rests approval on Trigger Notice 2020-18 under 7 CFR 273.24 and never mentions FFCRA.

Root cause identified in the agents' own JSONs: FY2021's agent wrote "*Per this
project's federal-suspension coding rule*" in `criteria_summary_text` while storing
the EB text in `criterion_verbatim` — it read the document correctly and then
overrode itself because `2220b` told it to. FY2011 was a *different* failure: the
ARRA recital was promoted into a group of its own, cued by the letter's Aug-2010
signature date.

The design flaw: `criterion_code` was being asked to carry two different objects —
(a) the legal basis of *this document's* decision, and (b) whether time limits were
in force in that state-year. (b) is a pure function of (state, month) and requires
reading nothing; asking 63 agents to re-derive it is what produced the WI-vs-ND
inconsistency. **Decision:** prompt codes only (a); (b) becomes a derived
`federal_suspension_in_force` overlay in the panel builder. Strictly more information
than the collapsed version, and immune to agent variance.

**(2) IA FY2011/12/13 → `eb_trigger` in gold** (Josh edited the sheet). All three
cite 7 CFR 273.24(f)(2) + a DOL EB determination and sit in neither suspension
window. Gold was wrong. But the *intuition* behind the original coding is worth
keeping: the May 3 2011 "All Regional Directors" memo qualified 46 states at once, so
"applying" in those years is a one-paragraph notification carrying almost no
revealed-preference content. Candidate `blanket_national_action` flag for the panel —
recorded, not built.

**(3) DE FY2026 unenumerated denial — deliberately NOT fixed.** The letter denies
"the specified areas" and never names them (verified by reading it), so the extraction
emits a denied group with zero units. A `unit_enumeration` schema field was designed
and **declined by Josh** because FY2026 is being dropped from the panel anyway. WI
FY2009 is the same shape and remains a known 1-unit residual.

**(4) ND FY2006 Rolette → `pct20_above_natl`** (gold right, extraction wrong). The
letter contradicts itself — item 9 lists Rolette inside the aggregate 20%-rule
sub-region, the asterisk footnote calls it an LSA, and the footnote's restatement of
the 20%-rule list omits it. **The arithmetic settles it:** the group as printed is
49,500/752,843 = 6.58 → 6.6 against a 6.6 threshold; drop Rolette (25% of the group's
labor force, running at 9.9%) and it falls to 5.43 and fails. Rolette is load-bearing
where the state put it. The LSA designation is what earns the 24-month rather than
12-month approval. Side finding worth keeping for the paper: a bundle constructed to
land *exactly* on the threshold is evidence of deliberate strategic bundling.

**(5) ND FY2003 Mountrail/Sioux — 273.24(g) exemptions are not a waiver.** The letter
says the state "is not seeking a waiver for Sheridan County and … will use its 15
percent exemption authority under 7 CFR 273.24(g) to exclude residents of Mountrail
and Sioux." Discretionary exemptions are individual-level, state-allocated, and
rationed (15% of covered caseload; 12% from FY2020) — coverage the state *buys*, not
coverage FNS *grants*. Coding them as approved waivers would erase exactly the margin
the panel measures, and would inflate approval rates. **Decision:** new
`group_action` value `withdrawn_by_state` + new group field
`state_alternative_coverage`. Josh added the matching gold column. Third case added
to the prompt: an area the document merely observes as eligible but never requested
(Sheridan) gets **no group at all** and goes to `request_level.notes` — a clean
revealed-preference observation that v1_4 dropped entirely.

**(6) The WI FY2005 "collision" is a validator defect, not an extraction defect.**
Two documents (a February *Modification* expiring 2005-03-31 and a June *Modification
and Extension* expiring 2006-03-31) share serial 2020071 and both map to FY2005. West
Bend is `percent_20` in the first and `lsa` in the second; both extractions are
faithful. The scorer keyed on `(state, FY, unit)` and silently took whichever row it
saw first. Josh's framing: two distinct actions, so fix the validator, not the data —
budgeted at <20 lines. **Decision:** `_resolve_multi_doc` keeps the candidate that
agrees with gold (the question being "does the corpus contain gold's action", not
"did an arbitrary pick land on it") and **prints every contested unit with its
competing doc stubs**, so a rule that can only raise scores can never do so silently.
Deeper issue recorded for `2224`: these waivers run April–March, so fiscal year is a
lossy key for what is really a (serial, coverage-interval, area) tuple.

**(7) Answer-leak sweep — the spec was teaching to the test.** Eleven illustrative
examples in `2220b`/`2220c` were lifted verbatim from corpus documents, so an agent
assigned one of those documents was handed its own answer. All replaced with abstract
patterns. Traced empirically:

| where (HEAD line) | leaked | traced to |
|---|---|---|
| `2220b` 87–90 | "Ashe, Columbus, Edgecombe, Robeson, Rutherford, Scotland and Vance … as LSAs" → "seven groups" | NC FY2002, FY2004-a, FY2006, FY2007, FY2016-a |
| `2220b` 113 | `"70 County Group"` | literal `bundle_label` in NC FY2016-a |
| `2220b` 152–154 | `WI FY2003 (serial 2020071)` | WI FY2003 — the one Josh flagged |
| `2220b` 166–169 | "16 LSA counties, 13 on their own 20%-rule rates, denying 50 more is 79 groups" | **WI FY2003's exact gold composition: 16 LSA-approved + 13 percent_20-approved + 50 rejected = 79 rows.** Worse than the named leak |
| `2220b` 174, `2220c` 592 | "Cleveland 6.1 is below the 6.3 threshold yet approved" | `Cleveland` is a real NC county in 5 docs; the 6.1/6.3 pair matches no printed rates found (11.5 FY2006, 7.3 FY2007), so name-only leak |
| `2220b` 270–271 | printed "Pasguotank" → name "Pasquotank" | NC FY2007 — that JSON contains both strings; also one of only two v1_4 improvements over control |
| `2220b` 265–268, `2220c` 261/265 | "Eau Claire city", "Balance of Adams County", "Bad River Reservation" | WI units (vocabulary, not a decision — weakest of the set) |
| `2220c` 599 | "70 County Group", "Advantage West Sub-region 1" | NC FY2016-a; "Sub-region of the Advantage West Region" in NC FY2006/FY2007 |
| `2220b` fed-suspension | the ARRA "however/because" quotation | **introduced by me earlier the same session** when rewriting that block; removed before any run used it. Never committed |

Rule adopted: **an example in the spec must be a pattern, not a document.** Never a
real unit, rate, count, serial, or state/FY from the corpus. This is the same
contamination the BLINDING block guards against, arriving through the front door — an
agent obeying blinding perfectly still gets the answer if the prompt contains it.
Aggravating factor: the leaks were drawn from the documents that had proved hardest,
i.e. exactly where scored agreement was most likely inflated.

Mitigating evidence, recorded for honesty: v1_4's WI FY2003 produced **32 groups, not
79** — it bundled the 50 denials into one group rather than splitting per unit. So
the unit-level 16/13/50 composition matched gold exactly while the group count did
not. Agents were not copying the example wholesale.

**(8) `state_alternative_coverage` comparison is exact.** Gold initially read
`discretionary_exemption273_24_g` (typo); a punctuation-insensitive normalizer was
added, then removed at Josh's instruction once he fixed the sheet. `_norm_alt` now
trims case and whitespace only, so a mismatch is a real disagreement.

## Files changed

- `2_scripts/22_extract/222_fna_waivers/2220b_extraction_prompt.txt` — federal-suspension
  block rewritten as disposition-based (+ "a recital is not a group", + anchor the
  window test on the waiver period not the signature date); two-label tie-break with
  the drop-the-unit-and-recompute test under SCOPE OF A JOINT SET; new WITHDRAWN AREAS
  AND STATE-DECLARED ALTERNATIVE COVERAGE section with the denied/withdrawn/
  never-requested three-way distinction and trigger phrases; all 8 leaked examples
  abstracted.
- `2_scripts/22_extract/222_fna_waivers/2220c_schema.json` — `group_action` += 
  `withdrawn_by_state`; new group field `state_alternative_coverage`; new
  `request_level.notes`; 4 leaked descriptions abstracted.
- `2_scripts/22_extract/222_fna_waivers/fna_extraction_results.py` — `EXTRA_COLUMNS` +=
  `state_alternative_coverage` and emit it; wire `notes` from `request_level.notes`
  (it had been hardcoded to `None`, so the gold `notes` column was always empty).
  Also carries the **previous** session's uncommitted work: `gold_path`/`gold_states`
  replacing the hard-wired GOLD_WI/GOLD_ND pair, and the `_PERIOD_RE` fix in
  `_fy_from_name` (ND FY2018 was named by waiver period, so its fiscal_year was null
  and 9 ND gold units were invisible to scoring).
- `2_scripts/22_extract/222_fna_waivers/2225_validate_vs_hand_collected.py` —
  `_resolve_multi_doc` document-level join + per-FY reporting of contested units;
  `_norm_alt` + `state_alternative_coverage` scoring (`alt_coverage n/d`, printed only
  where gold carries the column). Also the previous session's criterion-vocabulary
  normalizer and `--fys`-optional/per-state-TOTAL changes.
- `2_scripts/22_extract/222_fna_waivers/2222_extract_claude_protocol.md` — v1_5 arm row;
  full v1_5 adjudication section (ground truth per case, the Rolette arithmetic, the
  leak-sweep table, the join-key rationale, re-scoring table, re-run scope). Also the
  previous session's v1_4 result section.
- `Makefile` — previous session's `FYS ?=` empty + `fna_validate` doc update.
- `.worklog/` — this entry + CSV row.

**Not staged:** `1_data/10_raw/102_fna/1022_extractions/` remains untracked. Committing
it would undo `8a2dbe5`, which deliberately wiped extraction outputs from the working
tree so future extraction agents cannot read a prior arm. Josh confirmed.

## Verification

**Done and confirmed:**
- Re-scored all four gold states from the JSONs on disk, three times (baseline, after
  gold+validator changes, after the leak sweep). Baseline reproduced the protocol's
  recorded figures exactly.
- NC run-to-run vs the restored `01dc7c84` control: 286/286 criterion, 286/286 action,
  group partition identical 11/11.
- Schema validates as Draft 2020-12; **all 63 v1_4 JSONs still validate under the
  revised schema**, so the old arm stays readable.
- `2223` flatten round-trip: 66 columns, `columns match flat layout` True,
  `state_alternative_coverage` and `notes` both present.
- The WI FY2005 collision fix behaves correctly: West Bend resolves to gold's coding;
  **Oneida correctly does NOT resolve** (only the June letter mentions it, and it
  denies) — the fix is not blanket-charitable.
- Every leak traced to a named source document by grepping the extraction JSONs, not
  from memory. The 16/13/50/79 claim checked against the WI gold sheet directly.
- `run_id` recomputed after each spec edit: `3c73108d` → `236c8054` (interim, never
  run) → **`fe5d1b3c`** (current).

**Explicitly NOT done:**
- **No re-extraction.** Every score in this entry is the v1_4 arm re-measured; the
  prompt and schema changes cannot move a number until the v1_5 arm runs.
- The `federal_suspension_in_force` overlay and `blanket_national_action` flag are
  *specified*, not built — they belong to `2224`, which is still a stub.
- Whether WI FY2003's near-perfect score (74/75, 74/74, 27/27) was earned or inflated
  by the leaked composition is **not knowable from existing runs**. Only a clean v1_5
  run answers it.

**Score movement after gold + validator fixes (extractions unchanged):**

| state | name | action | criterion | change |
|---|---|---|---|---|
| WI | 294/298 (98.7%) | 290/294 (98.6%) | 199/202 (98.5%) | ← 198/202, West Bend via join fix |
| ND | 145/145 (100%) | 143/145 (98.6%) | 142/143 (99.3%) | denominator −2 (Mountrail/Sioux no longer gold-`approved`) |
| DE | 4/5 (80%) | 4/4 (100%) | 4/4 (100%) | unchanged |
| IA | 7/7 (100%) | 7/7 (100%) | 6/6 (100%) | ← 3/6, gold corrected |

ND FY2003 reports `alt_coverage 0/2` and 2 action misses — correct and expected, since
v1_4 predates `withdrawn_by_state`.

## Open threads / next steps

1. **Run the v1_5 arm** — `run_id fe5d1b3c`, root
   `1_data/10_raw/102_fna/1022_extractions/claude_v1_5_adjud`. Minimum 9 docs to close
   the adjudications: WI FY2005 ×2, FY2009, FY2011, FY2021; IA FY2011/12/13; ND FY2003,
   FY2006. Expected: WI criterion +2, ND action +2 with `alt_coverage` 2/2, ND FY2006
   criterion +1.
2. **Consider re-running WI FY2003 and the 5 leak-affected NC docs** even though their
   adjudications are settled — their scores were measured under a leaking prompt and
   are not clean evidence.
3. **Tier 1 extraction** (WY, MS, KS, NE, SC, AR, WV — 90 docs) was deliberately held
   until the spec settled. It is now unblocked.
4. `2224` panel builder: `federal_suspension_in_force` window overlay,
   `blanket_national_action` flag, and the coverage-interval-vs-fiscal-year keying
   question raised by the WI FY2005/FY2013 multi-document years.
5. Gold's `status` column vs `group_action` — Josh set `status=approved` while
   `group_action=withdrawn_by_state` for Mountrail/Sioux, which reads as a deliberate
   "was coverage achieved" vs "what did FNS do" split. The flattener still mirrors
   `status` from `group_action` and cannot reproduce it. Worth settling before `2224`.
6. Remaining known residuals, all adjudicated and accepted: WI FY2009
   `national`/`statewide`, WI FY2015 + FY2020 blank-gold actions, WI FY2025 ZCTA
   naming, DE FY2026 unenumerated denial, WI FY2002/FY2003 and ND FY1998 gold recall
   gaps (extraction found units gold does not carry).
