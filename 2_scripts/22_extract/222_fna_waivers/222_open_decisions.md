# FNA extraction — open decisions register

Running list of decisions that need Josh's ruling before the panel build (`2224`) can be
trusted. One entry per decision. Entries are **not** deleted when settled — they move to
the SETTLED section with the ruling and the date, so a later reader can tell why the code
does what it does.

Scope: the Claude in-harness extractor (`222_fna_waivers`), Phase 3–4 of the ABAWD FNA
rebuild. Companion docs: `2222_extract_claude_protocol.md` (procedure + per-arm results),
`0_lit/00_abawd_rules/` (rules KB), `2220b_extraction_prompt.txt` (the spec agents read).

Status values: **OPEN** (needs a ruling) · **DEFERRED** (ruled: not now) · **SETTLED**.

Three kinds of content live here.

1. **D-nn entries need a ruling from Josh.** These block or shape `2224`.
2. **Verification checklists** (per run, near the end) are per-document facts to check
   against the source PDF, not decisions; they exist because agents transcribe suspect
   values faithfully rather than correcting them, so the corpus carries known-suspect cells
   that would otherwise only be findable by re-reading free text.
3. **Agent judgment-call / deviation lists** (per run, added 2026-08-14 for SC/AR) record
   every place the spec did not determine the answer and an agent therefore chose, plus any
   protocol deviations. Nothing here needs a ruling on its own, but a call that recurs is
   how a D-nn entry gets born — D-13 came out of one.

Read (3) after any run before trusting its counts: it is where the row-count effects of
"referenced but not adjudicated → no row" are tallied.

---

## OPEN

### D-01 · Partial-statewide grants: enumerate the complement, or hold one unit?

**Opened** 2026-08-14, from the WV v1_5 run (`fe5d1b3c`). **Blocks** `2224` row counts;
**affects** `2220b`.

**The evidence.** `wv-abawd-response-fy2016-b` and `wv-abawd-response-fy2017` are
structurally identical documents: same serial (2150031), statewide EB-trigger grant, and
the same nine counties named as carve-outs (Berkeley, Cabell, Harrison, Jefferson,
Kanawha, Marion, Monongalia, Morgan, Putnam). Each states the approved count — 46 — and
never names the 46. Two blinded agents encoded them incompatibly:

| doc | approved side | the 9 excluded | units |
|---|---|---|---|
| FY2017 | enumerated all 46, derived as (55-county reference − 9 named) | case (c) "never requested", `request_level.notes` only | 46 |
| FY2016-b | one aggregate unit, `name = "West Virginia"`, `area_type = null` | own group, `group_action = withdrawn_by_state` | 10 |

Both agents reasoned explicitly from `2220b` and both flagged the call as a judgment.
The arithmetic is determinate (55 − 9 = 46, matching the document's own count), so this is
not an ambiguity about *what happened* — it is a representation choice the spec does not
make.

**Why the spec is silent.** `2220b` mandates a single state-named unit for
`federal_suspension`, and gives the three-way denied / withdrawn / never-requested
distinction for named areas. Neither covers a **partial-statewide** grant that states an
exact count and names only the complement.

**Options.**
1. **Expand from the reference.** Emit 46 county rows, `qualifying_basis = statewide`,
   `orig_text` flagged as derived-not-printed. Panel gets county-year rows for free.
   Risk: the reference becomes load-bearing for facts the document never printed, and a
   reference error silently becomes a data error.
2. **Hold as one unit.** Emit a single partial-statewide unit plus the 9 named exclusions.
   Faithful to the page. Cost: `2224` must expand it anyway to build a county-year panel,
   so the expansion just moves downstream — but it moves to one deterministic place
   instead of N agents.
3. **Both.** One unit + a schema field carrying the exclusion list and the stated count,
   and `2224` expands deterministically. Most information, one new field.

**Recommendation: (3).** It keeps the extraction faithful, puts the reference-dependent
step in code rather than in agent judgment, and preserves the stated count as a check
(expansion must reproduce 46 or the row errors). Pairs naturally with the
`unit_enumeration` field designed and declined under D-06.

**Magnitude.** 45 panel rows per affected document. WV has at least FY2016-b and FY2017;
sweep the rest of the corpus for the "entire State except" pattern before ruling.

**The WV gold sheet now votes (2026-08-15).** Hand-collected independently of the run, it
encodes the two structurally identical documents the *same* way — enumerated — and so
scores the two agents' incompatible choices directly:

| doc | agent's choice | gold's choice | name score |
|---|---|---|---|
| FY2017 | enumerated 46 | enumerated 46 | **46/46** |
| FY2016-b | one aggregate unit + 9 withdrawn | enumerated 46 (+1 statewide row) | **1/47** |

That single document is **46 of the 49 name misses in the entire WV eval** — without it WV
scores 501/501. So D-01 is not a marginal representation quibble: it is the only thing
separating the v1_5 WV run from a perfect name match, and it is worth ~94% of the state's
apparent error.

Two cautions before reading the vote as a ruling for option (1):
- Gold is **internally inconsistent on exactly this axis**. FY2012 and FY2013 are statewide
  EB-trigger grants and gold holds each as a single `West Virginia` row — the option-(2)
  encoding. The difference is that those documents state no count and name no complement,
  so the enumeration is not derivable; FY2016-b's is. That is a coherent line, but it is a
  line the sheet applies tacitly, not one `2220b` states.
- Gold's FY2016 block carries a statewide row **and** all 46 counties (rows 348–394, both
  under `group_id` 1), i.e. 47 rows for 46 counties. Whatever the ruling, the expansion
  must not also keep the aggregate row or the panel double-counts the state.

This is the human-side evidence the entry was waiting for; the recommendation of option (3)
is unchanged and now has a concrete acceptance test (expansion must reproduce 46, and must
replace rather than accompany the aggregate row).

---

### D-02 · Document supersession: one action, two documents, one voids the other

**Opened** 2026-08-14, from the WV v1_5 run. **Blocks** `2224`.

**The evidence.** `wv-abawd-approval-2018` (dated 2017-12-12) and
`wv-abawd-response-fy2018-b` are the **same waiver action**: serial 2150031, Jan 1 – Dec 31
2018, 46 counties, `joint_aggregate` / `pct20_above_natl`. FY2018-b is explicitly a
"Corrected Approval" replacing the December letter; FNS states the original contained a
processing error that misstated the 46 counties.

The two blinded extractions independently confirm which is wrong. Each agent computed
which member counties fall below the 5.9% threshold. The rate **multisets are identical** —
{4.0, 4.4, 4.6, 4.9, 5.4, 5.4, 5.4, 5.6, 5.6, 5.7, 5.8} — but attached to disjoint names:

| | sub-threshold counties |
|---|---|
| original (`approval-2018`) | Mercer, Grant, Marion, Calhoun, Gilmer, Mason, Pocahontas, Monongalia, Pleasants, Summers, Hampshire |
| corrected (`fy2018-b`) | Pendleton, Hampshire, Monroe, Doddridge, Greenbrier, Ohio, Tucker, Taylor, Preston, Wood, Hardy |

The original assigns rates to **Marion and Monongalia — two of the nine counties the state
excluded from the request**, which independently identifies it as the erroneous letter.
Neither agent knew the other document existed.

**The problem.** Both documents map to the same (serial, coverage interval). Naively
unioning them double-counts 46 counties with contradictory rate assignments. This is a
**different** failure from the WI FY2005 case that `_resolve_multi_doc` handles: there,
two genuinely distinct actions shared a serial and both were valid; here one document
*voids* the other.

**Options.**
1. Detect supersession from text ("corrected", "replaces", "supersedes" + a referenced
   prior date) and set a `superseded_by` / `supersedes` link at extraction time.
2. Curate a small manual supersession table keyed on `document_id`.
3. Latest-response-date-wins within (state, serial, coverage interval).

**Recommendation: (1) with (2) as the backstop.** The trigger language is explicit in this
case and cheap to capture; a curated table catches whatever the language misses. (3) is
tempting but unsafe — a later letter can *amend* rather than *replace*, and the WI FY2005
pair shows that same-serial-later-date does not imply supersession.

**Also worth keeping for the paper.** That the extraction reproduces a documented FNS
clerical error rather than smoothing it over is direct evidence on transcription fidelity.

**Second instance, and a cleaner one (WY, 2026-08-15).** `wy-abawd-response-fy2005` denies
serial 970264 on 2005-03-10; `wy-abawd-response-fy2005-a` approves it on 2005-04-11 and says
so explicitly — "This is a correction to our memorandum dated March 10, 2005, which originally
denied…", the cause being a typographical error in Fremont County's census-share data. Unlike
the WV FY2018 pair, the later letter **names the memo it replaces and the date**, which is
exactly the trigger language option (1) would key on. The WY gold sheet carries one FY2005 row
(approved) and `_resolve_multi_doc` reached it only via the agrees-with-gold tie-break — so on
an ungolded state this shape is currently resolved by chance. See § "Gold-sheet corrections —
WV and WY", item H.

**Two more instances from the UT/LA run (2026-08-15), and the second breaks option (1)'s
assumption that the superseding document describes the superseded one correctly.**

*Third instance, textbook.* `ut-abawd-response-fy2016` states that this approval "**replaces**
the State agency's August 6, 2015 approval" — explicit trigger language plus a referenced prior
date, exactly what option (1) keys on. But the same letter describes the preceding coverage
**two different ways two sentences apart**: once as "Garfield, San Juan, and Wayne Counties"
and once as the August 6 approval "which included only Garfield, Grand, and San Juan Counties."
Neither list matches the four counties this document actually approves (Garfield, Grand, San
Juan, Wayne). The agent carried both through verbatim and did not reconcile them, which is
correct. **The lesson for option (1): a supersession link can be detected from the recital, but
the recital's *content* cannot be trusted to identify what was superseded.** Whatever gets
built must key on the referenced date and serial, never on the recited area list.

**Fifth instance, and the cleanest controlled comparison the corpus will ever offer — a Word
draft and its final PDF, disagreeing on the granted term (2026-08-15).**
`ut-abawd-response-fy1999-a.doc` (the corpus's only non-PDF; see non-decision item 7) and
`ut-abawd-response-fy2000.pdf` are **the same FNS action**: serial 970138, state request
1999-09-30, RO transmittal of response 1999-11-05, the same six counties, the same five
approvals, the same denial of Uintah for falling off the FY1999 LSA list, the same
`criterion_code = lsa` throughout, and even the same `907138` page-header typo and the same
14-months-requested / 1-year-granted mismatch. Two blinded agents, two different source formats
(native Word text vs a scanned PDF), and the emitted JSONs are structurally identical:

| | groups | units | approved | denied | **granted expiry** |
|---|---|---|---|---|---|
| `ut-abawd-response-fy1999-a` (.doc) | 6 | 6 | Duchesne, Emery, San Juan, Garfield, Grand | Uintah | **2000-01-31** |
| `ut-abawd-response-fy2000` (.pdf) | 6 | 6 | *same five* | Uintah | **2001-01-31** |

**The two documents differ in exactly one substantive field, and it is the expiration date.**
A full extra year of coverage for five counties turns on which file is authoritative. The
`.doc`'s own field 8 says the state asked for 14 months expiring 2001-01-31, and the `.doc`
grants "1 year … expires on January 31, 2000" — internally coherent only if the term runs from
Feb 1999. The PDF grants "1 year," same phrase, to 2001-01-31. One of them is wrong, or the
Word file is a draft that was revised before issue.

Three reasons this instance is more useful than the other four. (a) It is a **natural
replication experiment**: same action, same spec, two agents, two formats, and everything
except the disputed field agrees — which is direct evidence on extraction fidelity, of the same
kind as the WV FY2018 rate-multiset finding. (b) It is the first case where the two documents
are filed under **different fiscal years** (`fy1999-a` and `fy2000`), so no FY-keyed or
serial-keyed dedupe will pair them; only a content comparison finds it. (c) The `.doc` is
invisible to the work-list, so under current tooling the corpus would simply carry the PDF and
nobody would know a conflicting version existed. Whatever supersession mechanism D-02 lands on
must be able to compare **near-duplicate documents across fiscal years**, not just follow
explicit "replaces" language — this pair contains no such language in either direction.

*Fourth instance, and a new shape — supersession inside one file.* `la-abawd-response-fy2001`
contains both the superseded and the superseding action in a single PDF: a Waiver Response
denying three areas, then two later FNS documents correcting the threshold arithmetic and
approving the same three. See D-16 for the substance. For this entry the point is structural:
`_resolve_multi_doc` and any `superseded_by` link operate on **pairs of documents**, and this
supersession has no second `document_id` to point at. The extracting agent emitted both the
denied and the approved groups and flagged the choice; the alternative — keep only the final
state — would silently discard a documented FNS reversal. Any supersession design needs an
intra-document case.

---

### D-03 · Null `fiscal_year` on period-named and approval-named files

**Opened** 2026-08-14. **Blocks** nothing today; **will silently drop rows** once WV is
scored or panelled.

**The evidence.** `wv-abawd-approval-2018` carries 46 of the WV run's 607 unit-rows and a
**null `fiscal_year`**. Its filename gives an approval year, not an FY, and the document
itself states only a calendar period (Jan 1 – Dec 31 2018) that straddles FY2018 and
FY2019. `_PERIOD_RE` in `_fy_from_name` keys on a `10.2017-9.2018`-style period string and
does not match `approval-2018`.

**Precedent.** This is the same class as the ND FY2018 bug (`nd-abawd-approval-10.2017-
9.2018`), where a null `fiscal_year` made 9 ND gold units invisible to scoring and they
read as "no extraction JSON" despite a clean extraction. That one was caught only because
ND has a gold sheet. WV has none, so nothing errors today — the rows just vanish from any
`--fys` query.

**Options.**
1. Extend `_fy_from_name` to catch `approval-<year>` and similar.
2. Derive `fiscal_year` from the extracted waiver period rather than the filename, with
   the filename as fallback.
3. Assert loudly: fail collation on any doc whose `fiscal_year` is null.

**Recommendation: (2) + (3).** The period is in the JSON and is the authoritative fact;
the filename is a scraping artifact. (3) is the durable fix — this bug class has now
appeared twice and both times was invisible until something else broke. Note (2) forces
D-04 to be answered, since a calendar-year waiver has no single FY.

**Sweep needed.** Scan the full 1,135-doc manifest for every file whose `fiscal_year`
parses null, not just the two known cases.

**Update 2026-08-14 (KY/GA run).** Two more instances: `ga-abawd-approval-2018` and
`ky-abawd-approval-2018`, both `approval-<year>` filenames over stated calendar-year
coverage (Jan 1 – Dec 31 2018). Between them they carry **166 unit-rows** — GA 66, KY 100 —
that vanish from any `--fys` query. Four instances now (ND FY2018, WV, GA, KY), every one
invisible until something else broke. The `approval-2018` filename shape is clearly
systematic across states, so option (1) alone will keep losing to the next naming variant;
(2) + (3) as recommended.

**Update 2026-08-15 (MO run).** Zero instances in 19 documents / 392 rows — every MO file
uses the `*-response-fy<YYYY>` shape and every row parses. Recorded as a negative datapoint:
the bug tracks the *filename convention*, not the state or the vintage, which is further
evidence for (3) over (1). MO does, however, contain the failure (2) is meant to fix in a
different guise — its FY2007 documents state coverage intervals that a single FY cannot
represent (see D-04) — so a state can be clean on `fiscal_year` parsing and still be
mis-keyed by fiscal year.

**Update 2026-08-15 (UT/LA run) — the `_PERIOD_RE` fix holds, and the residual is the
`approval-<year>` shape alone.** Zero instances in 45 documents / 455 rows. Both period-named
files in this pair — `la-abawd-approval-9.2018-8.2019` and `ut-abawd-approval-10.2017-9.2018` —
parse correctly (FY2019 and FY2018 respectively), which is the ND FY2018 `_PERIOD_RE` repair
working on two new naming variants it was not tuned against. Combined with MO's clean run, the
bug is now confined to the bare `approval-<YYYY>` filenames (ND, WV, GA, KY), and the argument
for (3) — fail loudly on a null `fiscal_year` rather than chase naming variants — is unchanged
and now cheap to adopt, since a corpus-wide assertion would currently fire on a known, bounded
set rather than an unknown one.

**Update 2026-08-15 (MT/SD run) — THE SWEEP IS DONE, and the mechanical half is fixed.**
`mt-abawd-approval-2018` turned up a fifth instance (31 unit-rows), which finally prompted the
corpus-wide scan this entry has asked for since it was opened. **18 documents across 18 states**
parse to a null `fiscal_year`, and the prediction above holds exactly — every one is in the
`FY2015-2019` batch and every one is an `approval-<YYYY>` variant:

| shape | files |
|---|---|
| bare `approval-2018` | AZ, GA, ID, IL, KY, MA, MD, MI, MT, NV, OR, PA, WA, WV |
| bare year, not trailing | CT `approval-2018-revised` |
| bare year behind another number | NY `approval-47-2018`, NY `approval-plus1-2018` |
| period, URL-encoded | NH `approval-10.2017%20-9.2018` — `%20` between the year and the dash defeats `_PERIOD_RE` |

Note the sweep also caught two shapes option (1) would have missed on a first pass (`-revised`
suffix, `47-` prefix) and one that is a `_PERIOD_RE` near-miss rather than a new class.

**Fix applied (option 1, as a stopgap).** `_fy_from_name` now falls back to the **last** plausible
year in the stub, guarded to `199\d|20[0-2]\d` so a serial or a county count can never be read as
a year; `_PERIOD_RE` now tolerates `%20` as whitespace. Corpus-wide null `fiscal_year` is **0 of
1134**, and every pre-existing shape (`*-response-fy<YYYY>`, `10.2017-9.2018`, `fy2003B`) parses
unchanged. `fna_extraction_results.py` does not hash into `run_id`, so no arm was relabelled.

**What is still OPEN.** This is option (1), which the entry above already argues is the weaker
fix, and nothing here changes that argument — it just stops the bleeding on a now-bounded set.
**(2) and (3) remain unruled**, and the case for (3) is stronger than before, not weaker: this
sweep happened because MT tripped the bug by accident, the **fifth** time in five discoveries that
this class surfaced only when something else broke. A null-`fiscal_year` assertion in `collate`
would now fire on nothing, which is the cheapest moment there will ever be to adopt it.

Note also that (1) does not answer D-04's question, it buries it: `mt-abawd-approval-2018` covers
**Jan 1 – Dec 31 2018** and is now keyed FY2018, which is a filename-provenance claim, not a
coverage claim. Every one of these 18 files is a calendar-year approval, so the whole set is
mis-keyed in exactly the way D-04 describes, and now silently rather than visibly.

---

### D-04 · Fiscal year is a lossy key for coverage intervals

**Opened** 2026-08-13 (v1_5 session), reinforced 2026-08-14 and **2026-08-15 (MO run)**.
**Blocks** `2224`.

WV's later waivers run **January–December** (calendar year); WI's run **April–March**.
Neither is a federal fiscal year. Keying the panel on `fiscal_year` forces a lossy
projection of what is really a `(serial, coverage_interval, area)` tuple, and it is what
produced the WI FY2005 collision in the first place. Decide the panel's true key before
`2224` is written, not after.

**MO supplies the case where BOTH candidate keys fail at once (2026-08-15).** All three
Missouri FY2007 documents carry serial **2070002** and are three distinct FNS actions with
three distinct coverage facts:

| doc | signed | coverage granted | action |
|---|---|---|---|
| `mo-…-fy2007-b` | 2006-11-02 | 2006-11-01 → 2007-03-31 (5 months) | approves 8 groups / 21 units |
| `mo-…-fy2007-a` | 2007-01-31 | 2007-04-01 → 2008-03-31 | approves 8 groups / 20 units |
| `mo-…-fy2007` | 2007-02-28 | 2007-04-01 → 2008-03-31 | **modifies** the above: adds Clinton, Montgomery, Schuyler |

`(state, FY)` collapses all three; `(state, serial)` also collapses all three. Note FY2007-b
exists *because* FNS refused to fold a 5-month window into the then-current 2-year waiver
(970129) and opened a new serial for it — i.e. the serial boundary is drawn on the coverage
interval, which is the tuple element the panel actually needs.

The complementary failure is in the other direction: serial **970129** carries every MO
response from FY1998 through FY2006 (**296 unit-rows, nine years**) and **2070002** carries
FY2007→FY2013. Two serials cover the entire state, so a serial-keyed join collapses a decade
while a FY-keyed join splits single actions. This is the AR 980013 pattern (one serial,
FY1999–FY2008) reproduced twice inside one state — it is the norm, not an outlier.

**AL breaks the last assumption the key was still resting on: that a state has ONE live
instrument at a time (2026-08-15).** Alabama runs **970043 (`pct10_statutory`) and 970225
(`lsa`) concurrently for five years**, FY1999–FY2003, and counties move between them as their
own rate crosses 10% (see D-18). Two consequences for the key:

1. `(state, FY)` does not even identify a *rule*, let alone an action — AL FY2001 contains
   both an 11-county 10%-rule adjudication and a 19-county LSA adjudication, on two serials,
   in two separate documents.
2. **Coverage and instrument are separate facts.** A county can be continuously covered while
   the serial covering it changes underneath it. Any key built from `serial` will read that
   continuity as an exit followed by an entry. The panel therefore needs the coverage
   interval as the spine and the serial as an *attribute* of it, not the other way round.

AL FY2016 supplies the ordinary version of the same problem on top: `fy2016-a` and `fy2016-b`
share serial **2150024** but are disjoint actions — `-b` is a statewide 3-month `eb_trigger`
extension (2015-10-01→2015-12-31), `-a` is a 13-county `pct20_above_natl` approval running
**2016-01-01→2016-12-31**, i.e. a calendar year straddling FY2016 and FY2017. Same serial,
same FY label, different scope, different rule, no overlap.

**Louisiana adds the case where one serial's own coverage intervals OVERLAP (2026-08-15).**
Serial **2020121** carries every LA response from FY2002 through FY2009 — and two of those
grants cover the same months:

| doc | signed | coverage granted |
|---|---|---|
| `la-…-fy2004` | 2004-05-14 | 2004-05-01 → 2005-04-30 |
| `la-…-fy2005` | 2005-04-11 | **2004-11-01 → 2005-10-31** |

The FY2005 grant is retroactive to a start date six months inside the FY2004 grant's window,
on the same serial and the same statewide scope. Every prior D-04 case has been *distinct
actions that a key collapses*; this is one instrument whose own intervals are not disjoint, so
even the `(serial, coverage-interval, area)` tuple the entry recommends does not by itself
produce a partition — a (state, month) panel built by unioning intervals will double-count
Nov 2004 → Apr 2005 unless the builder resolves overlaps explicitly. Recommend the panel spec
state a rule (later grant supersedes the overlap, presumably) and assert that post-resolution
intervals are disjoint within a serial.

**Louisiana's serial history also shows a serial being retired mid-stream, with its areas
migrating to another serial AND changing rule.** `la-abawd-response-fy1999` folds the ten
parishes previously covered under **970025** on a `pct10_statutory` basis into **970075** on an
`lsa` basis, in one document, without stating that 970025 is closed. LA's four serials
(970025 → 970075 → 2020121 → 2160020) therefore do not partition the state's history cleanly at
their boundaries. UT is the ordinary case for contrast: two serials, 970138 (FY1998–FY2009) and
2140019 (FY2015–FY2020), with a clean break. Same pattern as AR 980013 and MO 970129, plus a
rule migration on top — which is the IN FY2002 Randolph shape (D-12 item 5) at ten times the
scale, and equally invisible in the emitted data.

---

### D-05 · Gold's `status` vs `group_action`

**Opened** 2026-08-13 (v1_5 session). **Blocks** scoring semantics.

For ND FY2003 Mountrail/Sioux you set `status = approved` while
`group_action = withdrawn_by_state`, which reads as a deliberate split between "was
coverage achieved" and "what did FNS do". The flattener still mirrors `status` from
`group_action` and cannot reproduce that. Either the split is intended — and the flattener
needs a second field — or the gold cell is an artifact.

---

### D-10 · `qualifying_basis = unknown` — preserve or impute?

**Opened** 2026-08-14, from the KY/GA run. **Blocks** `2224` if the panel wants a
unit-level "was this area load-bearing" margin.

**The evidence.** Documents split cleanly into three reporting regimes, and the split is
chronological — the later the document, the less it prints:

| what the document prints | agents can determine | example docs |
|---|---|---|
| per-unit rates | `own_rate` / `carried_by_group` exactly | GA FY2005/2006, KY FY2007 |
| per-unit *counts* only (unemployed + labor force) | same, by division — and the derived total reproduces the document's own printed combined rate exactly | GA FY2017, KY FY2017, KY `approval-2018`, GA `approval-2018` |
| a set-level rate only | **nothing** | GA FY2020-b, FY2023; KY FY2023, FY2024, FY2025 |

Agents in the third regime correctly wrote `unknown` rather than defaulting to
`carried_by_group`. Result: 702 of ~2,517 unit-rows (GA 348, KY 354) are `unknown`.

**Why it matters.** `carried_by_group` is the revealed-preference quantity — it is the
count of areas a state pulled *into* a bundle that could not have qualified alone. Imputing
it where the document is silent would manufacture exactly the variable the paper measures.
But leaving it null means the margin is only computable on a non-random subsample: the
older, more verbose documents.

**Options.**
1. Preserve `unknown` as a distinct third state; compute the carried-in margin only on the
   determinable subsample and report the coverage rate alongside it.
2. Impute from external BLS/LAUS primitives — the county-month series is public, so the
   rate is recoverable independently of what FNS chose to print.
3. Treat set membership itself as the outcome and drop the carried/own distinction.

**Recommendation: (1) now, (2) as the real fix.** (2) is the same BLS-primitives merge
already contemplated under D-09, and it would close this on the entire corpus rather than
the talkative half. Until then `unknown` must not be silently collapsed into either
category. Note the selection direction: silence correlates with recency, so a
determinable-only analysis is tilted toward pre-2015 documents.

**MO confirms the recency story and exposes a second, cleaner convention (2026-08-15).**
Missouri returns **zero** `unknown` rows in 392 — the only state so far with none — because
its documents run FY1998–FY2008 for all the sub-state work and print per-county rates
throughout (224 of 392 rows carry a unit rate; the remainder are LSA rows, where the
designation *is* the basis and no rate is needed). That is the pre-2015 end of the same
selection gradient GA/KY sit at the other end of.

The second finding is a convention worth ratifying: MO's 10 null `qualifying_basis` rows are
**exactly** its 10 non-approved rows (3 `rejected` in FY2002, 7 `withdrawn_by_state` in
FY2005/FY2006). Both agents reasoned that an area never adjudicated on the merits has no
qualifying basis to record. That is coherent and it keeps the carried-vs-own denominator
clean — but it means `qualifying_basis IS NULL` currently carries two meanings corpus-wide
("not adjudicated" here, plain absence elsewhere) and is not the same as `unknown` ("the
document does not let us tell"). **Confirm null-on-non-approval as the intended rule and
state it in `2220b`**, otherwise `2224` cannot distinguish the three states, and the D-10
margin will silently include withdrawn areas as denominator zeros.

---

### D-11 · A "contiguous" claim the adjacency reference refutes

**Opened** 2026-08-14, from the KY/GA run. **Blocks** nothing; **evidence to reopen D-09.**

**The evidence.** KY FY2016-b describes Ballard, Fulton, Graves and Hickman as "four
contiguous counties." Per `ky_geo_context.md`, Ballard adjoins only Carlisle and McCracken;
Carlisle is the connector and is **not** in the set. Fulton–Hickman–Graves form a chain,
Ballard is isolated from it. The bundle as drawn is disconnected.

**Why it is new.** Every prior geo-context catch was orthographic (`Pasguotank`→Pasquotank,
`Rookcastle`→Rockcastle, `Mcintosh`→McIntosh). This is the first time the reference
contradicts a substantive factual assertion by the state, and contiguity is not decorative —
the 2016 rule conditions bundling on it.

**The problem.** The agent did the right thing (kept the bundle as printed, recorded the
tension in `qualification_level_evidence`), but that field is free text. The fact is
therefore unqueryable: a sweep for "how often do states assert contiguity that fails?"
cannot be run over the corpus.

**Options.**
1. Build the deferred `bundle_contiguous` schema field (designed and deferred under D-09),
   set from the adjacency lists at extraction time.
2. Compute contiguity deterministically in `2224` from the extracted unit lists + adjacency
   data — no schema change, no agent judgment.
3. Leave as free text.

**Recommendation: (2).** The unit list and the adjacency graph are both already in hand, so
contiguity is a pure derivation — the same argument that moved `federal_suspension_in_force`
out of `criterion_code` under S-1. Asking 60+ agents to re-derive a graph property invites
exactly the inconsistency that rule was written to stop. Worth a corpus-wide sweep once
built: a state asserting contiguity it does not have is itself a finding.

**A second failure mode, from the SC/AR run (2026-08-14) — the splitting rule manufactures
discontinuity.** AR FY2008 describes its set as contiguous and the *full* 73-county area is;
but the splitting rule separates 42 individually-qualifying counties into per_unit groups,
and the residual 31-county `joint_aggregate` group is internally disconnected (Craighead's
in-state neighbours all sit in the other group). The document is right and the emitted group
is not. AR FY2002's scattered 19-county group is the ordinary KY FY2016-b case.

**Consequence for the design.** `bundle_contiguous` computed on the emitted group is
meaningless wherever a document splits one stated set across groups. Whichever option is
chosen, the derivation has to run against the document's stated set — which means `2224`
needs to know which units were split away, i.e. a stable "this group came from that printed
set" link that the schema does not currently carry.

**MO is the clean negative control (2026-08-15) — and it separates contiguity from labels.**
Every one of MO's 22 `joint_aggregate` bundles checked contiguous against
`mo_geo_context.md`, including the largest (FY2008's 17-county Upper Southeast set and
FY2004's 10-county Bootheel). No new D-11 instance in 19 documents. What MO *does* add is
the distinction the sweep will have to make: the "Sub-region of **Greater St. Louis** Region"
appears in three documents containing only Crawford, Gasconade and (later) Montgomery — all
well southwest of St. Louis, none adjacent to the city or the county. Three independent
agents each checked this, found the members mutually adjacent, and correctly declined to
flag it, recording that the name is a MERIC planning-region label rather than a proximity
claim. A deterministic contiguity check per option (2) gets this right automatically; an
agent- or name-driven check would produce three false positives here. Argues for (2).

**UT/LA add the two failure modes a boolean `bundle_contiguous` cannot express (2026-08-15).**

*1. Contiguous but not compact — LA FY2024.* The 33-parish bundle **is** one connected
component under the adjacency lists; the agent traced the full chain. But the chain threads
from the far north (Bienville / Claiborne / Winn) down to Orleans / Plaquemines / St. Bernard
through a narrow winding path, omitting whole contiguous blocks in between (the I-49 corridor,
Baton Rouge, the Acadiana core, southwest Louisiana). It passes a contiguity test and looks
nothing like an economic region. A boolean would record `true` and conceal the most interesting
thing about the set. If the point of the check is to detect constructed bundles, **compactness
(or a perimeter-to-area / diameter measure) carries the signal that connectedness does not** —
and it is equally deterministic from the same adjacency data.

*2. The document's own prose contradicts its own tables — UT FY2006.* Fields 8 and 9 describe
all ten approved areas as "part of a contiguous sub-region" with "an aggregate average
unemployment rate." The tables below split them into two named AOG sets with printed totals
plus four areas with no set total at all, and two of the ten (Ogden city in Weber County, West
Valley City in Salt Lake County) are nowhere near the southern cluster or each other. The agent
used the table structure *and* the adjacency lists to emit six groups rather than honour the
prose, and recorded the tension. That is a different case from KY FY2016-b (state asserts
contiguity the reference refutes) and from AR FY2008 (the splitting rule manufactures the
discontinuity): here the **summary field over-generalises what the document's own detail
says**, and geography is what reveals it. Note UT FY2007 has the same over-generalising
summary field ("all six areas qualify via aggregate rates" when two are LSA-only with no rate
printed), so this is a recurring property of field 9 on this form vintage, not a one-off.

Both argue for option (2) — compute it in `2224` from the extracted unit lists — and item 1
argues that what gets computed should be richer than a boolean.

**Update 2026-08-15 (MT/SD run) — a fresh state-asserts-contiguity instance, plus a limit on
where option (2) can run at all.**

*1. MT FY2017.* The state calls its 5-county bundle (Big Horn, Petroleum, Prairie, Rosebud,
Treasure) "contiguous"; per the adjacency lists **Prairie borders none of the other four**. Same
shape as KY FY2016-b. The agent kept the set as drawn and flagged the tension rather than
splitting Prairie out, which is the correct behaviour under the current spec and is also why the
disagreement survives into the data where `2224` can act on it.

*2. The check is unperformable on reservations — a constraint on option (2), not on the ruling.*
Neither `mt_geo_context.md` nor `sd_geo_context.md` maps reservations to parent counties or gives
reservation adjacency, so for any bundle whose members are reservations there is **no adjacency
data to compute against**. The SD FY2022 agent hit this and said so explicitly instead of
guessing. This pair is 289 reservation-area unit-rows, so it is not a corner: whatever `2224`
computes will be null for a large and *non-random* slice — the tribal geographies — unless the
geo-context build is extended. That is a build task, not a decision, and it is recorded as a
non-decision item in the MT/SD checklist; but it does mean option (2) silently returns "unknown"
exactly where D-14's containment question is hardest.

---

### D-12 · An area dropped from a prior waiver is coded three incompatible ways

**Opened** 2026-08-14, from the KY/GA run. **Blocks** `2224`; **affects** `2220b`.
**Highest-priority item from that run** — it changes approval-rate denominators directly.

**The evidence.** "Area was in the prior waiver, is not in this one" is the single most
common non-approval event in the corpus. Blinded agents encoded it three ways:

| coding | documents | groups emitted |
|---|---|---|
| `denied` groups | GA FY1998 (4), GA FY2000 (4) | 8 |
| `withdrawn_by_state` groups | GA FY2002 (8), KY FY2002 (5) | 13 |
| **no group at all**, `request_level.notes` only | KY FY1999 (3), KY FY2000 (10), KY FY2001 (20), KY FY2003 (3), GA FY1999 (1), GA FY2001 (7) | 0 (≈44 areas) |

All three cite `2220b`. The facts are near-identical across the three rows — an area lost
its LSA designation, or the state chose not to renew it, and it silently leaves the waiver.

**Why the spec permits all three.** S-4 gave the denied / withdrawn / never-requested
three-way distinction, but it was written from ND FY2003, where the state *stated* its
alternative-coverage plan (273.24(g) exemptions). In the far more common case the document
says only "the State is not requesting an extension for X" or "X is no longer designated,"
which fits case (b) *and* case (c) on a plain reading, and reads as (a) to an agent who
treats FNS's affirmative "removed from waiver" language as a decision.

**Why it matters more than it looks.** ≈44 areas currently produce **no row at all**. If
the panel measures the approval margin, those are dropped observations, not zeros — and
they are dropped non-randomly, concentrated in KY (36 of 44). A state quietly declining to
re-request a county it previously held is close to the purest revealed-preference signal in
the corpus, and right now it is the one event with no representation in the data.

**Not to be conflated.** KY FY1998-b's 2 `denied` groups *are* genuine merits denials —
FNS refused to extend a city-level LSA waiver to the whole county on a stated
population-dominance rationale (69.5% / 48.4%). That is case (a) correctly applied and
should stay `denied`. The test is whether FNS adjudicated, not whether the area vanished.

**Options.**
1. **Always emit a group.** Add a `not_renewed` / `lapsed` `group_action` value covering
   "in the prior waiver, absent from this one, no FNS adjudication." Every area gets a row;
   the reason lives in the action, not in prose.
2. **Never emit a group**; standardise on case (c) and require a structured
   `areas_not_renewed[]` list at request level so the fact is at least queryable.
3. Tighten `2220b`'s trigger phrases so agents route to (b) vs (c) consistently, leaving the
   representation as is.

**Recommendation: (1).** It is the only option under which the count of areas a state
declined to re-request is recoverable by a `GROUP BY` rather than by re-reading 44 free-text
notes. It also composes with D-10: a `not_renewed` row needs no `qualifying_basis`, so it
does not pollute the carried-vs-own margin. (3) alone leaves ≈44 areas unrepresented and
merely makes the omission consistent.

**Sweep needed before ruling.** Count the "not requesting an extension" / "no longer
designated" pattern across the whole corpus, not just KY/GA — this is a recurring FNS form
phrase and the totals will be much larger than 44.

**Confirmed outside KY/GA (SC/AR run, 2026-08-14).** AR FY2006 drops ~15 counties from the
original 42-county DRA request, SC FY2000 drops 7 previously-LSA areas, SC FY2003-b drops
3–4, and AR FY2004 leaves Perry County requested but never adjudicated — all `notes` only,
no rows. The sharpest evidence is *within* one state's own series: SC FY1999 emits two
`denied` groups (Colleton, Edgefield) for the identical "no longer qualifies as an LSA"
fact that SC FY2000 records as prose a year later, same form, same office. That rules out
"the documents differ" as the explanation — the spec does.

**MO is now the strongest single-state case (2026-08-15) — both codings, one serial, one
decade.** Serial 970129 runs FY1998→FY2006 and the same event is encoded two ways inside it:

| coding | documents | areas |
|---|---|---|
| `withdrawn_by_state` groups | FY2005 (Kansas City as an individual LSA candidate; a 4-county-plus-city "cluster" the state pulled by e-mail 2005-04-12), FY2006 (Henry County) | 7 rows |
| **no group at all**, `request_level.notes` only | FY1999 (6 counties that lost LSA status), FY2000 (5: Camden, Carter, Laclede, Ripley, Buchanan-via-St.-Joseph), FY2001-a (7 removed from the prior waiver) | ≈18 areas, 0 rows |

Same state, same office, same waiver serial, same underlying fact — an area that was covered
last year is not covered this year. What separates the two codings is only whether the
document happens to attribute the removal to a state act ("the State withdrew", "eliminated
by e-mail") or to a lapse in designation. That distinction is real but it is *not* the
distinction the spec's three-way rule turns on, and it leaves ~18 of MO's dropped areas with
no representation while 7 get rows.

**AL reproduces the split in adjacent years of one serial (2026-08-15).** Waiver 970225's
FY2001 response drops **7** counties — 3 that fell off the DOL LSA list (Lawrence, Talladega,
Winston) and 4 the state affirmatively chose not to renew though still LSA-eligible (Marengo,
Perry, Pickens, Sumter) — and the agent coded **all 7 as case (c), no group**. The FY2002
response drops **3** (Bullock, Clarke, Escambia) on the same form, in the same words ("is not
requesting an extension"), and that agent emitted **3 `withdrawn_by_state` groups**. Same
serial, same office, consecutive years, both codings.

What AL adds beyond MO is that its FY2001 document **distinguishes the two sub-cases in
prose** — designation lapsed vs. state declined to renew — and the encoding collapses them
anyway, because case (c) has no row to carry the distinction. That is the sharpest available
argument for option (1): the document supplies the very field a `not_renewed` /
`lapsed_designation` split would need, and the current schema discards it.

**Do not conflate AL's transfers with D-12.** Alabama's 8 `rejected` rows from FY1999–2001
look like dropped areas and are not — coverage continues under a sibling serial. That is
**D-18**, a distinct entry opened by this run.

**Corpus running total for the sweep.** ≈44 areas (KY/GA) + ~25 (SC/AR) + ~18 (MO) + ~10 (AL)
≈ **97 areas with no row**, before the KS/NE/MS, IN and pilot states are counted. The sweep
called for above is now clearly the blocking task, not an optional check.

**UT/LA supply the two sharpest instances the entry will get: the same COUNTY coded both ways
within one serial, and both codings inside a SINGLE document (2026-08-15).**

*Same county, same serial, two codings.* Utah's waiver **970138** contains Uintah County
throughout, and the two documents that drop it disagree:

| doc | the fact | coded |
|---|---|---|
| UT FY2000 | Uintah was in the six-county request; FNS finds it absent from the FY2000 DOL LSA list and "does not include Uintah County," inviting further data | **`denied` group**, `qualifying_basis = null` |
| UT FY2002 | Uintah and Wayne held FY2001 LSA status and are simply absent from the FY2002 approval | **no group**, `request_level.notes` only |

Every prior instance of this split has been same-state or same-serial. This is the same
**county**, on the same serial, two years apart, on the same underlying fact — a DOL
designation lapsing. It removes the last reading under which the codings might be tracking some
genuine difference between the areas involved.

*Both codings inside one document.* `la-abawd-response-fy1999` drops four areas and encodes
them two ways in a single letter, and the agent stated the distinguishing rule it used:

| area | the document's words | coded |
|---|---|---|
| Acadia Parish | "the State agency does not wish a continuation" | **`withdrawn_by_state` group** |
| Ascension, West Baton Rouge | "no longer qualify as LSAs" | **no group**, notes only |
| Bossier City | newly requested in field 8, absent from field 9's approved list, never mentioned again | **no group**, flagged as unexplained |

That is exactly the split AL FY2001 made *in prose* and could not carry in the schema — state
choice versus designation lapse — arriving here as two different `group_action` outcomes for
the same class of event, decided purely by which verb the letter happened to use. And Bossier
City is a third thing again: requested and then silently unadjudicated, the AR FY2004 Perry
County shape.

The AL argument for option (1) was that the document supplies the distinction the schema
discards. LA FY1999 is the stronger version: the document supplies it, one agent acted on it,
and the result is that two areas dropped in the same paragraph land in different tables.

**Corpus running total for the sweep.** ≈44 (KY/GA) + ~25 (SC/AR) + ~18 (MO) + ~10 (AL) + **~7
(UT/LA: Uintah, Wayne, Ascension, West Baton Rouge, Bossier City, and LA FY2001's Shreveport /
New Iberia city ambiguity)** ≈ **104 areas with no row**, before the pilot states are counted.

---

### D-13 · "Insufficient jobs" → `lsa` or `other`?

**Opened** 2026-08-14, from the SC/AR run. **Blocks** nothing; **affects** `2220b` and the
criterion denominator in every pre-2006 state.

**The evidence.** "Insufficient jobs" is the statutory prong at FSA §6(o)(4)(A)(ii); LSA
designation is one operational route to satisfying it, but the phrase also appears alone.
Blinded agents split:

| coding | documents | agent's stated reason |
|---|---|---|
| `lsa` | SC FY1998, FY1999, FY2000, FY2001, FY2002-a, FY2003-b | the document itself defines "insufficient jobs" as LSA designation, and names the FY's DOL LSA list |
| `other` | AR FY2000 (Conway County) | the document says "insufficient jobs" with no LSA tie; the only number offered is a *projected* 10.6% from a plant-closing amendment, not a designation |

Both cite `2220b`, and on their own documents both look right. The SC agents are reading a
form whose heading and body are explicitly tied together; the AR agent is refusing to
promote a bare statutory phrase into a designation the document never claims.

**Why the spec is silent.** `2220b` gives `lsa` as a criterion code and the rules KB
correctly describes LSA as the operational route, but neither says what to do when a
document invokes the *parent prong* without the route. The result is that `lsa` counts are
not comparable across states: SC's 100 `LSA` unit-rows and AR's 161 rest on different
evidentiary standards.

**Note the asymmetry with the `federal_suspension` ruling (S-1).** That rule says code the
narrow thing only when the *disposition rests on it*. Applied here, the same logic gives
`lsa` only when the document names a designation, and `other` (or a new
`insufficient_jobs_unspecified`) when it does not — which is the AR agent's reading.

**Options.**
1. **`lsa` only on a stated designation**; bare "insufficient jobs" → `other` with the
   verbatim in `criterion_other_explanation`. Consistent with S-1.
2. **Treat the phrase as `lsa` by default** in the pre-2006 era, when LSA was the only live
   route to that prong. Fewer `other` rows, but it asserts a designation the page lacks.
3. Add a distinct `insufficient_jobs_unspecified` code so the ambiguous cell is visible
   rather than absorbed into the `other` catch-all.

**Recommendation: (3), falling back to (1).** `other` is already a mixed bag, and this is a
recurring FNS form phrase, not a one-off — a named code makes the "we could not tell which
route" population countable, which is the same argument that carried D-10's `unknown`. Cheap
either way: the distinction is mechanical (does the document name a designation?), so it
needs a one-line rule in `2220b`, not agent judgment.

**AL confirms the mechanical test works, on the SC side of the split (2026-08-15).** AL
FY2003-b prints the bare statutory phrase in field 9 ("approved based on insufficient jobs")
and the "does not have a sufficient number of jobs" boilerplate in field 10, but names LSA
designation as the basis in field 8. The agent coded `lsa`, reasoning that the statutory
phrase is the umbrella under which LSA sits rather than a competing criterion. That is
option (1) applied correctly and unprompted — the presence of a named designation elsewhere
on the form settled it. Two AL FY1999/FY2000 documents show the same field-8-names-LSA /
field-9-recites-statute layout, so this is the FNS form's standard construction, not an AL
quirk: **the form itself routinely prints the parent prong in the decision field and the
route in the request field.** That is a strong argument that the rule should key on the whole
document, not on the criterion field alone, and it lowers the expected size of the genuinely
ambiguous population that option (3)'s new code would hold.

---

### D-14 · Containment qualification: does an area inside a designated area get its own group?

**Opened** 2026-08-14, from the KS/NE/MS run (`fe5d1b3c`). **Blocks** group counts and any
per-area revealed-preference measure; **affects** `2220b`.

**The evidence.** Nebraska is the cleanest natural experiment in the corpus for this: waiver
serial **970152** runs FY1998→FY2013 and every document states the same fact in nearly the
same sentence — the Omaha and Winnebago Reservations are exempted **because Thurston County
holds a DOL LSA designation** and the reservations sit almost wholly inside it. Eight blinded
agents, one shared fact pattern, three incompatible encodings:

| coding | documents | units | agent's stated reason |
|---|---|---|---|
| two `per_unit` groups, both `own_designation` | FY1999, FY2000, FY2004, FY2006, FY2008, FY2011-a | 2 | LSA is a per-area designation; "one area's designation cannot depend on another's" |
| one `joint_aggregate` group, both `unknown` | FY1998 | 2 | the document prints ONE combined statistic (99% of the two reservations' population is in Thurston) with no per-reservation breakdown |
| one `joint_aggregate` group, county `own_designation` + reservations `carried_by_group` | FY2013-a | 3 | only the COUNTY holds a designation; the reservations are explicitly included by containment, not by their own DOL finding |

All three cite `2220b`, and each is defensible on its own page. The FY2013-a agent's reading
is the one that matches the documents' actual logic — no reservation is ever DOL-designated
in this series — but it is the minority coding, so the panel would read seven years of
`own_designation` and one of `carried_by_group` for an unchanged legal fact.

**Why the spec is silent.** `2220b`'s LSA rule says a list of LSA-designated areas states N
independent facts, not one joint finding. That rule is right for a list of *designated*
areas. It says nothing about an area that is **not itself designated** and rides on a
containing area's designation — which is neither an aggregate rate (so `joint_aggregate`
misdescribes it) nor an independent designation (so `per_unit`/`own_designation` asserts a
DOL finding that does not exist).

**Scale.** All 25 NE unit-rows in this run. The shape is not NE-specific: it is the same
relation as a city inside an LSA-designated county (KS Wichita/Sedgwick, Hutchinson/Reno),
and MS's 47- and 48-county LSA lists are the *contrasting* case where each unit really is
separately designated.

**Options.**
1. **`qualifying_basis = carried_by_group` whenever the designation is held by a containing
   area, keeping one group.** Uses machinery that already exists (D-10's vocabulary) and
   records the true dependency. Group counts drop for this shape.
2. **Per-area groups with a new `qualifying_basis = carried_by_containment`.** Keeps the
   one-group-per-area convention; distinguishes containment from rate-aggregation, which
   `carried_by_group` currently conflates.
3. Leave to agent judgment (status quo) — rejected; the table above is what that produces.

**Recommendation: (2).** Containment and rate-aggregation are different mechanisms with
different implications for the panel — a carried-by-rate unit would lose coverage if the
bundle were split, a carried-by-containment unit would not — and `carried_by_group` already
means the first. One new enum value plus a two-sentence rule in `2220b` makes the whole
class countable, and it is mechanical to apply (does the document name a designation for
THIS area, or for an area containing it?).

**The relation runs in three directions, not one (MO run, 2026-08-15).** Missouri supplies
the mirror image of Nebraska: **Buchanan County is approved because St. Joseph *city*, which
sits inside it, holds the LSA designation** — the FY1998-b and FY1999 letters call this "the
expansion of a partial county LSA" and justify it with 1990 census data putting 86.4–87% of
the county's population in the city. The container qualifies via the contained. Set against
the two shapes already on record:

| direction | case | who is designated | who gets coverage |
|---|---|---|---|
| contained ← container | NE Omaha/Winnebago Reservations via Thurston County | container | contained |
| **container ← contained** | **MO Buchanan County via St. Joseph city** | **contained** | **container** |
| container denied, contained approved | IN Lake County denied while East Chicago, Gary, Hammond approved | contained only | contained only |

Both MO agents reached the same encoding independently (`lsa` / `per_unit` /
`own_designation`) and both stated in their reports that no enum value fits — the same
complaint the NE agents made from the opposite direction. **This strengthens option (2) and
changes its wording:** a `carried_by_containment` value defined as "qualifies via the
containment relation with a designated area" covers all three rows above, whereas any value
phrased as "inherits from the containing area" covers only the first. The third row is also a
warning for `2224` independent of the enum — Indiana shows the disposition does *not*
propagate along containment in either direction, so a panel builder must never assign a
county's action down to its cities or up from them.

**Note the volume is small but the leverage is not.** MO contributes 2 unit-rows here against
NE's 25, but Buchanan is the difference between a county-year being covered and not, and the
same relation governs every city-inside-an-LSA-county row in the corpus (KS Wichita/Sedgwick,
Hutchinson/Reno; MO St. Joseph; the LAUS-city states generally).

**Louisiana adds a fourth direction: the container is covered EXCEPT for the contained
(2026-08-15).** `la-abawd-response-fy2000` approves "Bossier (except for Bossier City)" — the
parish holds the LSA designation, the city inside it does not qualify this cycle and is carved
out. The agent emitted one unit with `area_type = balance of county`, `balance_of_county =
true`, reasoning that dropping the parenthetical would silently erase a printed exclusion and
inventing a second Bossier City unit would assert an adjudication the letter does not make.
Set against the three directions already on record:

| direction | case | who is designated | who gets coverage |
|---|---|---|---|
| contained ← container | NE reservations via Thurston County | container | contained |
| container ← contained | MO Buchanan County via St. Joseph city | contained | container |
| container denied, contained approved | IN Lake County vs East Chicago / Gary / Hammond | contained only | contained only |
| **container approved, contained carved out** | **LA Bossier Parish except Bossier City** | **container** | **container minus contained** |

The fourth row is the one a `carried_by_containment` value does **not** cover, because nothing
is carried — it is a *subtraction*. The corpus already has the machinery (`balance_of_county`),
so the point is not a new enum value but a consistency one: `2224` must treat a
balance-of-county unit as strictly smaller than the county, and must not let a county-level
join re-absorb the excluded city. Louisiana makes this concrete twice more in the same series
(LA FY1999 records the prior year's Bossier approval as "including Shreveport City and
excluding Bossier City," a carve-out the FY1999 letter then does not repeat), so the
subtraction is not stable across years either — a parish can be whole one year and
balance-of-county the next, which a county-year panel will read as a boundary change.

**Update 2026-08-15 (MT/SD run) — a fifth direction, and by far the largest evidence base:
BOTH areas approved independently, over the same ground.**

South Dakota supplies **221 flagged unit-rows** in a single state — against 24 for MT and
essentially zero across UT/LA — and they are overwhelmingly one relation the table above does not
have a row for: a reservation approved as its own unit whose territory **is** one or more counties
approved separately *in the same document*, each on its own stated basis, with the document never
acknowledging the overlap.

| case | reservation | coextensive counties, also approved |
|---|---|---|
| SD FY2025 | Crow Creek | Buffalo |
| SD FY2025 | Cheyenne River | Dewey, Ziebach |
| SD FY2025 | Pine Ridge | Oglala Lakota, Bennett |
| SD FY2011 | Pine Ridge | Bennett, Jackson, Shannon |
| SD FY2012 | Pine Ridge | Jackson, Shannon |
| SD FY2008 | 12 counties requested a *second* time as reservation-area groups | Corson, Dewey, Walworth, Ziebach, Bennett, Jackson, Mellette, Shannon, Todd, Buffalo, Hyde, Lyman |

Add the fifth direction to the table:

| direction | case | who is designated | who gets coverage |
|---|---|---|---|
| **both, independently, same ground** | **SD reservations vs their own counties** | **both** | **both — counted twice** |

**Why this is not just another `possible_double_counting` flag.** Every agent set the flag *and*
wrote in `double_counting_note` that this is not the schema's core case (the same unit named
twice) — these are distinctly-named units with distinct stated bases. The flag is doing duty for
a relation it was not defined for, which means it cannot currently be distinguished from a true
name-duplication by query. And the two readings differ materially for the panel: if the county
grant and the reservation grant are the *same* coverage event recorded twice, a unit-count
overstates SD's waiver activity by roughly a third; if they are genuinely independent grants
(plausible — they rest on different data and can be decided differently), then they are two
events and the reservation is the finer geography.

SD FY2002 shows the state itself resolving it the other way in the one document that bothers to:
Bennett and Marshall are split into a reservation portion **and** an explicit "remainder of"
carve-out, i.e. D-14's fourth (subtraction) direction, non-overlapping and clean. That is the
only such treatment in 30 SD documents — evidence the overlap elsewhere is an artifact of how the
request was drafted rather than a considered dual grant.

**Relation to the rest of the entry.** D-14 asks how the *contained unit* should be coded.
This asks what `2224` should do when both units are coded and both are approved — a question
about the panel join, not the extraction. They should be ruled together, because
`carried_by_containment` (the recommendation above) presumes the container's designation is what
the contained area rides on, and here the contained area has its own. Note also that the
adjacency data needed to even *detect* these overlaps mechanically does not exist in the
geo-context files (see D-11's update), so today this relation is discoverable only from agent
free text.

---

### D-15 · A disposition that is neither approved, denied, nor withdrawn: deferred to a later letter

**Opened** 2026-08-14, from the KS/NE/MS run. **Blocks** `2224` action coding; **affects**
`2220c` (`group_action` enum).

**The evidence.** `ms-abawd-response-fy2023` requests 16 counties. FNS approves the 14-county
Delta bundle under the 20% rule and, for **Monroe and Montgomery** (requested on a March 26
2023 Stafford Act disaster declaration), states it asked for additional justification on
June 13 2023 and **will decide in a separate letter**. The agent emitted a second group with
`group_action = null` rather than force one of the enum values, and said so.

That is the right call under the current schema and the wrong record for the panel: `null`
is also what a state-request-only document produces (KS FY2013, MS FY2011, MS FY2013 in this
same run), so "FNS explicitly deferred" and "no FNS action is present in this document" are
indistinguishable in the flat file — 4 null-action rows here, two causes.

**MO adds two more of the second cause (2026-08-15).** FY2011 and FY2012 each produce one
statewide `group_action = null` row for the "no FNS action in this document" reason. Note
what this does to option (3): MO now has null-action rows whose `document_type` is
`state_request_only` (FY2011, FY2012) sitting in the same state as a `full_application` whose
action is `approved` (FY2013) — so the `document_type` fallback still resolves cleanly here.
It is the MS FY2023 shape (`null` + `fns_response_only`) that (3) has to lean on, and MO
supplies no counterexample to it. The recommendation is unchanged, but the evidence that (3)
*works on today's corpus* is now stronger, which makes the case for (2) rest squarely on the
robustness argument rather than on present breakage.

**Relation to existing entries.** D-05 already separates gold's `status` from `group_action`;
this is a third state that neither carries. It is *not* D-06 (those groups have a decided
action and no enumerable units); here the units are named and the action is what is missing.
It is also the counterpart to the v1_5 `moot`/`not_required` shape (the ARRA "no longer
necessary" letters) that was noted as load-bearing against gold and never added.

**Options.**
1. **Add `deferred` to the `group_action` enum**, distinct from `null`.
2. **Add both `deferred` and `moot`/`not_required`**, closing this and the standing WI FY2009
   residual in one schema bump.
3. Leave `null` and recover the distinction downstream from `document_type` (`null` +
   `fns_response_only` ⇒ deferred; `null` + `state_request_only` ⇒ no action present).

**Recommendation: (2).** Option (3) works on today's corpus but is a rule about a rule — it
breaks the first time an FNS response defers one group and is silent on another. Both values
are already evidenced by real documents, and `group_action` is the field the panel's
dependent variable is built from, so ambiguity there is the most expensive kind.

---

### D-16 · Which criterion does a DENIED group carry — the requested one or the dispositive one?

**Opened** 2026-08-14, from the IN run. **Blocks** `2224` criterion mix on denied rows;
**affects** `2220b`.

**The evidence.** `in-abawd-response-fy2004` denies two areas that were *requested* on one
theory and *denied* on another. Portage City was requested as a city on the DOL LSA list;
Lake County was requested via inclusion in the multi-state **Chicago labor market area**. FNS
rejected both LSA theories, then independently ran the 20%-above-national test as a backstop
and denied both on that arithmetic (Portage 5.8%, Lake 6.1%, against the applicable
threshold). The agent coded `criterion_code = lsa` for both — matching how each was
requested — recorded the 20% computation in `local_unemployment`, spelled the dual reasoning
out in `criteria_summary_text`, and explicitly flagged `pct20_above_natl` as the defensible
alternative.

The same shape appears wherever FNS recomputes rather than accepts: AR FY2005 rejects the
state's DRA "insufficient jobs" documentation and approves the same 42-county set under the
20% rule instead; AR FY2005 and AR FY2002 deny Columbia and Stone Counties on FNS's own
arithmetic; IN FY2005 rejects the state's *averaging method* outright. In every one of these
the requested criterion and the dispositive criterion differ.

**Why the spec is silent.** `2220b` tells an agent how to *recognise* a criterion from the
document's rule language. It does not say whose rule language governs when the state's and
FNS's differ — and on a denial they differ by construction, because the denial is FNS
refusing the state's theory.

**Why it matters.** The panel's revealed-preference content lives in what states *asked
for*; the panel's outcome variable lives in what FNS *did*. Collapsing both onto one
`criterion_code` field forces a choice that erases one of them. It is currently 5 rejected
rows in IN, but it governs every denial in the corpus and every future FNS-recomputes case.

**Options.**
1. **Requested criterion.** `criterion_code` always records the theory the state advanced.
   Preserves revealed preference; loses the basis of the decision.
2. **Dispositive criterion.** `criterion_code` records the rule that actually produced the
   outcome. Preserves the decision; loses what was asked.
3. **Both.** Add `criterion_code_requested` alongside `criterion_code`, populated only when
   they differ. Two fields, no loss, and the *divergence itself* becomes queryable — which is
   exactly the "decision rule contested" event flagged as paper-worthy in the SC/AR and IN
   writeups.

**Recommendation: (3).** The cases where the two diverge are a small, identifiable, and
substantively interesting subset — FNS refusing a state's theory is the sharpest evidence in
the corpus that the rule is contested rather than mechanical. Options (1) and (2) both throw
that away to save a column. Note this interacts with the two-label tie-break (D-nn candidate
in the IN judgment-call list, item B14): neither has a dedicated field, and a single
`criterion_*` redesign should settle both.

**MO's three denials are the converging case, and they sharpen the option-(3) design
(2026-08-15).** MO FY2002 denies Bates, Caldwell and Chariton — added to the request by fax
on a "trend of rising unemployment" argument — because their rates cleared neither candidate
threshold. Requested criterion and dispositive criterion are **the same** (`pct20_above_natl`)
so no D-16 conflict arises; what differs is that the state advanced a *soft* justification
alongside the numeric one and FNS answered only the numbers. All three rows carry
`soft_criterion_invoked = true`, and they are the corpus's first instance of that flag firing
on a **denial** rather than an approval. The lesson for option (3): `criterion_code_requested`
would be identical to `criterion_code` on these rows and would record nothing, while the
actual asked-vs-decided divergence lives entirely in `soft_criterion_verbatim`. So the
revealed-preference content of a denial is not always in the criterion pair — sometimes it is
in the soft argument the state made and FNS declined to engage. Whatever `criterion_*`
redesign lands should confirm that `soft_criterion_invoked` survives into `2224` on rejected
rows, which is currently 3 of the corpus's small rejected population.

**AL supplies the missing sign: FNS recomputing in order to APPROVE (2026-08-15).** Every
prior instance of "FNS recomputes rather than accepts" (IN FY2004/FY2005, AR FY2002/FY2005)
has FNS re-running the arithmetic and *denying*. AL FY2000-a runs the other way. Dallas
County's printed rate is **9.95%**; the state rounded it to "10 percent"; FNS explicitly
**rejected the round-up** (the rule requires unemployment *above* 10%, and a flat 10% would
fail even if the rounding stood) — and then, because current BLS county data was unavailable
for Dallas, recomputed on an **older 12-month window** (Nov 1998–Oct 1999, against Dec
1998–Nov 1999 for the other seven counties) and approved it on the new figure.

So the same discretion that produces denials elsewhere produces an approval here, via a
*methodological* substitution rather than a different rule. Two implications for the
`criterion_*` redesign:

- The requested/dispositive pair does not capture this at all. Both are `pct10_statutory`;
  what changed is the **data window**, which lives in `data_nonconformance` and
  `local_unemployment_*`. Any redesign must confirm those fields survive into `2224`
  alongside the criterion pair, or the case becomes invisible.
- It is direct evidence that FNS's arithmetic is not a neutral check. FNS refused the state's
  rounding — stricter than asked — and then supplied a substitution that reversed the outcome.
  That combination is hard to read as mechanical rule-application and is worth isolating for
  the paper next to the IN FY2005 below-threshold approvals.

**Louisiana supplies the second recompute-to-APPROVE, and then something sharper: FNS reverses
its own denial by changing the rounding convention (2026-08-15).**

*The second recompute-to-approve.* `la-abawd-response-fy2003` states plainly that on the data
the state submitted — a 24-month average of **6.04%** for CY2001–2002 against a **6.08%**
threshold — "the State would not qualify for the waiver based on the data submitted." FNS then
substitutes an **earlier** 24-month window (CY2000–2001: **5.7%** against a **5.2%** threshold)
and approves. Mechanically identical to AL FY2000-a's Dallas County window substitution, in a
different state, five years earlier — and this time the substitution is not forced by missing
data: the current data existed and simply failed. That removes the "FNS had no choice" reading
AL FY2000-a permitted, and makes the pair much harder to describe as neutral rule-application.
(The extracting agent set `data_nonconformance.older_vintage = true` with a note that the
substitution is sanctioned by 7 CFR 273.24(f)(3)(iii) — see D-22 for why that flag's semantics
are themselves unsettled.)

*The rounding reversal.* `la-abawd-response-fy2001` is a bundled packet containing FNS's own
correction of itself. The Waiver Response **denies** Calcasieu (balance), Livingston and West
Feliciana against a stated "national rate" of 5.28%. Two later FNS documents in the same PDF
(a 2001-02-22 memo and a 2001-03-14 letter to the state) establish that 5.28% was never the
national rate — it was **120% of** national, i.e. the threshold itself, mislabelled — recompute
the threshold to 5.24%, round both sides to one decimal, and **approve all three**. Calcasieu
lands at exactly 5.2 against 5.2; Livingston's 5.25 becomes 5.3 under a round-half-up
convention the document never states.

The same three areas are denied and approved inside one document, and what changed was not the
data, the areas, or the rule — it was **the rounding convention plus a label error**. IN FY2005
showed an approval apparently turning on a rounding rule; here FNS *changes the convention* and
the outcome flips. This is the strongest single piece of evidence in the corpus that the
arithmetic is administered rather than applied. It is also a D-02 supersession case with an
unusual property: the superseding action is inside the same file as the action it supersedes.

*Approvals that do not clear the stated rule now span four states.* Adding to IN FY2005 (two
sub-regions approved below the threshold FNS itself recomputed) and AL FY2006 (≈6.86% against
a correctly-derived 6.96%):

| doc | printed claim | the arithmetic | outcome |
|---|---|---|---|
| LA FY2001 | Plaquemines, under a heading reading "Greater Than 120% of National" | 5.05% against a cited national 5.04% = **100.2%** of national | approved |
| UT FY2009-a | San Juan, "20 percent above" a national 4.7% | 5.6/4.7 = **119.1%**; the literal threshold is 5.64% | approved |
| LA FY2024 | threshold stated as 5.2% for a national 4.4% | 4.4 × 1.2 = **5.28 → 5.3**; the bundle's own rate is 5.2% | approved |

LA FY2024 reproduces AL FY2006's mis-rounding exactly: the document under-rounds its own
threshold and the set then "clears" the under-rounded figure. Two states, and in both the error
runs in the direction that grants coverage. Worth counting corpus-wide before drawing the
inference — but if the sign holds, a systematically permissive rounding convention is a finding
in its own right and belongs beside the threshold-hugging exhibit.

---

### D-17 · State-request documents: one group with zero units, or one statewide unit?

**Opened** 2026-08-14, from the IN run. **Blocks** `2224` row counts for the state-authored
document class; **affects** `2220b`.

**The evidence.** Two adjacent Indiana documents of the same class were encoded
incompatibly by blinded agents:

| doc | content | groups | units | reasoning given |
|---|---|---|---|---|
| IN FY2011 | forwarded email carrying the state's request; basis given only as "under labor surplus", no areas named | 1 | **0** | LSA is inherently a per-unit DOL designation and the document never claims whole-state LSA status, so inventing a statewide unit would misrepresent the rule |
| IN FY2013 | state letter claiming Indiana is one of 46 states qualifying; no rule named, no areas named | 1 | **1** (Indiana, statewide) | the letter makes a genuine state-level claim about a specific area and period; `group_action = null` preserves that no decision was made |

Both agents reasoned explicitly from `2220b`; both are defensible. IN FY2012 (also a state
adoption email) went the FY2013 way, giving 2–1 within one state.

**MO FY2011 and FY2012 both went the statewide-unit way (2026-08-15), making it 4–1.** Both
are DSS Waiver Requests with no FNS decision; both agents emitted one group with **one
statewide unit** (`Missouri`) and `group_action = null`. Neither agent flagged the choice as
difficult, and unlike IN FY2011 the basis here is `eb_trigger` — a genuinely state-level DOL
determination — so a statewide unit is not an over-claim. **That is the distinction the rule
should turn on, and it cuts across the two IN cases too:** IN FY2011's agent refused a
statewide unit precisely because its stated basis was *LSA*, which is per-area by
construction; IN FY2013's accepted one for a claim about the state as a whole. So the
existing 4–1 split is not really 4 agents against 1 — it is agents correctly tracking whether
the asserted rule has state-level scope. A rule that says "emit a statewide unit iff the
document's stated criterion is one whose scope is the state (`eb_trigger`,
`federal_suspension`); otherwise emit the unenumerated form" would reproduce all five
codings, which is a strong argument that option (3) should be scoped by criterion rather than
applied blanket.

**Why the spec is silent.** `2220b` mandates a single state-named unit for
`federal_suspension` and describes unit emission for adjudicated areas. It says nothing about
a document that requests coverage without enumerating *any* area — which is the normal shape
of the state-authored class (**15 documents corpus-wide**: KS FY2011/12/13, MS FY2011/13, AR
FY2011/12/13, SC FY2012, IN FY2011/12/13, **MO FY2011/12**, GA FY2007).

**Relation to existing entries.** This is **D-06's shape arriving from the opposite
direction.** D-06 is about unenumerated *denials* — FNS decides, and the areas cannot be
listed. Here nothing is decided at all and the areas are equally unlistable. D-06's declined
`unit_enumeration` field would in fact cover both, which is an argument for reopening it.
Distinct from D-07, which asks whether these documents should count as applications; D-17
asks how to shape the row if they do.

**Options.**
1. **Zero units.** A group with no units is the honest record when no area is named. Costs:
   the row is invisible to every unit-level query, and `2224` must special-case it.
2. **One statewide unit.** Every group carries at least one unit, so unit-level joins never
   silently drop a document. Costs: asserts statewide scope the document may not support —
   FY2011's agent objected to exactly this.
3. **One unit with `area_type = unspecified`.** Keeps the row joinable without claiming
   scope, and makes "requested but not enumerated" a first-class, countable value.

**Recommendation: (3)**, paired with reopening D-06's `unit_enumeration`. The two problems
have one cause — the schema cannot say "areas are in scope but this document does not name
them" — and it has now produced a wrong-looking row four times as a denial (DE FY2026,
WI FY2009, SC FY2004-c) and once as a request (IN FY2011). If only one is fixed, fix this
one: the state-authored class is 13 documents and growing, and D-07 may yet make them
analytically load-bearing.

**AL supplies BOTH codings inside one state, and they fall exactly where the criterion-scoped
rule predicts (2026-08-15).** This is the cleanest test the entry has had, because the two
documents are the same class, one state, two blinded agents:

| doc | what it is | criterion stated | units emitted |
|---|---|---|---|
| AL FY2011 | forwarded email chain; the only AL content is "Alabama requests the continued waiver of the ABAWD requirement for FY 2011" | **none** — the referenced national memo is not attached | **0** |
| AL FY2013 | forwarded SERO broadcast + "Alabama will adopt the ABAWD waiver for FY 13" | **`eb_trigger`** (from "ABAWD Trigger Notice") | **1**, statewide |

Neither agent knew of the other. FY2011's declined to name an area because the document names
no rule with any scope; FY2013's emitted a statewide unit because the trigger notice is a
state-level determination. That is precisely the rule proposed in the MO update above —
**emit a statewide unit iff the document's stated criterion has state-level scope** — and it
now reproduces the coding on **7 of 7** documents (IN FY2011 zero / IN FY2012, FY2013
statewide / MO FY2011, FY2012 statewide / AL FY2011 zero, FY2013 statewide) without a single
counterexample.

That is strong enough to treat the criterion-scoped formulation as the recommendation rather
than a refinement of option (3): scope the rule by criterion, and option (3)'s
`area_type = unspecified` becomes the value the *no-scope* branch emits, which is exactly the
row shape AL FY2011 needed and could not express.

**UT/LA take it to 12 of 12 (2026-08-15) — the rule can be considered tested.** Five more
state-authored documents in the state-request class, all five stating `eb_trigger`, all five
emitting **one statewide unit** with `group_action = null`:

| doc | the state's own words | criterion | units |
|---|---|---|---|
| LA FY2011 | "elects to extend … DOL Trigger Notice 2010-2 … one of 49 qualifying states" | `eb_trigger` | 1, statewide |
| LA FY2012 | "DOL Trigger Notice 2011-13 … one of 46 qualifying states" | `eb_trigger` | 1, statewide |
| LA FY2013 | "DOL Trigger Notice 2011-52 … one of 46 qualifying states" | `eb_trigger` | 1, statewide |
| UT FY2011 | "choosing the option to suspend the ABAWD time limits … met UI extended-benefit criteria" | `eb_trigger` | 1, statewide |
| UT FY2012 | "the State qualifies for extended unemployment benefits" | `eb_trigger` | 1, statewide |

Five blinded agents, two states, no counterexample, and several said explicitly that they were
extending the spec's statewide-unit convention *by analogy from `federal_suspension`* because
`2220b` does not name the `eb_trigger` case. That is the rule doing the work while going
unstated — which is the argument for writing it down rather than continuing to rely on the
analogy holding. **12 of 12** across IN, MO, AL, LA and UT.

One caution the LA trio adds. All three cite a DOL trigger notice AND a count of
simultaneously-qualifying states (49, 46, 46), so under D-07 these are the blanket-national
event, not independent applications. The criterion-scoped rule gets the *row shape* right and
tells you nothing about whether the row should be counted as an application — those are
separate questions and D-07 owns the second one.

---

### D-18 · Two concurrent waiver serials, and an area that moves between them is coded `denied`

**Opened** 2026-08-15, from the AL run (`fe5d1b3c`). **Blocks** `2224` — it corrupts the
outcome variable directly. **Affects** `2220b` and `2220c` (`group_action` enum).
**Highest-priority item from that run.**

**The evidence.** Alabama does something no state in the corpus has done so far: it runs
**two waiver serials at the same time, on two different rules**, for five consecutive years.

| serial | rule | FY1999 | FY2000 | FY2001 | FY2002 | FY2003 | FY2004→2009 |
|---|---|---|---|---|---|---|---|
| **970043** | `pct10_statutory` | 12 | 9 | 11 | 12 | 15 | — (ends) |
| **970225** | `lsa` | 18 | 24 | 19 | 23 | 27 | 37 → 43 → 36 → 22 → 15 → 32 |

Counties migrate between the two as their own unemployment rate crosses 10%. When a county
drops below 10% it leaves 970043 — but it does **not** lose coverage: FNS moves it onto
970225, where it qualifies on its LSA designation instead. The traffic runs both ways
(FY2003's Bibb, Franklin, Greene and Monroe come *from* 970225 and re-qualify on their own
10% rates under 970043).

Three blinded agents met this and all three coded the transfer as **`denied`**, each
flagging that the enum has no home for it:

| doc | counties transferred out | coded |
|---|---|---|
| FY1999-a | Bullock, Conecuh, Dallas, Perry, Sumter | `denied` ×5 |
| FY2000-a | Choctaw | `denied` ×1 |
| FY2001-a | Crenshaw, Monroe | `denied` ×2 |

**Why it matters more than any other item in this run.** Alabama's flat file carries **10
`rejected` unit-rows. Eight of them are these transfers.** The only genuine merits denials in
the entire state are Mobile and Morgan (FY2005, own rate 6.9% against a 7.0% threshold). So
**80% of Alabama's apparent denial population is areas whose coverage was never interrupted** —
and the denial rate is the panel's dependent variable. Every agent flagged it; none could
avoid it, because the schema offers no alternative that does not lose the fact.

Note this is *not* D-12. In D-12 an area leaves the waiver and coverage genuinely lapses (or
the document is silent about what happened). Here the document affirmatively states that
coverage continues, under a named sibling serial, with no gap. Coding it `denied` asserts the
opposite of what the page says.

**Options.**
1. **Add `transferred` to the `group_action` enum**, with a companion
   `transferred_to_serial` field. The fact becomes queryable and the denial denominator
   becomes clean.
2. **Emit no group** and record the transfer in `request_level.notes` (D-12's case (c)).
   Rejected on the same grounds as D-12: it drops the observation entirely, and here the
   observation is a *positive* coverage fact, not an absence.
3. **`group_action = approved`** on the receiving serial's document only, and no row on the
   sending one. Loses the sending document's own account of what it did.
4. Leave `denied` and repair downstream in `2224` by checking whether the same
   (state, area, interval) appears under another serial. Works only where both documents are
   in the corpus and both were extracted.

**Recommendation: (1).** It is one enum value plus one field, it is mechanically
determinable (does the document name a destination serial?), and it is the only option under
which the denial rate is correct without a downstream repair that silently depends on corpus
completeness. (4) is the fallback if the schema is frozen, but note it would have to run
*before* any approval-rate statistic is computed, not after.

**Sweep needed.** Alabama is the first state where the parallel-serial architecture is
visible, but it cannot be the only one — AR 980013 and MO 970129/2070002 were each read as
"one serial spans a decade," which is the same phenomenon seen from one side. Grep the corpus
for transfer language ("transferred to waiver", "will be covered under", "moved to #") before
ruling. **This also changes how D-04's key question is posed:** the panel key must separate
*coverage* from *instrument*, because in Alabama a county-year can be continuously covered
while its serial changes underneath it.

---

### D-19 · An approval that rests on no criterion at all: the bridge extension

**Opened** 2026-08-15, from the AL run. **Blocks** `2224`'s criterion denominator;
**affects** `2220b`. **Companion to D-18** — same cause, different field.

**The evidence.** The flip side of D-18's transfer is the **bridge**: rather than move a
county immediately, FNS extends its existing 970043 coverage for a few months until the
sibling LSA waiver can pick it up. The county's own rate is *below* the 10% threshold the
whole time, and the document says so.

| doc | counties | own rates | bridge expiry | coded |
|---|---|---|---|---|
| FY2002-a | Butler, Greene | "slightly below 10%" (not printed) | 2002-03-31 | `approved`, `criterion_code = null`, `qualification_level = unknown` |
| FY2003-a | Clarke, Pickens, Sumter, Winston | 9.5, 9.3, 9.8, 9.3 | 2003-03-31 | `approved`, `criterion_code = null`, `qualification_level = unknown` |

Two blinded agents reached the identical encoding independently and both explained why: the
group is genuinely `approved` (FNS grants a dated extension), but no rule supports it —
`pct10_statutory` is false on the printed numbers, and the LSA basis belongs to the *other*
serial, which this document does not adjudicate. Both refused to invent one. That is correct
behaviour and it produces **6 approved unit-rows with a null criterion**, which is currently
indistinguishable from "criterion could not be determined."

**Why it matters.** These are approvals that are not qualifications. If the paper's criterion
mix is read as "which rule carried this area," six Alabama rows silently answer "none," and
a reader cannot tell whether that means *no rule applied* or *we could not read the page*.
It is also substantively interesting on its own: FNS is administering continuity of coverage
as a goal separate from the eligibility test, which is exactly the kind of discretion the
paper is trying to locate.

**Options.**
1. **Add `criterion_code = administrative_continuity`** (or `bridge`), defined as "coverage
   extended to avoid a gap pending qualification under another instrument." Makes the
   population countable and keeps `null` meaning "undeterminable."
2. **Leave `null`** and recover it downstream from (`group_action = approved` AND
   `criterion_code IS NULL`). Works today; breaks the first time a genuinely
   undeterminable approval appears — and D-10's `unknown` population shows those exist.
3. Code it under the destination serial's rule (`lsa` here). Rejected: it asserts a
   designation this document does not claim and that the county may not yet hold.

**Recommendation: (1).** The distinction between "approved on a rule" and "approved to
preserve continuity" is exactly the margin the panel measures, and it is mechanical to
apply — the document either states a qualifying test or states a bridge. Note this composes
with D-18: a bridge is a *deferred* transfer, so the two values together describe the whole
Alabama pattern, and `2224` can reconstruct continuous coverage from them without re-reading
prose.

**Related, and not the same:** D-15's `deferred` is FNS declining to decide *yet*. Here FNS
has decided — affirmatively, with an end date — it simply has not decided on a rule.

**Utah reproduces the bridge twice, and D-19 is therefore not an Alabama artifact
(2026-08-15).** The entry was opened on a single state where two concurrent serials made the
mechanism visible. Utah has one serial and produces the same shape anyway:

| doc | area | the bridge | coded |
|---|---|---|---|
| UT FY1999-b | Kane County | FNS states Kane is **not** on the FY1999 LSA list, then extends its exemption to end-Feb 1999 "to notify recipients … or to develop additional data to justify a further extension" | `approved`, `criterion_code = null`, `qualification_level = unknown` |
| UT FY2009 | the whole (unnamed) prior coverage | FNS **denies** the state's reconsideration request, then extends the existing waiver through 2009-01-30 so coverage does not lapse while the state prepares a revised request | `approved`, `criterion_code = null`, `qualification_level = unknown` |

Two more blinded agents, same encoding, same stated reason — the group is affirmatively
approved with a dated end, and no rule supports it. That is now **four independent agents in
two states** converging on `approved` + `null` + `unknown` without prompting, which is about
as strong as unprompted inter-agent agreement gets in this corpus.

Utah also adds a sub-shape Alabama did not have. AL's bridges are *forward-looking* — hold
coverage until the sibling instrument picks the county up. UT FY2009's bridge runs alongside a
**denial**: FNS refuses the substantive request and extends coverage anyway, purely to give the
state time. UT FY1999-b is the same, one step earlier — coverage extended explicitly so the
state can go get evidence it does not yet have. So the bridge is not only a transfer mechanism;
it is FNS buying the state time against its own adverse decision. That strengthens the
"continuity as a separable objective" reading and makes option (1)'s name matter: something
like `administrative_continuity` covers all four cases, whereas `bridge_to_sibling_waiver`
covers only Alabama's.

---

### D-20 · Aggregate geography as a unit: expand an MSA row into its members, or hold it?

**Opened** 2026-08-15, from the UT/LA run. **Blocks** `2224` row counts; **affects** `2220b`.

**The evidence.** Two Louisiana documents on the **same serial (2020121), in adjacent years,
printing the same table shape**, were encoded incompatibly by blinded agents. Both tables list
parishes individually and then carry one row for the **New Orleans-Metairie-Kenner MSA** with a
single combined rate and no sub-parish breakdown.

| doc | stated coverage | MSA row encoded as | units emitted |
|---|---|---|---|
| `la-abawd-response-fy2008` | "the 61 parishes" | **expanded** into its 7 named constituent parishes, `unemployment_rate = null`, `qualifying_basis = unknown` | 61 |
| `la-abawd-response-fy2009-a` | "55 parishes" | **held** as one unit, `area_type = metropolitan statistical area` | 49 (for 55 parishes) |

Each agent reasoned explicitly and each is defensible on its own page. FY2008's agent expanded
because the document's own stated unit count (61) is only reachable by expansion — 54
individually-tabulated parishes + 7 named inside the MSA parenthetical = 61 — and because the
document's unit of coverage is the parish, not the MSA. FY2009-a's agent held the row because
expanding it "would fabricate parish-level rates the document never gives," and recorded the
7-parish membership in prose instead.

**Why the spec is silent.** `2220b` tells an agent how to split a *rule/action* set into
groups and how to treat a named bundle of areas. It says nothing about a printed row whose
**geography is itself an aggregate** of the coverage unit. The MSA is neither a bundle the
state constructed (it is a Census definition) nor a coverage unit in its own right (the waiver
covers parishes).

**Why it is not D-01.** D-01 is a *stated count with a named complement*, and there the
arithmetic is determinate — 55 − 9 = 46 reproduces the document's own number, so expansion is
verifiable. Here expansion recovers the **names** (they are printed) but not the **rates**, and
the 7 parishes' individual status is genuinely unknowable from the page. So D-01's acceptance
test — "the expansion must reproduce the stated count" — works for FY2008 (61) and has nothing
to check against in FY2009-a (which states 55 and prints 48 rows + the MSA).

**Options.**
1. **Always expand** where the members are named, with `unemployment_rate = null` and
   `qualifying_basis = unknown`. Every row is a coverage unit, so unit-level joins are clean
   and the panel gets parish-years for free. Cost: 7 rows per document carry no rate, which
   inflates D-10's `unknown` population for a reason unrelated to FNS reporting practice.
2. **Always hold** the aggregate as one unit with `area_type = metropolitan statistical area`.
   Faithful to the page. Cost: `2224` must expand it anyway, against an external MSA-definition
   crosswalk whose vintage matters (MSA boundaries are redefined decennially — the 2008 and
   2020 New Orleans MSA are not the same 7 parishes).
3. **Hold the unit, carry the membership structurally** — one unit plus a
   `component_units[]` list populated from the document's own parenthetical, and let `2224`
   expand deterministically.

**Recommendation: (3), same shape as the D-01 recommendation and for the same reason.** The
expansion is reference-dependent, so it belongs in code rather than in agent judgment, but the
membership list is *printed in this document* and must not be re-derived from an external
crosswalk of uncertain vintage. Note this is a real trap independent of the ruling: the MSA
row is not a small residual — it is 7 of 61 parishes in FY2008 and 7 of 55 in FY2009-a, i.e.
11–13% of the state's covered geography, and it sits on New Orleans, the largest ABAWD
caseload in Louisiana.

**Sweep needed.** Grep the corpus for MSA / LMA / "metropolitan statistical area" rows inside
otherwise unit-level tables. The KS "Finney-Kearny LMA" component (KS FY2004, already flagged
under D-11 for double-counting Finney) is the same shape from a different direction, and IN
FY2004's rejected multi-state **Chicago labor market area** claim shows FNS itself reasoning
about aggregate geographies as candidate units.

---

### D-21 · `qualifying_basis` for a lone statewide unit under a rate rule

**Opened** 2026-08-15, from the UT/LA run. **Affects** D-10's denominator; **affects** `2220b`.

**The evidence.** Louisiana files whole-state waivers under `pct20_above_natl` — no sub-state
areas named anywhere, the state itself is the evaluated unit. Four blinded agents, one state,
one recurring document shape, a **2–2 split**:

| doc | `qualifying_basis` | agent's stated reason |
|---|---|---|
| LA FY2002 | `own_rate` | it is a rate test and the state cleared the threshold on its own printed rate; `own_rate` is more precise than `statewide` |
| LA FY2019 | `own_rate` | same |
| LA FY2003 | `statewide` | the unit *is* the state; `statewide` is the enum value built for whole-state qualification |
| LA `approval-9.2018-8.2019` | `statewide` | same |

All four flagged it as a close call. Every one of them also coded `qualification_level =
statewide` — the split is only on `qualifying_basis`.

**Why the spec is silent.** `2220b` defines `qualifying_basis` as an answer to "did this area
qualify on its own or ride the bundle," which presupposes a bundle. `statewide` is documented
as the value for whole-state qualification under rules whose *scope* is the state
(`eb_trigger`, `federal_suspension`). Neither branch covers a **rate rule applied to the state
as the unit**, which is what these documents are.

**Why it matters despite looking cosmetic.** D-10's carried-vs-own margin is computed off
`qualifying_basis`. If half the statewide rate-rule rows read `own_rate`, they enter that
margin's denominator as genuinely load-bearing areas; if the other half read `statewide`, they
are excluded. In this run that is 17 LA rows and 2 UT rows, but the shape is the modern norm —
Louisiana is statewide-dominant from FY2002 onward and several other states go statewide after
2015 (MS from FY2006, AL FY2013, WI/KY post-OBBB).

**Options.**
1. **`statewide` whenever `qualification_level = statewide`**, regardless of criterion. One
   rule, mechanically checkable, and it keeps `own_rate` meaning "this area cleared the bar
   inside a set that had other members."
2. **`own_rate` whenever a rate test was run on the unit**, reserving `statewide` for
   scope-statewide rules (`eb_trigger`, `federal_suspension`). Preserves the fact that an
   arithmetic test was actually performed.
3. Leave to agent judgment — rejected; the table above is what that produces.

**Recommendation: (1).** It is the option under which `qualifying_basis` answers exactly one
question (own-vs-carried *within a set*) and never has to double as a record of which rule
ran — that is `criterion_code`'s job, and it already distinguishes `pct20_above_natl` from
`eb_trigger` on these very rows. Under (2) the two fields become partially redundant and the
D-10 margin quietly acquires a population of single-member "sets."

---

### D-22 · `data_nonconformance` on documents whose criterion has its own data regime

**Opened** 2026-08-15, from the UT/LA run. **Affects** `2224` filtering; **affects** `2220b`
and `2220c` field documentation. **Lower priority than D-20/D-21 — it changes a flag, not a
row.**

**The evidence.** Louisiana's EB-trigger letters cite a **seasonally adjusted, DOL-sourced,
3-month-average TUR** — which is not a departure from method, it is the method the EB trigger
is *statutorily defined* on (26 USC 3304). Four agents, 2–2:

| doc | coded | reasoning |
|---|---|---|
| LA FY2004 | `non_bls_source = true`, `seasonally_adjusted = true`, + a `note` saying this is correct practice for the criterion, not a defect | the field's literal definition fires on affirmative textual evidence |
| LA FY2006 | same (true + explanatory note) | same |
| LA FY2005 | whole object `null` | the flags are calibrated to the 24-month BLS/LAUS area tests; firing them here manufactures a false non-conformance signal |
| LA FY2023 | whole object `null` | same, stated with the KB citation |

Both readings are argued from the spec and both agents on each side wrote the reasoning out.

**Why it matters.** `data_nonconformance` is precisely the kind of column a panel builder
filters on ("drop rows whose data method was irregular"). Under the true-with-a-note coding,
every statewide EB-trigger row in the corpus looks irregular and the note explaining otherwise
is free text no filter will read. Under the null coding, the field silently loses the ability
to record a genuine EB-trigger data problem if one ever appears.

**Note the third position already in the corpus.** LA FY2003's agent set `older_vintage =
true` for an FNS-sanctioned substitution to an earlier data window (see D-16) — i.e. it used
the flag to record *a fact the document reveals* while noting the substitution was permitted.
That is the same tension in a case where the flag is clearly the right home for the fact.

**Options.**
1. **Scope the flags to the criterion.** Define `data_nonconformance` as departure from *the
   norm applicable to this criterion*, and state in `2220b` that the EB-trigger TUR regime is
   conforming by construction. Null (or all-false) becomes correct for LA's letters.
2. **Keep the flags literal** (what the document says about the data) and add a separate
   `data_regime` field naming which norm applies, so `2224` can decide.
3. Leave as is and instruct `2224` to ignore `data_nonconformance` wherever
   `criterion_code IN (eb_trigger, federal_suspension)`.

**Recommendation: (1).** The field's whole purpose is to mark rows a careful analyst should
look at twice; a flag that fires on the statutorily-correct method for its own criterion has
negative information value. (3) works today but is another rule-about-a-rule of exactly the
kind D-15's recommendation warns against.

---

### D-23 · Partial approval on the TIME margin has no representation

**Opened** 2026-08-15, from the UT/LA run. **Blocks** `2224`'s outcome variable; **affects**
`2220c`.

**The evidence.** FNS routinely grants **less time than the state asked for**, while approving
every area requested. Three instances in this run alone, across both states:

| doc | requested | granted | how the agent encoded it |
|---|---|---|---|
| LA FY2002 | 17 months (2002-05-01 → 2003-09-30) | 12 months (→ 2003-04-30) | one `approved` group; requested window in `applied_waiver_*`, granted window in `waiver_*` |
| UT FY1998 | 2 years | 1 year, FNS explicitly capping it | same |
| UT FY2007 | (2-year approvals are the norm) | 17 months "as an exception," because the state "did not provide us with the data for a two-year waiver approval" | same |

All three agents made the same call and at least one flagged it: emitting a second `denied`
group for the unapproved months "would imply FNS evaluated and rejected a *different* claim,
when in fact it made one determination and limited its duration." That reasoning is right, and
the consequence is that **the partial refusal leaves no trace in `group_action`.** Every one of
these rows reads `approved`.

**Why it matters.** The panel's dependent variable is what FNS did. A state that asked for 24
months and got 12 was partially refused, and UT FY2007 states the *reason* on the page — the
state's evidence supported less than it asked for. That is a graded FNS response to evidence
quality, which is closer to the discretion the paper is trying to locate than a binary
approve/deny ever gets. Right now it is recoverable only by comparing two date pairs that are
populated inconsistently (see the judgment-call list: several agents populate `applied_*` only
when the two windows differ; others populate them always; UT FY2007 left them null because the
document implies rather than states the ask).

**Options.**
1. **Derive it in `2224`** as `granted_duration < applied_duration`, and make the `applied_*`
   date fields mandatory-when-stated so the comparison is well defined. No schema change.
2. **Add `group_action = approved_in_part`**, or an orthogonal `duration_trimmed` boolean plus
   the reason text. Makes the event countable by `GROUP BY` rather than by date arithmetic.
3. Leave it. Rejected — this is the third distinct margin (after D-12's dropped areas and IN's
   invisible additions) on which a real FNS decision produces no queryable record.

**Recommendation: (1) with the field-population contract tightened, escalating to (2) if the
sweep finds volume.** The dates already carry the fact; what they lack is a stated rule about
when to populate them. Note the interaction with D-04: a trimmed duration is precisely a case
where `fiscal_year` destroys the information, because the requested and granted windows can sit
in different FYs.

**Sweep needed.** Count documents where `applied_waiver_end_date != waiver_expiry_date` across
the whole arm. Three in 45 here suggests this is not rare.

---

### D-24 · A disaster-relief basis with no criterion code

**Opened** 2026-08-15, from the UT/LA run. **Affects** `2220b`, `2220c` (`criterion_code`
enum), and the criterion denominator.

**The evidence.** `la-abawd-response-fy2009` approves a **statewide** ABAWD exemption for
2008-09-01 → 2009-02-28 under **Section 402 of the Stafford Act** and **Section 5(h) of the
Food and Nutrition Act**, after Hurricanes Gustav and Ike. The stated rationale is disaster
impact and strained state-agency staff and resources — **not** insufficient jobs, not an
unemployment rate, not an LSA designation, not an EB trigger.

The agent grepped the rules KB for `disaster` / `stafford` / `d-snap` / `402`, found nothing,
and set `criterion_code = null` rather than forcing `other`. Its stated reason: `other` is
scoped in `2220b` to *softer insufficient-jobs evidence* (declining EPOP, industry decline, a
cited study), and this is not a jobs argument at all — it is an administrative-burden argument
under a different statute. It called this "the single most consequential call in this
extraction" and asked for the entry.

**Why it matters.** This is the first document in the corpus whose waiver does not rest on the
labor market in any form. It is also **not** a fringe case for the paper: a disaster waiver is
coverage a state obtains without any revealed preference about local labor conditions, so
counting it as an ABAWD waiver application in a labor-market model is a category error. It
needs to be visible enough to *exclude*, which `null` does not achieve — `null` currently also
means "the letter names no rule" (LA FY2011/FY2012 state letters, IN FY2013) and, after D-19,
"approved as a bridge."

**Options.**
1. **Add `criterion_code = disaster_relief`** with the Stafford Act / FNA §5(h) citation in
   `criterion_verbatim`. One enum value; makes the population countable and excludable.
2. **Route to `other`** and rely on `criterion_other_explanation`. Cheap, but it merges a
   different-statute waiver into the soft-jobs catch-all, which D-13 is already trying to
   un-merge.
3. Leave `null`. Rejected: `null` is now carrying at least three distinct meanings.

**Recommendation: (1).** Note the interaction with D-07: a disaster waiver, like a blanket
national action, is an event where coverage arrives without a state making a labor-market
case, so both belong in whatever exclusion flag `2224` builds for the revealed-preference
analysis. Worth a corpus sweep for Katrina (2005), Rita, Sandy (2012), Harvey/Irma/Maria
(2017) and the 2020 derecho — Louisiana will not be the only state with one, and the
2005 window in particular should be checked against LA/MS/AL/TX.

---

### D-25 · Per-unit rates derivable from printed counts: populate or leave null?

**Opened** 2026-08-15, from the UT/LA run. **Directly determines whether D-10's margin is
computable**; **affects** `2220c` field documentation.

**The evidence.** A large class of documents prints **unemployed and labor-force counts per
area but no per-area rate**, with only a combined rate for the set. The division is trivial
and unambiguous. Three Utah agents, one state, one table convention, split **2–1** on whether
the derived rate belongs in the `unemployment_rate` field:

| doc | derived the rate? | populated `unemployment_rate`? | reasoning |
|---|---|---|---|
| UT `approval-10.2017-9.2018` | yes | **yes** | "the spec explicitly wants this arithmetic done"; the division is trivial from the same printed row |
| UT FY2017 | yes | **yes** | same — "the schema field exists to let this check be re-verified downstream" |
| UT FY2007 | yes | **no** | the field is defined "as printed for it"; no rate is literally printed, so populating it would store a self-computed number in a transcription field |
| UT FY2016 | yes | **no** | same; put the computed rates in `qualification_level_evidence` free text instead |

(4 agents, 2–2 — UT FY2016 joined the FY2007 side.) **Every one of them used the derived rates
to set `qualifying_basis`**, so the group-level judgment is consistent; what differs is whether
the number survives into a queryable column or dies in free text.

**Why this is the highest-leverage of the new entries.** D-10 says the carried-vs-own margin
should be preserved where determinable and never imputed. This class of document is exactly
where it *is* determinable but not printed — and under the FY2007/FY2016 coding the evidence
for that determination is unqueryable, so a downstream check cannot verify or reproduce the
`qualifying_basis` assignment. IN FY2004 hit this same fork (re-derived all seven sub-area
rates, reproduced the document's own totals exactly in 7/7 cases, and still set `unknown`), and
GA FY2017 / KY FY2017 hit it on the other side.

**Options.**
1. **Populate the derived rate, and add a `rate_is_derived` boolean.** The number is
   queryable, and nobody mistakes it for a transcription. One new field.
2. **Populate `unemployment_rate` only when printed; add `unemployment_rate_derived`** as a
   separate column. Keeps the transcription field pure — the same discipline `name` vs
   `orig_text` already follows, which is a strong precedent.
3. Populate silently (status quo for two agents). Rejected: it makes transcribed and computed
   values indistinguishable in the one field a validator would use to check the extraction.

**Recommendation: (2).** It mirrors the `name`/`orig_text` split the project already made and
already trusts, and it lets `2225` keep scoring `unemployment_rate` as a pure transcription
channel. Either (1) or (2) closes the D-10 gap on the count-printing documents, which is the
substantive win; the choice between them is about keeping the transcription channel clean.

**Update 2026-08-15 (MT/SD run) — the split reproduces in a second state, 3–1, on one serial.**
Montana serial **2140013** prints the same table convention across four documents (counts per
county, combined rate only), and four blinded agents split the same way Utah's did:

| doc | populated `unemployment_rate` from derived counts? | reasoning |
|---|---|---|
| MT FY2016 | **yes** | "the prompt explicitly instructs doing this arithmetic"; the schema notes the field is what lets the threshold check be re-verified |
| MT `approval-2018` | **yes** | same, and documented the derivation in `qualification_level_evidence` so the choice is auditable |
| SD FY2016 | **yes** | computed each county's rate to establish which members are carried |
| MT FY2017 | **no** | "no per-county *rate* is literally printed"; put the arithmetic in `qualification_level_evidence` free text instead |

Running total across both states: **7 agents, 5–2 to populate.** The Utah entry above framed this
as a 2–2 tie; it is not a tie, and the majority reading is the one that keeps the evidence
queryable. But the two-state spread is the more useful fact: **MT FY2016 and MT FY2017 are
adjacent years on the same serial with the same table layout and opposite encodings**, so a
downstream rate-based query sees MT's FY2017 counties as missing and its FY2016 counties as
populated for no reason a reader could reconstruct from the data. That is the concrete cost of
leaving this unruled, and it is now visible inside a single state's time series rather than
across states.

Nothing here changes the recommendation — **(2)** still mirrors `name`/`orig_text` — but the case
is now urgent rather than tidy, because the inconsistency has reached *within-serial*.

### D-26 · `city` vs `independent city`: one `area_type` for county-equivalent cities

**Opened** 2026-08-17, from the VA/OH run (`fe5d1b3c`), with a corpus-wide sweep. **Blocks** any
`2224` join or filter on `area_type`; **affects** `2220c` (the field's description is the cause).

**The evidence.** `2220c` types `area_type` as free string and documents it as "Unit type if
stated/inferable: county, city, parish, borough, census area, reservation area, LMA/labor market
area, **independent city**, planning region, town, balance of county, statewide, national." Both
`city` and `independent city` are on the list and nothing says which governs a Virginia, Maryland or
Missouri independent city — which is a county equivalent with its own LAUS series, not a sub-county
place. Sweeping every JSON in the arm:

| state | `independent city` | `city` | where |
|---|---|---|---|
| VA | 118 rows / 15 docs | 24 rows / 2 docs | `va-abawd-response-fy2006`, `va-abawd-approval-5.2018-4.2019` |
| MD | 16 rows / 16 docs | 7 rows / 4 docs | **`md-abawd-response-fy1999` and `-fy2000` use BOTH inside one document** |
| MO | 10 rows / 10 docs | 3 rows / 2 docs | `mo-abawd-response-fy2005`, `-fy2008` (St. Louis city) |

So the *same physical unit* — Danville, Martinsville, Petersburg, Baltimore, St. Louis — carries
different `area_type` in different years of its own state's series, and in Maryland's case in the
same letter. Every agent read its document correctly; the spec offered two names for one thing.

**Why it matters more than a label.** These are not cosmetic. In VA and MD the independent cities
are a large share of the waived units (VA: 142 of 561 rows), they are exactly the units the
LAUS-cities-vs-counties tier wart was about, and `2224` will want to distinguish "a sub-county place
was waived" (a genuine geography complication, and a `non_standard_geography` candidate when under
25,000) from "a county-equivalent city was waived" (routine). Filtering `area_type == 'city'` in
Virginia today returns two of seventeen years. Note also that WV prints a third variant,
`city (partial)` (`wv-abawd-response-fy2002-b`), against a plain `city` in `wv-abawd-response-fy2004`
— a genuinely different thing (a carve-out of part of a city) that a fixed vocabulary would keep
distinguishable instead of leaving it to prose.

**Options.**
1. **Close the vocabulary.** Make `area_type` an enum in `2220c` and drop `city` in favour of
   `independent city` wherever the unit is a county equivalent, keeping `city` for sub-county places.
   Requires the agent to know which it is — which the geography reference already tells it, since
   independent cities appear in the county-equivalent list.
2. **Keep free text, normalise in `2224`.** A lookup keyed on (state, unit name) against the geography
   reference decides county-equivalent vs sub-county, and `area_type` becomes advisory.
3. **Split the field**: `area_type` (what the document calls it) plus a derived
   `is_county_equivalent` boolean resolved against the reference.

**Recommendation: (1) plus the derived check from (3).** The enum removes the ambiguity at the point
where it is created and costs one line of spec; the derived boolean is what `2224` should actually
join on, because it is resolved against the reference rather than against an agent's reading. (2)
alone leaves the corpus carrying a field that looks authoritative and is not. This is the same
discipline as `name`/`orig_text`: record what the document says, derive what the panel needs.

**Cheap and worth doing either way:** the fix is retroactive without re-running anything. The
mapping is deterministic from the geography reference, so the existing 34 `city` rows in VA/MD/MO can
be reclassified in place once the rule is set.

---

### D-27 · Cross-group carrying sets: the arithmetic depends on units outside the group

**Opened** 2026-08-17, from the VA/OH run. **Recommended in the FL run (2026-08-16) and corroborated
in TN; opened now because OH makes it three states and the first where it is the filing's design
rather than an incident.** **Blocks** any margin recomputed from group membership; **affects**
`2220c` (a `carrying_set[]` field) or `2220b` (a rule about emitting carrying units).

**The evidence, three states.**

| state | doc(s) | shape |
|---|---|---|
| FL | FY2002, FY2004-b, +2 | group's combined rate computed over a set that includes counties adjudicated separately in the same letter, or approved in an earlier action |
| TN | FY2005-a | Campbell and Cumberland approved on a combined 7.5% computed over a set that also contains Monroe, Morgan and Scott — adjudicated in an *earlier* action, not members of the emitted group. Both counties' own rates (6.10, 5.71) are below the 7.1 threshold, so the grant depends entirely on non-members |
| **OH** | **FY2006, FY2006-a** | the EDR tables carry counties labelled **"currently waived"** — covered by a prior, separate action, not adjudicated here — whose labor-force and unemployment numbers feed the printed regional aggregate that carries the newly-requested members |

Ohio is the case that changes the status of this. It is not one letter reusing a neighbour's figures:
it is how the state files. Every Economic Development Region table in FY2006 and FY2006-a lists the
already-waived counties alongside the new ones and prints one aggregate over the union. Both blinded
agents excluded the already-waived counties from `geographic_units` (spec case (c) — referenced but
not requested in this document) and put them in `request_level.notes`; FY2006's agent checked the
exclusion arithmetically against the document's own count (25 bundled + Stark = "26 additional
counties"). That is the correct behaviour under the current spec and it produces a group whose
printed rate cannot be reproduced from its own members.

**Three consequences, all of which bite `2224`.**
1. **Every margin recomputed from group membership is wrong for these groups.** The threshold-hugging
   tables in this register are computed from the documents' own printed aggregates for exactly this
   reason; a downstream analyst recomputing from unit rates will get different numbers for OH FY2006
   and FY2007 and will not know which groups are affected.
2. **`qualifying_basis = carried_by_group` is true but underspecified.** The row says a unit was
   carried; it cannot say by what. Where the carrier is outside the group, the information is not
   anywhere in the schema.
3. **It manufactures spurious D-11 violations.** OH FY2006's Northwest, Southern and Southeast EDR
   decided-subsets are internally non-contiguous *as emitted*, and contiguous once the excluded
   already-waived counties are put back. Any contiguity check run on the emitted groups will flag
   documents that are geographically coherent.

**Options.**
1. **A `carrying_set[]` on the group**: names (and where printed, rates/counts) of units whose data
   enters the group's aggregate but which this document does not adjudicate. Purely additive; the
   agents already write this information into `qualification_level_evidence` prose, so it costs
   transcription, not judgment.
2. **Emit the carrying units as group members with `group_action = null`** (or a new
   `not_adjudicated_here`), flagged so they never count as waived. Keeps one units list; risks a
   naive query counting them as coverage — which is the exact error D-12 is about, in reverse.
3. **A group-level `rate_computed_over_larger_set` boolean.** Cheapest, and enough to *suppress* wrong
   recomputation, but it discards the carrying set itself.

**Recommendation: (1).** It is additive, it matches what the agents already do voluntarily, and it is
the only option that lets the contiguity check and the margin recomputation both be repaired rather
than merely disabled. (3) is the fallback if schema growth is the binding constraint — but note that
FL, TN and OH between them now cover roughly a dozen documents, so the field would carry real content
rather than sitting mostly null.

**Interaction.** This is adjacent to but distinct from **D-11** (a bundle non-contiguous as drawn),
**D-20** (aggregate geography treated as a unit) and **D-12** (an area dropped from a prior waiver).
The distinguishing fact is that the unit is *neither* waived by this document *nor* absent from its
arithmetic. D-12's dropped areas produce no row and no effect; a carrying unit produces no row and a
large effect.

### D-29 · A qualifying rate the schema cannot store: the higher of two windows

**Opened** 2026-08-25, from the TX run. **Affects** `2220c` (`local_unemployment`,
`geographic_unit.unemployment_rate`), and any downstream threshold check.

**The evidence.** TX FY2000-b (serials 970057 & 990067) approves 16 counties under
`pct10_statutory` on an explicit **higher-of-two-windows** test: FNS printed both a 12-month
average (Jun 1999–May 2000) and a 6-month average (Dec 1999–May 2000) for each county and
approved on whichever was larger. Two approved counties clear the threshold only on the
6-month figure:

| county | 12-month (stored) | 6-month (qualifying) |
|---|---|---|
| Culberson | 9.8 | 10.7 |
| Kinney | **8.0** | 10.3 |

`local_unemployment` holds one window, so the agent stored the 12-month rate in
`unemployment_rate` and put the 6-month figure in `criteria_summary_text` free text. The
extraction is faithful to the document and the reasoning is recorded — but the queryable
column now carries, for two approved `percent_10` units, **a number that fails the very test
they were approved under**, one of them by two full points.

**Why it matters beyond two rows.** Any downstream validation that asserts
`percent_10 & approved ⇒ rate > 10` fires a false positive here, and the refutation lives only
in prose. This is also the first documented case in the corpus of a *disjunctive* rate test
(FY1998 and FY1999 use a similar "either the 12-, 7-, or 3-month period" construction, where
the FY1998 agent reached for `window_type: "other"` and no rate at all), so it is a TX-era
convention rather than a one-document accident — and it is upstream of D-10, since a
carried-vs-own margin computed off the stored window is computed off the wrong window.

**Options.**
1. **Store the qualifying window in `local_unemployment`, the other in a new
   `local_unemployment_alt[]`.** The queryable column always holds the number the action
   actually rests on. Costs one repeated field.
2. **Add a `rate_is_qualifying` boolean** to flag when the stored rate is not the operative
   one. Cheap; leaves the wrong number in the column.
3. Status quo (free text). Rejected for the reason above.

**Recommendation: (1).** It keeps the invariant a validator would want to assert — the stored
rate is the one the decision turned on — and it generalises to the FY1998/FY1999 three-window
form, which (2) does not.

**UPDATE 2026-08-25 (NV run) — the invariant breaks a second way, and it is not about windows.**
NV approves three `pct10_statutory` **joint aggregates**, in which the stored per-unit rate is below
10 while the group's combined rate clears it:

| doc | bundle | combined | members below 10 alone |
|---|---|---|---|
| NV FY2001 | Washoe Tribe of Nevada and California | 11.1% (26/234) | Washoe Reservation 6.5, Carson Colony 9.0 |
| NV FY2004 | Washoe Reservation | 12.9% | Stewart Colony ~4.7 |
| NV FY2000 | Washoe/Carson/Dresslerville | 12.45% | not printed per-member |

So `percent_10 & approved ⇒ stored rate > 10` now has **at least five documented false positives**
(TX's two window cases, NV's three carried members) arising from two unrelated mechanisms. The NV
cases are, unlike TX's, correctly representable in the current schema — `qualification_level =
joint_aggregate` plus `qualifying_basis = carried_by_group` says exactly what happened, and the
FY2001/FY2004 agents used both. The lesson for D-29 is therefore narrower than it first looks: the
schema does not need a new field for the NV shape, but **any validator or panel query must condition
on `qualification_level` before asserting anything about a stored rate**, and that rule should be
written down wherever the D-29 fix lands.

Independently: this refutes the TX section's claim that `pct10_statutory` is "per-area by
construction, with no arithmetic that aggregation could help." That holds in Texas and fails in
Nevada.

---

### D-30 · `nonstandard_averaging` on `pct10_statutory`: is a 12-month window a departure?

**Opened** 2026-08-25, from the TX run. **Affects** `2220b`/`2220c`
(`data_nonconformance.nonstandard_averaging`).

**The evidence.** Texas prints a 12-month average window under `pct10_statutory` in nearly every
year of its record, and sixteen blinded agents seeing the same construction split **5–1** on
whether that is a flaggable departure:

| doc | `nonstandard_averaging` | reasoning |
|---|---|---|
| TX FY1999, FY2001, FY2006, FY2008, FY2013, FY2014 | **true** | the 24-month non-seasonally-adjusted procedure of the 2006 guidance is the standard; a printed 12-month window is an objective departure the document itself reveals |
| TX FY2012 | **false** | checked `002_rules_machine.yaml`, which gives `pct10_statutory` **no fixed-window requirement** and lists `recent_12mo_avg` as a *conforming* evidence form |

**The minority reading is the grounded one.** It is the only one that consulted the rules KB,
and the KB is unambiguous: the 24-month procedure attaches to the 20%-above-national test, not
to the statutory 10% rule. Under the majority coding, `nonstandard_averaging` is set `true`
across most of a 17-year state record for conduct the rules KB says is conforming — which makes
the flag a proxy for "criterion is pct10" rather than a data-quality signal, and quietly
contaminates any cross-state comparison that conditions on it. The flag is currently `true` on
**129 of 264 TX unit-rows**.

**Options.**
1. **Amend `2220b` to state that `pct10_statutory` has no fixed window**, so a 12-month average
   is conforming and the flag stays `false`. Then re-code the affected TX rows.
2. Keep the flag but redefine it as "window differs from 24 months," documented as descriptive
   rather than a nonconformance. Preserves the data, renames the meaning.
3. Status quo. Rejected: the field is called *nonconformance* and is being set on conforming
   documents.

**Recommendation: (1).** The KB already settles the substantive question; the spec just does not
say so where the agents read it. This is a prompt clarification, not a new rule — but it needs a
sweep, because the same 12-month-under-pct10 construction almost certainly appears in earlier
states' arms and would have been coded by the majority reading there too.

**UPDATE 2026-08-25 (NV run) — the recommendation above is now contested by agency text.**
NV FY2002-b approves 16 tribal groups under serial 970184 (`pct10_statutory`) on a 12-month CY2001
average, and FNS **accepts it "this once" while explicitly flagging it for correction going
forward** — i.e. the agency treats a 12-month window under the 10% rule as a departure it is
excusing, not as conforming conduct. That is direct evidence against option (1), which would
declare the same construction conforming and re-code the flag to `false`.

One nearby NV document looks like corroboration but is **not**: FY2005 has FNS rejecting a
single-calendar-year national average as a nonconforming "12-month guidepost," but that test is
`pct20_above_natl`, where the 24-month procedure is uncontested. It shows FNS polices windows; it
says nothing about `pct10_statutory`. NV's other 12-month `pct10` documents (FY2003, FY2004,
FY2026 — 36 groups) carry no FNS remark either way.

So the position is now: the **rules KB** says no fixed window under the 10% rule; **FNS in NV
FY2002-b** says a short window there needs excusing. Both cannot be taken at face value.
**Revised recommendation: option (2)** — keep the flag set but rename it to mean "averaging window
differs from 24 months," descriptive rather than nonconformant. It is the only option that does not
require deciding which of the two authorities is wrong, it preserves the TX and NV data as recorded,
and it leaves the substantive question open for a ruling that can be made on regulatory text rather
than on two documents' worth of inference. The cross-arm sweep is still needed either way.

---

### D-31 · Partial grant by duration: FNS shortens the term instead of refusing the area

**Opened** 2026-08-25, from the TX run. **Affects** `2220b` (`group_action` semantics).

**The evidence.** TX FY2002 approves all 14 requested counties, but grants **four of them
(Crane, Culberson, Morris, Sabine) three months instead of twelve** — 2002-10-01 to 2002-12-31,
against 2002-09-30 for the other ten — because Texas rested those four on a 3-month rate without
the supporting documentation FNS's own January 2001 preamble requires to treat a short-window
rate as durable. This is a *refusal on the duration margin*: substantively a partial denial,
recorded in the schema as `group_action = approved` with a different `waiver_expiry_date`.

**Why it matters.** `group_action` is the field every summary counts, and it reads this document
as 14-for-14 approved with no adverse action anywhere. The adverse action is recoverable only by
comparing expiry dates within a document — which nothing currently does. The corpus already has
one neighbouring shape (WA FY1998-b, where FNS refused whole Community Service Offices and
substituted 25 census tracts — a refusal on the *geography* margin, counted there among the
denials), so this is the second distinct case of FNS bargaining on something other than the
inclusion set, and the two are coded inconsistently.

**Options.**
1. **Add `group_action = "approved_modified"`** (or a `term_reduced` boolean) for a grant whose
   duration is shorter than requested. Makes the adverse action countable.
2. **Derive it**: flag any group whose `waiver_expiry_date` precedes the document's modal expiry.
   No schema change, but it is inference, and it misfires on documents that legitimately carry
   staggered terms.
3. Status quo. Rejected: it makes partial denials invisible to every count.

**Recommendation: (1).** Duration is a choice variable FNS demonstrably uses, and if the panel is
going to measure waiver *coverage* the length of the grant is not a detail. Ruling this also
forces the WA-style geographic substitution to be coded consistently with it.

**UPDATE 2026-08-25 (NV run) — two more instances, both statewide, which strengthens (1).**
- **NV FY2020-a**: 12 months requested, **3 granted** (2020-01-01 to 2020-03-31), because the new
  7 CFR 273.24(f) standards took effect 2020-04-01. The letter calls itself a "Partial Approval"
  *in terms*, and all 21 groups still record `group_action = approved`.
- **NV FY2025**: 24 months requested, **12 granted**, with FNS using only the most recent 24 of the
  36 months of data the state submitted.

That is four instances across three states (TX, NV x2, plus the WA geographic sibling), and the NV
FY2020-a case adds something the TX case lacked: **FNS's own document uses the words "Partial
Approval" for a duration cut**, so option (1)'s `approved_modified` would be recording the agency's
own characterisation rather than an analyst's inference. Note also that NV FY2020-a's shortening is
driven by a *rule change*, not by any defect in the request — so if (1) is adopted, the reason for
the reduction is worth capturing alongside the flag, or the panel will read a regulatory transition
as an adverse action against Nevada.

---

---

### D-32 · LSA qualification by residency: an area that qualifies on someone else's designation

**Opened** 2026-08-25, from the NV run. **Affects** `2220b`/`2220c`
(`geographic_units[].qualifying_basis` enum).

**The evidence.** Nevada repeatedly approves tribal areas under the LSA serial **because they sit
inside an LSA-designated county or city**, not because the area itself holds a DOL designation:

| doc | areas | mechanism |
|---|---|---|
| NV FY2003 | Fallon Paiute-Shoshone, Yerington Reservation and Trust, Yomba Reservation | added to serial 970120 "because they are located within LSA counties" |
| NV FY2005 | Las Vegas Colony | approved because it "resides within" the North Las Vegas City LSA; FNS notes its **own rate is under 10%**, so it fails the 10% test standing alone |

Four instances, two documents, two blinded agents. Both reached for `qualifying_basis =
own_designation` as the closest available value, and **both flagged in-field that it is wrong** —
the area holds no designation of its own.

**Why it matters.** The enum currently distinguishes an area that qualifies on its own evidence
(`own_rate`, `own_designation`) from one carried by a group's *arithmetic* (`carried_by_group`).
Residency inside a designated parent area is a third mechanism: the area qualifies on another
area's status, with no aggregation involved and no group to be carried by — these are coded
`per_unit`. Recording it as `own_designation` asserts a designation that does not exist, and any
count of independently-qualifying areas is inflated by exactly these rows. The FY2005 case is the
sharp one, because the document states the area would fail on its own.

**Options.**
1. **Add `derivative_designation`** to the `qualifying_basis` enum, for an area qualifying on the
   designation or status of a containing area, with the parent named in the unit's evidence text.
2. Reuse `carried_by_group` and force these into a joint group with the parent. Rejected: it
   fabricates a bundle the document does not draw, and corrupts the bundling statistics that
   D-27/D-29 depend on.
3. Status quo (`own_designation` + a note). Rejected: it is a false positive in the one field that
   answers "did this area qualify on its own?", and it is unrecoverable without reading free text.

**Recommendation: (1).** Cheap, additive, and it makes the containment relation explicit. Worth a
cross-arm sweep afterwards — reservations-inside-LSA-counties is unlikely to be NV-only, and other
states' agents would have faced the same missing value.

---

### D-33 · `area_type` is free text, and the tribal vocabulary has fragmented six ways

**Opened** 2026-08-25, from the NV run. **Affects** `2220c` (`geographic_units[].area_type`).

**The evidence.** `area_type` is typed `["string","null"]` with a suggested vocabulary in the field
*description* ("county, city, parish, borough, census area, reservation area, LMA/labor market
area, independent city, planning region, town, balance of county, statewide, national") but no
`enum`. Nevada — 208 of 300 unit-rows tribal, the most tribal-heavy state in the corpus — spreads
those rows across six spellings:

| value | rows |
|---|---|
| `reservation area` (the documented term) | 165 |
| `colony` | 23 |
| `reservation` | 11 |
| `tribal colony` | 7 |
| `tribal community` | 1 |
| `community` | 1 |

Every one is schema-valid. The split is not an agent failure: the documented vocabulary has one
term for tribal areas, and Nevada's documents print "Colony," "Reservation," "Community" and
"Ranch" as legally distinct entity types, so agents reasonably reached for the printed word.

**Why it matters.** `area_type` is the natural grouping key for "how much of the waiver record is
tribal geography?" — a question NV makes central and one the panel will want to ask. Today that
query needs a hand-maintained synonym list, and silently under-counts by 26% in NV if run on the
documented term alone. The corpus-wide `city` / `independent city` version of this is already
open as **D-26**, which suggests the general fix rather than another one-off.

**Options.**
1. **Enum the field** in `2220c` with the documented vocabulary, and keep the printed entity word
   in `orig_text` (where it already lives) plus `non_standard_geography_note`. Forces consistency
   at write time and makes violations schema-invalid rather than silent.
2. Leave it free and normalize downstream in `2223`/the panel builder with a mapping table.
   Cheaper now, but the mapping becomes load-bearing and undocumented.
3. Status quo. Rejected: a grouping key that 26% of NV rows spell differently is not a key.

**Recommendation: (1), resolved together with D-26**, since both are the same defect — a
vocabulary documented in prose but not enforced — and ruling them separately risks two
inconsistent fixes. If (1) is chosen, the enum needs a tribal term general enough for colonies,
communities, ranches and trust lands; `reservation area` as currently documented reads narrower
than the entities it must cover.

---

## DEFERRED

### D-06 · Unenumerated denials (`unit_enumeration` field)

**Ruled 2026-08-13: not fixing.** DE FY2026 denies "the specified areas" and never names
them, so the extraction emits a denied group with zero units against gold's `statewide`.
A `unit_enumeration` schema field was designed and declined because FY2026 is being
dropped from the panel. WI FY2009 is the same shape and remains a known 1-unit residual.

**Reopen if** D-01 lands on option (3) — the field designed there is the same field, and
building it once would close both.

**Third instance (SC/AR run, 2026-08-14).** SC FY2004-c denies a retroactive LSA relabelling
of waivers #970044/#970112 and never names the counties, so the group again carries zero
units. Unlike DE FY2026 this document is not being dropped from the panel, which weakens the
"not worth building" half of the ruling.

**Fourth and fifth instances, both in one document (UT/LA run, 2026-08-15) — and the ruling
should probably be revisited.** `ut-abawd-response-fy2009` is a reconsideration: FNS declines
to revisit its April 2008 denial and separately extends the existing waiver through
2009-01-30 so coverage does not lapse. **Neither group names a single county** — the letter
refers throughout to "the counties identified in the modification" and to "certain counties
and a city" without ever listing them. The agent emitted 2 groups and **0 geographic units**,
which is the honest record and is invisible to every unit-level query.

Three things this changes. (a) The count is now five documents across four states (DE, WI, SC,
UT ×2), so the shape is a recurring FNS drafting habit, not a handful of oddities. (b) It is
the first time the shape hits an **approval** as well as a denial — the bridge extension has
no units either — so `unit_enumeration` would need to cover both, not just denials. (c) UT
FY2009 is a Tier 2 state in the live extraction set and is **not** being dropped from the
panel, which removes the specific ground the 2026-08-13 ruling rested on. Recommend reopening
alongside D-01 and D-20, all three of which want the same "the document did not enumerate;
here is what it said instead" field.

### D-07 · `blanket_national_action` flag

**Specified, not built.** The May 3 2011 "All Regional Directors" memo qualified 46 states
at once, so "applying" in FY2011–13 is a one-paragraph notification carrying almost no
revealed-preference content. Belongs to `2224`.

**The memo is now IN the corpus (SC/AR run, 2026-08-14).** `sc-abawd-response-fy2011` is not
a South Carolina document at all — it is the FNS nationwide broadcast naming the 49 states
and areas that DOL Trigger Notice 2010-2 qualified at once. So the blanket action is not
merely a fact to overlay; it is filed as individual states' "responses" and will be counted
as an application unless flagged. The companion shape is the state-side acknowledgement:
AR FY2011/2012/2013 are one-page notices ("Arkansas will be using the ABAWD trigger notice
specified in the memo from you on …") and SC FY2012 is an email opting into a
pre-qualified SERO-wide waiver. Same event, five documents, two document classes.

**Five more documents, and the criterion is coded three ways (KS/NE/MS run, 2026-08-14).**
Kansas files a state-authored adoption letter in each of FY2011, FY2012 and FY2013 — same
state, same phenomenon, three consecutive years — and blinded agents coded the criterion
`null` (FY2011: "meets the criteria" per an unattached All States Letter, no rule named),
`federal_suspension` (FY2012: the letter says "one of the 46 States that qualify for the
**suspension** of the ABAWD time limits"), and `eb_trigger` (FY2013: "Kansas is a trigger
state"). Mississippi adds two more (FY2011 `federal_suspension`, FY2013 `eb_trigger`). Each
agent coded the words on its own page, correctly. **The criterion field is therefore
tracking the letter's vocabulary, not the mechanism** — and the FY2012 case codes
`federal_suspension` for a period (through 2012-09-30) lying outside BOTH
canonical windows, which the agent flagged explicitly rather than silently reclassifying.
That is exactly the failure D-08's overlay exists to prevent, arriving through a document
class D-07 has not yet defined. Ten documents across four states now belong to this event;
`blanket_national_action` should be built with a `document_class` of its own rather than
inferred per-state.

**MO adds two more, and a sixth state (2026-08-15).** `mo-abawd-response-fy2011` and
`mo-abawd-response-fy2012` are both state-authored Waiver Requests with no FNS decision,
resting on DOL State EB Indicators — FY2011 attaches DOL Trigger Notice 2010-2 (the same
notice behind SC FY2011's broadcast memo), FY2012 cites the Feb 2011 indicators and states
Missouri is "one of 26 states in Tier Four Status EB." Both were coded `eb_trigger`, so MO
happens to land on the third of D-07's three vocabularies without contradicting itself. The
event now spans **twelve documents across six states** (IA, SC, AR, KS, MS, IN, MO — with the
IA FY2011/12/13 memo as the original). Two further MO documents sit adjacent to the class
without being in it: FY2013 is a *bundled* application-plus-approval on the same EB basis
(so FNS did act), and FY2016 is a genuine state-specific extension resting on EUC Trigger
Notice 2013-49. Any `blanket_national_action` flag must therefore be set from document
content, not from "the years 2011–2013" — MO has all four shapes inside that window.

**AL adds a seventh state and a REGIONAL broadcast, which the flag's name does not cover
(2026-08-15).** `al-abawd-response-fy2013` is a forwarded email chain whose underlying message
is an FNS **Southeast Regional Office** broadcast from the regional E&T coordinator to ABAWD
contacts across the region — recipient domains show FL, NC, MS, TN, SC, KY and GA alongside
AL — stating "All SERO states qualify for a continuation of the ABAWD waiver for FY 13,"
with a trigger notice attached that is **not** in the PDF. Alabama's own contribution is one
line: "Alabama will adopt the ABAWD waiver for FY 13."

The event is therefore not purely national. A `blanket_national_action` flag keyed on the
May 2011 All-Regional-Directors memo will not catch this, and the analytic point is identical:
seven states' FY2013 "applications" may all be one-line adoptions of a single regional
determination. Two consequences:

- **Rename and generalise the flag** — `blanket_action` with a `scope` of `national` /
  `regional`, and a field for the issuing office. SERO recurs: SC FY2012's email opts into a
  "pre-qualified SERO-wide waiver," which is the same regional shape already in the corpus and
  was not recognised as such at the time.
- **The AL FY2013 broadcast names its recipients.** That is a directly checkable list of which
  states were covered by this specific action — worth capturing rather than inferring, and it
  cross-validates whatever those states' own FY2013 documents say.

`al-abawd-response-fy2011` is the second AL document in the class (forwarded chain, request
only, no rule named, referenced memo not attached). The event now spans **fourteen documents
across seven states**.

### D-08 · `federal_suspension_in_force` overlay

**Specified, not built.** Whether time limits were in force in a state-year is a pure
function of (state, month) and requires reading nothing; it was removed from
`criterion_code` in v1_5 precisely so 60+ agents stop re-deriving it. Belongs to `2224`.

### D-09 · Deterministic name validator

**Deferred 2026-08-10.** Subsumed later by the merge onto optimal-application data built
from BLS primitives (non-matches flag typos/OCR). Also deferred: NE town adjacency,
`bundle_contiguous` schema field.

---

## SETTLED

Recorded in full in `2222_extract_claude_protocol.md`'s v1_5 section; summarised here so
this file is a complete index.

| # | Decision | Ruling | Date |
|---|---|---|---|
| S-1 | Federal suspension: calendar or disposition? | **Disposition-based.** Code the basis the document's decision rests on; a recital is not a group; anchor the window test on the waiver period, not the signature date. Verified holding on WV FY2020/FY2021 and WY FY2011-a in the v1_5 run. | 2026-08-13 |
| S-2 | IA FY2011/12/13 `federal_suspension` vs `eb_trigger` | **Gold was wrong** → `eb_trigger`. All three cite 7 CFR 273.24(f)(2) + a DOL EB determination and sit in neither suspension window. | 2026-08-13 |
| S-3 | ND FY2006 Rolette | **Gold right, extraction wrong** → `pct20_above_natl`. The arithmetic settles it: the group as printed is 6.58 → 6.6 against a 6.6 threshold; drop Rolette and it falls to 5.43 and fails. | 2026-08-13 |
| S-4 | ND FY2003 Mountrail/Sioux | **273.24(g) exemptions are not a waiver.** New `group_action` value `withdrawn_by_state` + group field `state_alternative_coverage`. An area merely observed as eligible but never requested gets no group and goes to `request_level.notes`. | 2026-08-13 |
| S-5 | WI FY2005 "collision" | **Validator defect, not extraction defect.** `_resolve_multi_doc` keeps the candidate agreeing with gold and prints every contested unit with competing doc stubs. | 2026-08-13 |
| S-6 | Worked examples in the spec | **An example must be a pattern, not a document.** Never a real unit, rate, count, serial, or state/FY from the corpus. Eleven leaks removed from `2220b`/`2220c`. | 2026-08-13 |

---

## Pending work that is not a decision

Tracked here only so it is not lost; these need doing, not ruling.

1. **The 9-doc adjudication re-run** under `fe5d1b3c`: WI FY2005 ×2, FY2009, FY2011,
   FY2021; IA FY2011/12/13; ND FY2003, FY2006. Expected: WI criterion +2, ND action +2
   with `alt_coverage` 2/2, ND FY2006 criterion +1.
2. **The 6 leak-affected docs** (WI FY2003 + 5 NC) — their scores were measured under a
   leaking prompt and are not clean evidence. Whether WI FY2003's 74/75 was earned is not
   knowable from existing runs.
3. **`2122` unified inventory** — content-hash both streams into one `document_id` ledger,
   dedupe, link response↔application. Note from the WV run: **four files named "response"
   are actually state requests** (WV FY2012/FY2013, WY FY2011-a/FY2012), so the FNA
   filename convention is not trustworthy for `doc_class`. **KY/GA run adds three more
   shapes:** (a) `ga-abawd-response-fy2007` is the state request and
   `ga-abawd-response-fy2007-a` is its matching FNS response — same serial 970088, same 13
   groups / 91 counties — so the response stream carries a **request/response pair under one
   FY**, which `2224` must not union; (b) `ga-/ky-abawd-response-fy2011` and
   `ky-abawd-response-fy2013` are Outlook email chains, not Waiver Response forms (GA FY2011
   yields zero groups — FNS only acknowledges receipt); (c) `ga-/ky-abawd-approval-2018` are
   approval-year filenames over calendar-year periods (see D-03). `doc_class` has to be read
   from content, not parsed from the name.
4. **Extractor A (OpenAI, `2221`)** — cost-gated. Text-only path cannot read the scanned
   FY2002–2013 docs.
5. **`2220b`/`2220c` contradict each other on `criterion_other_explanation` — a bug, not a
   decision (UT/LA run, 2026-08-15).** `2220b`'s two-label tie-break (added in v1_5 from the
   ND FY2006 Rolette adjudication) instructs recording a unit's secondary criterion label in
   `criterion_other_explanation`. `2220c` restricts that property to
   `criterion_code = "other"`. **Two agents hit this independently** (UT FY2005 for
   Garfield/Duchesne, which FNS explicitly moved from the LSA list into the 20%-rule
   sub-districts "to avoid having the same counties listed as approved for both"; UT FY2007
   for San Juan, printed inside a 20%-rule aggregate table while the prose attributes its
   qualification to LSA designation). Both followed the schema, both dumped the second label
   into `criteria_summary_text` free text, and both flagged the tension. So the v1_5 tie-break
   currently has no queryable home for its output. Fix by either widening the schema property
   or adding a dedicated `criterion_code_secondary` — and note this is the same field surgery
   D-16 option (3) contemplates, so settle them together rather than patching twice.
6. **State in `2220b` that these tables print 24-MONTH CUMULATIVE COUNTS, not levels (UT/LA
   run, 2026-08-15).** The BLS tables on the modern Waiver Response form give summed unemployed
   and labor-force counts over the 24-month window, so the labor force reads ~24× the state's
   or county's actual figure. **Four agents flagged this as document corruption** — LA FY2017-b
   ("roughly 25x Louisiana's actual labor force … not credible at face value"), UT FY2007
   (West Valley City 1,450,924, "orders of magnitude too large … looks like a copy-paste"),
   UT approval-2018 (Carbon County 203,897, "probable extra-digit error"), and LA FY2020
   (worked out the ×24 relationship correctly but still listed it under flags "worth a QC
   eye"). Only LA FY2008's agent identified the convention outright and verified it by summing
   the columns against the document's own printed rate. Every one of these is a **false**
   verification-checklist item that costs a human a PDF re-read. The tell is that the totals
   reconcile exactly. One sentence in `2220b` removes the whole class. (Cross-reference D-25,
   which decides whether the derived per-unit rate gets a column.)
7. **The work-list is PDF-only and silently skips one real document (UT/LA run, 2026-08-15).**
   `fna_extraction_results.build_worklist` enumerates `RESP_DOCS_DIR.rglob("*.pdf")` plus
   `rglob("*.PDF")` (line ~329). The download manifest holds **1,135 rows, of which 4 are not
   `.pdf`**: three uppercase `.PDF` (MS/RI/WI FY2011 — handled by the second glob) and **one
   legacy Word file, `ut-abawd-response-fy1999-a.doc`**, which no glob matches. It is a
   complete 2-page FNS Waiver Response (serial 970138, Word for Windows 95, last saved
   1999-11-22) and it was invisible to every run to date — the progress table's "21/22" for
   Utah is this file, not a failed extraction. It has now been extracted from a `textutil`
   text conversion and written to
   `claude_v1_5_adjud/FY1997-1999/ut-abawd-response-fy1999-a.json`, but **`collate` and the
   ledger still cannot see it**, because they key off the same PDF-only work-list. Two things
   to do: add a non-PDF branch (or a conversion step) to the work-list builder, and assert
   that the work-list's document count reconciles against the manifest so the next such file
   fails loudly instead of vanishing. Note this is the *only* instance corpus-wide, so the
   cost of leaving it is one document — but the cost of the silent-skip behaviour is unbounded.
8. **Corpus-integrity sweep: a page from another state inside a state's PDF (UT/LA run,
   2026-08-15).** Page 5 of `la-abawd-response-fy2001` is a spreadsheet headed "**ARKANSAS**
   ABAWD WAIVER REQUEST FOR FY 2001 UNEMPLOYMENT" — wrong state, no Louisiana content. It
   contributed nothing to that extraction because the agent recognised it, but a text-only
   extractor would have merged Arkansas rates into a Louisiana document. This is a scrape/
   source-side defect, distinct from the doc-class problem in item 3: the *file* is the right
   document, one *page* is not. Worth a cheap sweep — for each PDF, flag any page whose
   state-name mentions disagree with the filename's state code.

---

## Gold-sheet corrections — WV and WY (2026-08-15)

A **fourth** kind of content: places where scoring the run against a gold sheet showed the
**gold** to be wrong. The sheets are hand-maintained `.xlsx` outside version control, so a
correction has no other durable home, and an uncorrected gold cell permanently mis-scores
every future arm.

WV is the largest sheet in the project (547 scored units vs WI's 298) and, at
`sha256=8117ce4c`, scores against `claude_v1_5_adjud` (`fe5d1b3c`):

| basis | name | action | criterion |
|---|---|---|---|
| exact | 496/548 (90.5%) | 494/496 (99.6%) | 474/489 (96.9%) |
| canonical | 498/547 (91.0%) | 496/498 (99.6%) | 476/491 (96.9%) |

**Every one of the 66 disagreements was adjudicated against the source PDF. None is an
extraction error.** Adjudicated, the run is 501/501 name · 498/498 action · 491/491
criterion. Detail below; items A and B need edits to the sheet.

### A. Gold is wrong — the extraction is right (verified against the source)

| # | FY | units | gold | extraction | evidence |
|---|---|---|---|---|---|
| A-1 | 2006 | Calhoun, Clay, Grant, Jackson, Mason, Ritchie, Roane, Tyler, Wetzel, Wirt, Lincoln, Mingo, McDowell, Wyoming (**14**) | `percent_20` | `lsa` | The document groups counties into three named Regions and then **splits each region's list in prose by criterion**: "Calhoun, Clay, Grant, Jackson, Mason, Ritchie, Roane, Tyler, Wetzel, and Wirt counties are currently eligible as labor surplus areas (LSAs). Barbour, Braxton, … qualify for a waiver based on the area's aggregate average unemployment rate…" (same shape for Region 3: Lincoln/Mingo/McDowell/Wyoming LSA, Boone/Logan 20%). Gold coded the whole region `percent_20`. Text layer is clean — `pdftotext -layout` reproduces it verbatim. |
| A-2 | 2000 | Wayne (**1**) | `percent_20` | `lsa` | Gold recorded the basis the **state requested**; FNS's field 9 approves on a different one: "We are also approving exemptions for Mineral and Wayne Counties **based on LSA designation** although the State agency was apparently not aware that both counties are designated LSAs" — the state had asked under the 20% rule believing Huntington City was not designated; FNS checked 64 FR 55969 and found both Huntington City and the balance of Wayne separately listed. Scanned doc, read from page images (970037, p. 2). |

A-2 is the **requested-vs-dispositive criterion** distinction of **D-16**, arriving from the
gold side rather than the extraction side. Note it is *not* a denial, which is the only case
D-16 currently contemplates — FNS can substitute its own theory on an approval too. That
widens D-16's scope and strengthens option (3) (`criterion_code_requested` alongside
`criterion_code`): here both facts are on the page and the single field can only hold one.

These 15 units are the **entire** criterion gap. Fixing them takes WV to 491/491.

### B. Gold transcription typos beyond the repair rule's reach

`_repair` snaps a near-miss only when it is within two edits of exactly one reference name.
These are three or more edits, so they can never match and each costs a name point:

| FY | gold cell | intended | extraction has |
|---|---|---|---|
| 2002 | `Wettz` | Wetzel | `Wetzel` ✓ |
| 2018 | `Min` | Mineral | `Mineral` ✓ |
| 2019 | `Jackk` | Jackson | `Jackson` ✓ |
| 2019 | `Raand` | **Randolph** | `Randolph` ✓ |

`Raand` is the one to watch: it *is* within two edits of `Roane`, and `Roane` is separately
present in the same year, so the repair rule silently snapped it onto a duplicate and shrank
the FY2019 denominator 37→36 rather than flagging it. The extraction's FY2019 unit list is
exactly right (all 37); gold has the two typos. **A near-miss that resolves to a name already
present in the same fiscal year should be reported, not snapped** — worth a guard in `2225`.

### C. Gold coverage gaps (not scored, but the sheet is incomplete)

- **FY1999** collects only waiver **#970036** (17 counties, the 10-percent form) and omits
  **#970037** entirely — the LSA form on the same PDF, carrying 27 more counties, which the
  extraction picked up in full. Gold's 17 score 17/17 · 17/17 · 13/13.
- **FY2004** omits **Boone** (extraction: approved, LSA).

### D. Not errors on either side — convention

- **FY2016-b, 46 units.** D-01, above. The single largest line item in the eval.
- **FY2012 / FY2013, 2 units, `group_action`.** Gold says `approved`; the extraction leaves
  it null. **The extraction is right on the document.** Both PDFs, despite their `-response-`
  filenames, are one-page **outgoing state request letters** (WV DHHR → FNS MARO, 2011-07-20
  and 2012-07-05, citing 7 CFR 273.24(f)(2) and DOL Trigger Notice 2010-2) containing no FNS
  Waiver Response form and no decision. Both were coded `document_type = state_request_only`.
  Gold recorded the **outcome it knows** rather than the document's content — which is
  precisely the `status` vs `group_action` split already open as **D-05**, and these two rows
  are the cleanest evidence for it in the corpus. They are also two of the ten documents
  belonging to the blanket-national-action class of **D-07**.
  These 2 units are the **entire** action gap.
- **`Wheeling` emitted in FY2002-b and FY2004** as a second unit alongside an
  approved-in-its-entirety `Marshall`, flagged `non_standard_geography = true`. Faithful to
  FNS's stated reasoning (the sub-0.5% Wheeling-city sliver was folded in rather than carved
  out) but it double-lists territory already inside Marshall. Harmless for scoring (the
  denominator is gold), a real double-count for `2224`.

### E. Method note

10 of WV's 23 documents are image-only (`textchars == 0`): FY1999–FY2003 and FY2012/13, i.e.
the whole pre-2004 record. The extraction's accuracy there is indistinguishable from the
text-layer years — FY1999 17/17, FY2001 42/42, FY2003 31/31 — which confirms the agents are
reading page images, not `pdftotext`, and that the "image-only" wart is an OCR *cost*, not an
accuracy risk. This is the first direct measurement of that on a scanned-majority state.

### F. Validator change made for this eval

`_CRIT_CANON` in `2225` gained `percent_10_statutory → pct10_statutory`. The WV sheet spells
the statutory-10% code that way; unaliased it passed through raw and failed against the
extraction's `pct10_statutory` on all **53** FY1999–FY2000 rows — a pure vocabulary artifact
of the kind the map already exists to absorb (cf. the WI/ND vs DE/IA vintages). WY uses the
same spelling, so the alias serves both.

### G. WY (`sha256=a8abe1e1`, 9 rows, FY1999–2013)

Tiny sheet — one row per fiscal year, 9 units — but it covers the **entire** WY corpus
(10 docs; FY2005 holds two). Score vs `claude_v1_5_adjud`:

| basis | name | action | criterion |
|---|---|---|---|
| exact = canonical | **9/9 (100%)** | 6/9 (66.7%) | **8/8 (100%)** |

**Adjudicated: 9/9 · 9/9 · 8/8. No extraction error.** The three action misses:

| FY | gold | ext | verdict |
|---|---|---|---|
| 2013 | `rejecte` | `denied` | **Gold typo** — a dropped `d`. `_norm_action` folds `denied`/`rejected` onto `not_approved`; `rejecte` is not in the map, so it fails against a substantively identical value. **Fix the cell.** Do *not* alias it — a typo is not a vocabulary variant, and aliasing it would hide the next one. |
| 2011 | `approved` | null | **D-05.** `wy-abawd-response-fy2011-a` is a state request, and **gold itself codes `document_type = state_request_only`** while still recording an action. Gold is holding "was coverage achieved", the extraction "what did FNS do on this page". |
| 2012 | `approved` | null | Same. Also **D-07** — both are blanket-national-action documents. |

**The interesting result is the name column.** WY's whole record is the Wind River
Reservation, and the state pursues it by applying for **Fremont County** (99% of the
reservation's population), the reservation itself having no BLS/LAUS series. Gold resolves
this to the substantive target: `geographic_unit_name = "Wind River"`,
`area_type = "reservation area"`. **Seven blinded agents independently reached the same
resolution** — same name, same `area_type` string, `non_standard_geography = true`, with
notes recording the Fremont/Hot Springs census-share apportionment FNS used to derive a
reservation-level rate. That is convergence on an *interpretive* call, not an orthographic
one, and it is the first evidence that the geo-context reservation tables are doing work
beyond spelling. Contrast WV FY2016-b (D-01), where two agents reading the same spec split.

### H. WY FY2005 is a clean second instance of D-02 (supersession)

The corpus holds both halves of one action under serial 970264:

| doc | date | action | text |
|---|---|---|---|
| `fy2005` | 2005-03-10 | **denied** | FNS recalculated Fremont's 24-month rate as 6.4% against a 5.9% national average, and faulted the state for not following the April 22 2004 "New Method for Calculating Average Unemployment Rates" memo |
| `fy2005-a` | 2005-04-11 | **approved** | "This is a correction to our memorandum dated March 10, 2005, which originally denied the Wyoming State Agency's request… a subsequent review found a **typographical error in the census share data** for Fremont County; corrected, the Reservation's recalculated rate is 7.3 percent" |

Gold carries one FY2005 row (approved). `_resolve_multi_doc` landed on the right document —
but by the agrees-with-gold tie-break, **not** by supersession logic, so an ungolded state
with this shape would be scored on a coin flip and `2224` would union a denial with its own
correction. This is D-02's option (1) fact pattern in its purest form: the trigger language
is explicit, dated, and names the superseded memo. Note it is *cleaner* than the WV FY2018
pair — there the two letters disagree about which counties are sub-threshold and neither
says which is authoritative in so many words; here the later letter says so outright.

Second corpus instance of **FNS's own clerical error preserved rather than smoothed over**
(WV FY2018 was the first) — and here the error is *named* by FNS itself. Worth keeping for
the paper's transcription-fidelity argument.

### I. Status of the WV corrections

As of `sha256=1be591fc` (2026-08-15 01:16) the WV sheet has been re-saved — 64 → 65 columns —
but **the A-1/A-2 criterion corrections and the B typos are not yet applied**: row counts and
the criterion distribution are unchanged, and the score is bit-identical (498/547 · 496/498 ·
476/491). The eval above still stands against the current sheet.

---

## Verification checklist — KY/GA run (2026-08-14)

Things flagged during extraction that need **checking against the source PDF**, not ruling
on. Each was recorded by a blinded agent in `request_level.notes` or a group evidence field
and transcribed faithfully rather than silently corrected — which is the wanted behaviour,
but it means the corpus now carries known-suspect cells. Grouped by whether an error would
change a number.

### A. Would change extracted values — check first

| # | doc | what to check |
|---|---|---|
| A-1 | GA FY2016-b | **Two different data windows for one decision.** Cover letter + field 7 say May 2013–Apr **2014**, national 6.8% (→ 8.1% threshold); the BLS table that mechanically produces the approval says May 2013–Apr **2015**, combined 7.7% vs 7.7%. Extraction anchored dates on the table and the national rate on the narrative — an internally inconsistent pair. Decide which governs. |
| A-2 | GA FY2004 | **Two national-average figures for the same CY2001–02 window.** Counties paragraph derives 5.3 × 1.20 = 6.3; cities paragraph says rates were "at least 20 percent above the national average of 6.3," implying a 7.56 threshold under which 6 of 9 approved cities fail. Agent read it as a drafting error and coded `per_unit`; if the literal reading is right, those cities are `joint_aggregate`. |
| A-3 | GA FY2007-a | Same defect, different year: threshold printed as **6.2** (field 8 opening + Atkinson) and **5.9** (the paragraph before the SDR tables + Clinch) for the same Nov2004–Oct2006 window. No outcome changes, but one of the two is wrong. |
| A-4 | KY FY2007 | **36-month data window** (Nov 2003–Oct 2006), not the standard 24. Flagged `nonstandard_averaging = true`. Confirm the window is really as printed — if so this is a genuine methodology departure worth its own analysis, not just a flag. |
| A-5 | GA FY2005 | Field 16 national-office action date prints **2004-04-21**, before the state's own 2005-02-28 request. Signature block reads `VRobinson:4-21-05`. Transcribed as printed. |
| A-6 | KY FY2003 | Field 16 prints **2002-02-25** against a Feb-2003 document. Transcribed as printed. |
| A-7 | GA FY2001 | Field 13 expiry **hand-corrected** by strikethrough from 2001-11-30 to 2002-02-28. Extraction treated the handwriting as authoritative; the surrounding prose still says November. Genuinely underdetermined — check the scan. |
| A-8 | KY FY1999 | Expiry **2000-02-28** (item 13) vs **2000-02-29** (summary-table caption). Leap-year off-by-one; item 13 used. |
| A-9 | KY FY2026 | Field 7 says the waiver rests on "**one county** having a three-month average rate over 10 percent," but Table 1 prints five counties all independently over 10% and calls them "five individual counties." Coded 5 `per_unit` groups. If "one county" is literal, the group structure is wrong. |

### B. Counts that do not reconcile inside the document

| # | doc | what to check |
|---|---|---|
| B-1 | GA FY2002 | Field 8: prior waiver 50 counties, 43 continue, 8 added = 51 (matches the table) — but only **6** dropped counties are named where 50−43 implies 7. A 7th is unnamed. |
| B-2 | GA FY2001 | Item 8 calls **Dooly** one of two counties "being added," yet its own transcription of the prior 55-county list already contains Dooly. |
| B-3 | GA FY1999 | **Quitman** appears in the prior-waiver list (42 counties) but not in the 41 continuing, nor in the approved list, nor in the cover letter's arithmetic. Dropped with no group. |
| B-4 | GA FY2008 | Cover memo and field 7 say waiver 2080015 covers "**six**" multi-county regions; the tables present **eight** named sets plus six stand-alone areas. Groups taken from the tables. |
| B-5 | GA FY2007-a | Field 8 says "**four** sub-regions"; the document presents 11 SDR bundles + 2 standalone = 13 groups. Read as stale boilerplate. |
| B-6 | KY FY2006 | Cover memo says "**15** Area Development Districts"; field 8 says "**fourteen** areas … Sub-regions of one of the fifteen ADDs." 14 groupings + standalone Nicholas extracted. |
| B-7 | KY FY2007 | Only **14 of 15 ADDs / 93 of 120 counties** appear. The Louisville–Jefferson ADD (and Fayette/Lexington) are absent with no explanation — confirm this is the state's choice and not a missing scan page. |
| B-8 | KY FY2006 | **Lake Cumberland** sub-region has no explanatory sentence, unique in the document — likely a scan/formatting gap. Its `joint_aggregate` call and per-county `qualifying_basis` were inferred from arithmetic alone. Highest-uncertainty group in the KY set. |

### C. Transcription / OCR calls made against the geography reference

Each preserved the printed form in `orig_text`; verify the canonical `name` is right.
`Rookcastle`→Rockcastle (KY FY2007) · `Case County`→Casey and `Elliot`→Elliott (KY FY2006) ·
`Mclean`→McLean (KY `approval-2018`) · `Mcintosh`→McIntosh (GA FY2016-b, FY2017,
`approval-2018`) · `Randolnh`→Randolph, `Snalding`→Spalding (GA `approval-2018`) ·
`Head`→Heard (GA FY2000) · `Dekalb`→DeKalb (GA FY2007) · `7 CPR 273.24`→`7 CFR` (GA FY2017).
Two word-splits, both of which change unit counts if wrong: **`Glascock Monroe`** with no
comma read as two GA counties (FY2002), **`Greenup Hancock`** read as two KY counties
(FY1998-b — corroborated there by the document's own "56" total).

Also: **KY FY2026's text layer is corrupt** — `Lewis Countynty, KY`, `Martin Countyartin
County, KY`, `Wolfe Countynty, KY`. The agent used the image rendering as ground truth.
Any `pdftotext`-based pass over this document will produce garbage.

### D. Recurring traps to encode as assertions in `2224`

1. **Macon county vs Macon city** — distinct units sharing a name, present together in GA
   FY1998, FY2000, FY2002, FY2004, FY2006. Flagged `possible_double_counting = false` each
   time, but a naive name-keyed join *will* collapse them. Pre-2014 only; Macon–Bibb
   consolidated in 2014, so the crosswalk changes mid-panel.
2. **Balance-of-county units** — `Warren (less Bowling Green City)`, `Christian (less
   Hopkinsville City)`, `Liberty (less Hinesville City)`, `Henderson City` vs balance of
   Henderson County. County-level aggregation double-counts unless these are handled.
3. **`state` column is not normalised** in the flat CSV: 2,516 rows say `Georgia`/`Kentucky`
   and 2 say `GA`/`KY`. `state_code` is correct throughout — key on that, and consider
   normalising `state` in the flattener.
4. **GA FY2011 legitimately has zero groups** (an FNS email acknowledging receipt, no
   decision) with `non_conforming_document = false`. Any "every document yields ≥1 group"
   assertion will false-positive here.

### E. Corpus-wide sweeps these motivate

- Null `fiscal_year` across all 1,135 docs (D-03) — the `approval-<year>` shape is systematic.
- "not requesting an extension" / "no longer designated" frequency (D-12) — sizes the
  ≈44-area gap corpus-wide.
- "entire State except" partial-statewide pattern (D-01).
- Documents printing a set-level rate but no per-unit rates or counts (D-10) — this is the
  `qualifying_basis = unknown` population and it grows with document vintage.
- Bundles whose aggregate rate equals the threshold to the printed precision — five in
  KY/GA plus ND FY2006. Worth a corpus-wide count as a paper exhibit.

---

## Agent judgment calls and deviations — SC/AR run (2026-08-14)

Every call a blinded agent made that the spec did not determine, plus the deviations from
protocol. This is a *third* kind of content: not a decision awaiting a ruling (D-nn), and
not a suspect transcribed value (the verification checklist below) — it is the set of places
where two competent agents reading `2220b` could have written different JSON, and where the
one that got written is therefore a choice rather than a reading. Skim A and B; they are the
ones that move numbers.

### A. Calls that change row counts

| doc | the call | effect if wrong |
|---|---|---|
| AR FY1999-a | prior "33 counties and one city" waiver referenced as background, never enumerated → **no group** | 34 areas unrepresented |
| AR FY1999-b | same, for a prior 26-county waiver → **no group** | 27 areas unrepresented |
| AR FY2000 | Pine Bluff City merged into the Jefferson County line as the document does → **not emitted separately** | 1 unit, and it is a city/county boundary case |
| AR FY2001 | page-3 spreadsheet lists 7 counties with FY2001 data that the letter never adjudicates → **no group** | 7 areas |
| AR FY2004 | **Perry County** is in the 33-county request but appears in neither the Delta table nor the approval sentence → **no group** | 1 area, disposition simply absent from the page |
| AR FY2005 | Jacksonville City and Pine Bluff City named as LSA-designated but never requested → **no group** (case (c)) | 2 areas |
| AR FY2006 | ~15 counties dropped from the original 42-county DRA request → **notes only** (D-12) | 15 areas |
| AR FY2008 | Benton and Washington appear in neither list → **no group** | 2 areas; note the other 73 are the whole state |
| SC FY1999 | the 6-county 970044 request is split across two serials in the final action (Chester, Georgetown, Lee, Marion land under 970112/LSA) → coded as **reclassification**, no denied/withdrawn group | 4 areas' action history |
| SC FY2000 | 7 previously-LSA areas dropped → **notes only** (D-12) | 7 areas |
| SC FY2003-b | 3–4 areas dropped or reassigned → **notes only** (D-12) | 3–4 areas |
| SC FY2004-b | two other pending requests "folded into" the statewide grant → treated as **recital**, no groups | a whole 20%-rule county request with no row |
| SC FY2004-c | 970044 and 970112 collapsed into **one** denied group; the agent flags that a stricter reading of the splitting rule gives two | 1 group, and the group is already 0-unit (D-06) |
| AR FY2008 | field 9 is boilerplate from a different response (wrong window, names an LSA city absent from the document) → transcribed verbatim, **no phantom group created** | correct call; the opposite would invent a group |

The recurring shape: **"referenced but not adjudicated here" → no row.** That is defensible
per case (c), and it is also how ≈30 areas in this pair vanish. D-12 is the ruling that
decides all of them at once.

### B. Calls that change a coded value

1. **AR FY2000 Conway → `other`, six SC documents' "insufficient jobs" → `lsa`.** The D-13
   split. Affects 100 SC unit-rows and 1 AR row directly, and the comparability of every
   `lsa` count across pre-2006 states.
2. **AR FY2003's five 20%-rule counties → `per_unit`.** No individual rates are printed, so
   the decisive arithmetic could not be run. The agent inferred `per_unit` from the
   sentence's structural parallel to the LSA list and the absence of aggregate language, and
   explicitly flags that `unknown` is defensible. 5 units.
3. **AR FY2002's 19-county group → `joint_aggregate`.** Forced by two printed rates
   (Arkansas 5%, Baxter 4.8%) sitting below the threshold inside a group FNS's prose says is
   entirely above it. If those are OCR truncation — plausible, since Fulton's prints as a
   garbled `.7%` — the qualification level is wrong for 19 units.
4. **AR FY2011/2012/2013 → `eb_trigger`, `approved`, `state_request_only`.** All three
   inferred. The documents are state letters that say only "the ABAWD trigger notice
   specified in the memo from you"; they never say Extended Benefits, cite no IUR/TUR, and
   record no FNS action. FY2013's agent names this "the single largest source of
   classification risk here." 3 documents, 3 state-years.
5. **SC FY2012 → `state_request_only` with `criterion` and `action` both null.** The agent
   flags `non_conforming_document` as the competing call. The actual basis lives in
   attachments not in the PDF.
6. **SC FY2002-a Fairfield coded under both serials** (`possible_double_counting = true`)
   rather than deduplicated, because the approval table prints it twice even though the
   narrative moves it. 1 unit, double-counted by construction.
7. **AR FY2003 Crittenden** appears as `Crittenden (less West Memphis City)` in the LSA
   group and as plain `Crittenden` in the Delta aggregate, with no statement whether the
   carve-out carries. Kept both, flagged. Drives most of the 67 double-counting rows.
8. **SC FY2000 `soft_criterion_invoked = false`** for "insufficient jobs", on the ground
   that the document defines the phrase as LSA designation (a hard criterion). Consistent
   with the `lsa` coding in B-1 but the two calls are independent and should move together.
9. **SC FY1999 `non_bls_source` left null, not true**, despite "based on data furnished by
   the State agency" — the agent judged that suggestive rather than affirmative. AR FY1999-a
   set it `true` on comparable language. Only 2 rows corpus-wide carry `true`, so this field
   is currently too sparse to trust.

### C. Calls on dates

- **Two candidate response dates, stamp chosen over typist line:** AR FY1999-b (Dec 10 vs
  12/9/98), AR FY2000 (stamp 1999-12-06, field 16 blank), SC FY1998 (stamp, field 16 blank),
  SC FY2000 (APR 11 2000 stamp vs a typed 4/6/00).
- **Two candidate request dates:** SC FY2001 (memo says Dec 11, field 17 says Dec 28 — field
  17 used); AR FY2008 (memo 2007-04-14 vs field 17 2008-04-14, a full year apart — field 17
  used).
- **Effective date left null rather than inferred:** SC FY1998 970112 (no start stated; the
  agent declined to infer 1998-03-01 from the 1-year framing), SC FY2011, AR FY2011/12/13.
- **Approved period preferred over eligibility window:** AR FY2016 records Oct 1–Dec 31 2015
  (what was granted), not the Dec 2014–Dec 2015 window the letter narrates as available.

The convention that emerged and should be written into `2220b`: **date stamp beats typist
line; form field beats cover memo; never infer a start date from a stated duration.** All
three were applied consistently here, but by convergence rather than instruction.

### D. Fields the schema does not cleanly accommodate

1. **Form field 18 prints backwards.** "Date of regional office transmittal of *response* to
   *National office*" runs opposite to the normal routing. Three agents resolved it three
   ways: SC FY2001 → `date_ro_transmittal_request` (matched the drafting stamp), SC FY2003-b
   → `date_ro_transmittal_response` with a caveat, SC FY2002-a → **both left null**, raw
   value in notes. Same printed field, three encodings.
2. **Which name is `fns_official_name`?** SC FY2016-a carries a decision-signer (Chief,
   Certification Policy Branch) and a separate "FNS regional contact"; the agent used the
   signer and asked whether that matches the arm's convention. Likewise `state_official_name`
   from field 18's contact rather than the letter's addressee. Unstated in `2220b`.
3. **Expiration printed as a range**, not a date (SC FY2016-a: "October 1, 2015 through
   December 31, 2015") → transcribed verbatim rather than forced into one value.

(1) and (2) are cheap to settle and should be one-line additions to `2220b`; they are
currently costing cross-document comparability on four date/name fields.

### E. Protocol deviations

**Six of 29 agents ran `ls`/`find` under `1022_extractions/` before writing**, in violation
of the explicit prohibition in their prompts: AR FY1999-b, FY2003, FY2004, FY2012, FY2013,
SC FY2012. All six self-disclosed unprompted. In every case what was exposed was sibling
*filenames* only — never contents — and always of other states' documents, and every agent
stated its extraction judgment was already fixed before the listing.

**Assessment: the arm is not contaminated.** A filename of the form
`ga-abawd-response-fy2000.json` carries no answer for an Arkansas document. But the rate is
now 6/29 (≈21%) here against roughly a dozen in KY/GA, i.e. it did not fall when the
prohibition was present in the prompt from the start — which is the KY/GA fix, and it did
not work. The failure mode is mechanical, not motivated: agents `ls` to confirm a directory
exists before writing to it. **Recommended change:** state in the *write* step that the
directory is guaranteed to exist and that no check is needed, rather than relying on a
prohibition in the blinding block several hundred words earlier.

### F. Where the agents were right to refuse

Worth recording because these are the spec working:

- AR FY2008 declined to build a group from field 9's stale boilerplate.
- AR FY2005 coded all 42 units `qualifying_basis = unknown` rather than guessing, once the
  labour-force table proved internally impossible (unemployed exceeding labour force).
- SC FY2011 did not emit a group for the recited ARRA suspension — the S-1 rule holding.
- SC FY1998/AR FY1999-a left effective dates null rather than back-computing them.
- AR FY2002 kept the printed 19-county bundle despite non-contiguity, recording the tension.

---

## Verification checklist — SC/AR run (2026-08-14)

Per-document facts to check against the source PDFs. Same status as the KY/GA checklist:
these are not decisions, they are suspect cells that agents transcribed faithfully rather
than corrected, and they are only findable by re-reading free text.

### A. Would change extracted values

1. **AR FY2005 — the 42-county DRA table is arithmetically broken.** Unemployed exceeds
   labor force for Monroe and Phillips; Prairie, Pulaski and Randolph carry implausibly
   large totals; Pulaski's figure prints as `23,3557`. The combined rate FNS approves on is
   **14.8%** against a 6.8% threshold, which is not credible for CY2003–04 Arkansas and is
   almost certainly a consequence of the same corruption. All 42 units are coded
   `qualifying_basis = unknown` as a result. Check whether the printed table is a scan
   artifact or a genuine FNS error — it decides whether 42 units are recoverable.
2. **AR FY2003 — `129 percent` vs `120 percent`.** Field 8 (the state's request) says the
   five counties exceed "129 percent" of the national average; field 9 (FNS's approval) says
   120 percent for the same five. 120 is the standard cutoff and matches FNS's own later
   arithmetic, so 129 is probably a typo — but it was not silently corrected.
3. **AR FY2008 — field 9 appears to be boilerplate from a different response.** It cites an
   accounting period of Nov 2004–Oct 2006 and states "the city of Hot Springs was indeed a
   Labor Surplus Area," while the tables and field 8 both use Dec 2005–Nov 2007 and no
   LSA-coded group or Hot Springs unit exists anywhere in the document. Transcribed verbatim
   into `action_reason_approval_denial`; no phantom group was created. Confirm.
4. **AR FY2008 — state request date differs by exactly one year** between the cover memo
   (2007-04-14) and form field 17 (2008-04-14). Field 17 was used.
5. **AR FY2002 — the Stone County denial sentence is missing a negation.** "The county's
   unemployment rates were **not below** 120 percent of the national averages … so they do
   not qualify" reads as the opposite of the outcome. Coded `denied` on the arithmetic
   (4.3% vs 5.28%/5.88%) and the stated conclusion.
6. **AR FY2002 — two rates may be OCR-truncated.** Arkansas County (5%) and Baxter County
   (4.8%) print below the 5.28% threshold inside a group FNS's prose says is entirely above
   it; Fulton's rate prints as a garbled `.7%`. The arithmetic is what forced
   `joint_aggregate` rather than `per_unit`, so if these are scan damage the qualification
   level is wrong.
7. **AR FY2005 — Stone County appears in the approved 42-county table but never in the
   46-area request list**, and the LSA asterisks look swapped: Stone (on the document's own
   FY2005 LSA list) is unmarked, Cleveland (not on it) is marked.
8. **AR FY2005 / FY2004 — header counts do not match the enumeration.** FY2005 says "46
   counties and 1 city" but lists 46 areas total; FY2004's memo says "12 additional
   counties" where the table shows 13.
9. **AR FY2006 — city count contradicts itself.** The itemised list gives 2 cities (West
   Memphis, Hot Springs); the approval paragraph and field 8 both say 3. The list was taken
   as authoritative.
10. **SC FY2000 — garbled expiry text in the field 9 table** (`expires 3/1/01`,
    `expires32/1/01`) conflicts with field 13's "expire on February 28, 2001". Field 13 used.
11. **SC FY2002-a — Fairfield County appears under both serials.** The narrative moves
    Fairfield from #970112 to #970044, and the state's extension request for #970112 names
    only 14 counties (Fairfield omitted) — but the approval table still lists it under both.
    `possible_double_counting = true`. Likely a clerical carryover; confirm.
12. **SC FY2003-b — cover-memo date stamp is overwritten in the scan** (`MAR 1? 2003` vs a
    cleaner `MAR 17 2003`). Read as 2003-03-17.
13. **SC FY2006 — two different national averages in one sentence:** "at least 20 percent
    above the national average of 5.3, or 6.4 percent." `national_unemployment_rate_cited`
    left null. Also a routing stamp reading `2/13/05` on a letter dated 2006-02-17.

### B. Threshold-hugging bundles (extends the KY/GA table)

| doc | bundle | aggregate | threshold | members below it |
|---|---|---|---|---|
| AR FY2008 | 31 counties | 5.6 | 5.5 | **31 of 31** |
| AR FY2007 | Western sub-region (5 cty) | 5.9 | 5.9 | 3 of 5 |
| AR FY2007 | Delta Regional Authority (42 cty) | 5.9 | 5.9 | 14 of 42 |
| AR FY2004 | Delta Regional Authority (42 cty) | 6.4 | 6.3 | ≥6 identified |
| AR FY2006 | Arkansas County (per_unit) | 6.4 | 6.4 | — (own rate == threshold) |

AR FY2008 is qualitatively different from every other row: *all* members are below the
threshold, and the document simultaneously approves 42 other counties that each clear it
individually. The bundle is the exact residual. AR FY2007's two groups landing on 5.9
against a 5.9 threshold in the same document is the second-strongest.

### C. Nonstandard windows and data sources

Twelve unit-rows carry `data_nonstandard_averaging = true`, concentrated pre-2006 where
12-month averaging was the norm: SC FY1999 (12-mo), FY2001 (12-mo), FY2003-b, AR FY2002
Polk (a **3-month** window, mass-layoff driven). SC FY2007 uses a **36-month** window
(Dec 2003–Nov 2006) for the 20% test, which the 2006 guidance does not contemplate. AR
FY1999-a is the only `non_bls_source` case: rates from the AR Department of Economic
Security's website, projected forward through two announced plant closings (5.4% → 10.6% →
17.9%) rather than measured.

### D. Doc-class failures in this pair

- **AR FY2011, FY2012, FY2013** — one-page *state-authored* trigger notices, no serial, no
  form, no FNS action. Filed as `*-abawd-response-*`.
- **SC FY2012** — an Outlook email chain; the state opts into a pre-qualified SERO-wide
  waiver. `approval_criterion` and `group_action` both null. The actual eligibility basis
  lives in attachments not present in the PDF.
- **SC FY2011** — the FNS nationwide broadcast memo listing 49 qualified states (D-07).
  Not a South Carolina document in any meaningful sense.
- **SC FY2004-c** — a denied group with **zero** units (D-06 shape, third instance), and the
  corpus's only purely procedural denial: refused under 7 CFR 272.3(c)(2)(i) because the
  regional office's own email revealed the purpose was rebuilding an exhausted 15% exemption
  balance, not program administration.

### E. Traps for `2224` specific to this pair

1. **Serial 980013 spans FY1999–FY2008 in AR** — ten documents on one serial. Neither
   `(state, FY)` nor `(state, serial)` separates them; only D-04's
   `(serial, coverage-interval, area)` does.
2. **`Crittenden (less West Memphis City)`** appears as a balance-of-county unit in AR
   FY2003/FY2004/FY2005 while plain `Crittenden` appears in the same documents' Delta
   aggregate tables, with no statement whether the carve-out carries over.
   `possible_double_counting = true` on 67 rows, mostly this.
3. **Cities embedded in counties** — Hot Springs/Garland, Jacksonville/Pulaski, Pine
   Bluff/Jefferson (AR); Anderson, Florence, Sumter, North Charleston (SC). AR FY2000 merges
   Pine Bluff City into the Jefferson County line mid-series; AR FY2004 asterisks the LSA at
   county level while field 8 names the city.
4. **AR FY2002's 19-county and AR FY2008's 31-county groups are non-contiguous as emitted**
   (D-11). FY2008's is an artifact of the splitting rule, not a state error — the full
   73-county area is contiguous.

---

## Verification checklist — KS/NE/MS run (2026-08-14)

Per-document facts to check against the source PDFs. Same status as the KY/GA and SC/AR
checklists: not decisions, but suspect cells that agents transcribed faithfully rather than
corrected, and only findable by re-reading free text.

### A. Would change extracted values

1. **MS FY2003 — the Waiver Response form's field 5 ("State") literally reads `Florida`.**
   Everything else in the document is unambiguously Mississippi (subject line, requesting
   agency, all 47 counties, corpus placement). The agent preserved `Florida` verbatim in the
   `state` column and coded `state_name`/`state_code` as Mississippi. This is the strongest
   instance yet of the unnormalised-`state`-column trap already flagged for `2224`: any
   groupby on `state` silently moves 47 county-rows to Florida.
2. **NE FY2011-b — field 16 "Date of national office action" reads `January 4, 2010`**, which
   precedes both the Nov 22 2010 state request it answers and the letter's own `JAN 5 2011`
   stamp. Almost certainly a typo for 2011-01-04; transcribed literally.
3. **NE FY2004 — the Santee Sioux rate is printed twice with different values.** Narrative
   text says 16.0%, the worksheet's computed "Reservation Unemployment Rate" says 16.4%. The
   table value was used.
4. **NE FY2008 — did Thurston County itself get a grant, or only the two reservations?**
   Field 8 records the state adding off-reservation Thurston residents to the request and
   field 9 opens "We are approving the waiver as requested," but the rest of field 9 discusses
   Thurston's LSA status only as the rationale for the reservations. A 4th group was emitted
   on the "as requested" language. This is the single unit-count-changing call in NE.
5. **KS FY2006 — "the State is only requesting to waive ABAWDs residing in the city of
   Wichita."** Read literally that drops Sumner County from the extension; read as limiting
   only the Sedgwick portion (city, not whole county), Sumner stays. Both areas were coded
   approved. Two units turn on this sentence.
6. **KS FY2005 / FY2006-a — the state's request date differs between the cover letter and
   form field 17** (Mar 5 vs Mar 3 2005; Mar 7 vs Mar 5 2006). Field 17 was used.
7. **KS FY2004 — "Initial" vs "revision."** Form field 2 says Initial; the cover memo calls
   it "a revision to the waiver approved on June 4, 2004."
8. **KS FY2005 — the LWIA-Four data window prints two ways**, Mar 2002–Feb 2004 in the field-8
   table and "March 2002 through April 2004" in field 9.
9. **MS FY2011 — the state's letter misstates the ARRA window**, asserting the suspension runs
   "through September 30, 2011" against the KB's canonical 2010-09-30. The requested period
   therefore lies wholly outside the real window even though the letter was signed inside it.
   Coded on the document's own basis with the tension recorded, per the v1_5 waiver-period
   anchoring rule.

### B. Internal count and citation mismatches

10. **KS FY2006-a — the cover letter says FNS is "approving two Sub-Area Local Workforce
    Areas"; the form supports three evaluated sets** (two county bundles plus standalone
    Hutchinson). Three groups were emitted.
11. **`7 CFR 274.24` for `273.24`** in KS FY2004, FY2005, FY2006-a and FY2007 field 3 — the
    same typo on four Kansas forms, transcribed verbatim each time. Worth a corpus-wide grep;
    if it recurs elsewhere it is a form-template defect, not a state's slip.
12. **KS FY2005 — field 9 attributes Cherokee County's LSA designation to "the Bureau of Labor
    Statistics"**; LSA designations are DOL/ETA, as the same document's field 8 says.
13. **KS FY2006-a — Sumner County and Wichita City rates appear in this document's rate table
    but field 9 says they are approved under a different serial (#2060031) on an LSA basis.**
    No groups were emitted for them here. Confirm the cross-reference, or those two areas are
    invisible in FY2006 unless `ks-abawd-response-fy2006` (which does carry them) is joined.
14. **KS FY2008 — field 9 mentions DOL LSA designations generically while no county is named
    as an LSA anywhere.** Treated as boilerplate; no `lsa` group created.
15. **NE FY2006 — the RO transmittal date and the state request date are both 2006-03-02.**
    Possibly genuine, possibly one field copied into the other.
16. **NE FY2000 — form fields 16 and 18 are blank**; `response_date` and
    `date_ro_transmittal_request` were taken from the cover memo's date stamps instead.
17. **KS FY2006-a — field 6 prints `Mountain Plain`** (no final "s").
18. **MS FY2016 — FNS narrates eligibility "from December 2014 through December 2015" but
    approves only 2015-10-01→2015-12-31.** Only the approved period was extracted.

### C. Recurring traps for `2224`

19. **NE serial 970152 spans FY1998–FY2013** — sixteen years, one serial, repeatedly extended
    and modified. Same shape as AR 980013 (FY1999–2008). Reinforces D-04: `(state, FY)` and
    `(state, serial)` are both lossy; only `(serial, coverage-interval, area)` separates the
    actions.
20. **Reservation-inside-county double coverage (NE).** Most of the Omaha and Winnebago
    Reservations lie inside Thurston County, so from FY2008 the county and the reservations
    are both waived and the same residents are covered twice. `possible_double_counting` is
    `false` on those rows because the schema defines it narrowly as duplicate *named units*;
    the overlap is real and is recorded only in notes. 22 rows in this run carry
    `non_standard_geography = true`, all NE reservations.
21. **Cities inside counties (KS).** Wichita in Sedgwick and Hutchinson in Reno recur across
    FY2004–FY2008, sometimes as the waived unit while the parent county is explicitly NOT
    waived (KS FY2006 says BLS data does not support all of Sedgwick). The county-year panel
    cannot represent these without a sub-county layer or an explicit rule.
22. **KS FY2004's "Other Areas" group double-counts Finney County** — listed on its own line
    and again as a component of the "Finney-Kearny LMA" inside the same combined total.
    `possible_double_counting = true`.
23. **Geary County sits in the KS FY2004 "Other Areas" bundle with Finney and Kearny**, which
    are ~200 miles away in the southwest; the set is non-contiguous as drawn (D-11, fourth
    instance). Kept as printed.

### D. Threshold-hugging bundles (extends the KY/GA and SC/AR tables)

Kansas is the densest case in the corpus. Every joint set it filed FY2005–FY2008 lands on
its printed threshold, and the numbers below are computed from the extracted unit rates, not
read off the agents' prose:

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

**Seven exact-threshold sets in four documents from one state**, plus one clearing by a
single tenth. FY2008 is the strongest single observation in the corpus after AR FY2008: only
3 of 27 counties clear 5.6 on their own rates (Leavenworth 5.7, Linn 6.5, Wyandotte 7.8),
four sit exactly at 5.6, and the remaining twenty — down to Clay at 3.7 — are carried by an
aggregate equal to the threshold at the printed precision.

What Kansas adds that AR/GA/KY did not is a **time series of the same construction**: the
state re-drew the bundle every year, against a threshold that moved 7.0 → 6.8 → 6.5 → 6.1 →
5.6 as the national rate fell, and hit the number every time. That is much harder to explain
as coincidence than a single well-fitted bundle, and it is the cleanest available evidence
that the bundle is chosen *given* the threshold rather than the threshold being met by a
pre-existing region. With ND FY2006, GA, KY and AR, the regularity now holds in **six states
across three decades**.

**Caveat.** KS FY2004 cannot be assessed: it prints combined labor-force/unemployed totals
for each of its four regions and **no per-county rates at all**, so the members' individual
standing is unrecoverable (all 22 units are `qualifying_basis = unknown`, D-10). The same
gap hides GA FY2020-b/FY2023 and KY FY2023–25. Any exhibit built on this table must state
that the sample is documents that printed per-unit rates, which is not all of them.

### E. Doc-class failures in this trio (extends D-07)

- **KS FY2011, FY2012, FY2013** — three consecutive years of one-page *state-authored*
  letters to FNS adopting a pre-qualified waiver. No serial, no form fields, no FNS action.
  Criterion coded `null` / `federal_suspension` / `eb_trigger` respectively, tracking each
  letter's wording rather than the mechanism.
- **MS FY2011** — state-authored letter to the SERO Regional Director; coded
  `federal_suspension`, and the letter itself misstates the ARRA window as running through
  September 2011 (canonical: 2010-09-30).
- **MS FY2013** — an Outlook email forwarding a trigger-notice memo, asking FNS to treat it
  as the official request. The memo attachment is not in the PDF, so the eligibility basis
  cannot be verified from this document.

All five are filed as `*-abawd-response-*`. Running total across runs: **ten** documents
whose class the filename gets wrong.

### F. Nonstandard windows and data sources

Only six unit-rows in 304 carry a nonconformance flag, and five of them are one place:
**Nebraska's Santee Sioux Reservation**, FY1998–FY2008. There is no BLS/LAUS series for the
reservation, so every year the state constructs one by applying census population-share
ratios to Knox County's figures — `non_bls_source` in FY1998/1999, `nonstandard_averaging`
in FY2000/2004 (12-month aggregates, and a 36-month window in FY2008 that field 7 expressly
authorises for two-year extensions). FY1998 also carries the trio's only
`soft_criterion_invoked`: a 1996 BIA employment-to-population ratio and "chronically low
employment" language alongside the rate.

This is a different failure mode from AR FY1999-a's projected plant-closing rates. There the
state substituted a forecast for a measurement; here the measurement **does not exist at the
waived geography** and apportionment is the only available construction. Whether the panel
can use rate-based identification on tribal units at all is the open question — and it will
recur in every Tier 2.5/3 state that names reservations (MT, SD, ID, OR, WA, AK, NM, AZ).

The one other flag, MS FY2006's `seasonally_adjusted`, is a false positive worth leaving
visible: the seasonally-adjusted TUR is the statutorily correct measure for the EB-trigger
route, and the agent said so in the note rather than suppressing the flag.

---

## Verification checklist — IN run (2026-08-14)

Per-document facts to check against the source PDFs. Agents transcribe suspect values
faithfully rather than correcting them, so these are the known-suspect cells in the IN slice.

### A. Would change extracted values — check first

1. **IN FY2002 field 9 cites TWO national reference rates in one sentence, and the reading
   flips 11 of 19 groups between `per_unit` and `joint_aggregate`.** Printed: "unemployment
   rates greater than 20 percent above the national average of **4.4** percent for calendar
   years January 2000 through December 2001, **and above 4.8** percent for fiscal year 2000
   through 2001." The second clause does not repeat "20 percent above."
   - 4.4 × 1.2 = 5.28 → all 11 pct20 areas clear individually (min Crawford 5.4) → per_unit.
   - 4.8 × 1.2 = 5.76 → five fail alone (Crawford 5.4, Randolph 5.5, Sullivan 5.6,
     Vermillion 5.6, Michigan City 5.7) → the spec's STRONGEST joint_aggregate signal.
   The agent chose per_unit on grammatical parallelism, no set-level total or bundle name,
   and geographic dispersion, and preserved the alternate reading in every affected group's
   `qualification_level_evidence`. **Highest-priority item in this run.**
2. **IN FY2005 — two approved bundles are arithmetically BELOW the threshold FNS itself
   recomputed.** Sub-Region 1 prints 6.8523% and Sub-Region 6 prints 6.8847% against a
   recomputed 6.9076%, and both are approved. Both round to 6.9% at one decimal, matching the
   printed threshold, but the document states no rounding convention. Confirm the printed
   figures and whether the document anywhere states how it rounds.
3. **IN FY2003-a serial conflict.** Field 1 and the handwritten header stamp read `970088`;
   the page-1 footer reads `DIR:I:\CPB\Waiver\970155-03 Indy ext`. FY2003-b and every other
   IN document FY1999–FY2008 read `970155`. Confirm which is authoritative — this is almost
   certainly an FNS stamping error, but `2224` should not key on serial until ruled. **Note
   `970088` is also the GA FY2007 serial: serials are not globally unique.**
4. **IN FY2000 prints two different rate floors and never reconciles them.** The state's
   letter and Waiver Request form say "at least 6.0%" (3 most recent months, projected 12);
   the MWRO transmittal letter on p.4 says "at least 6.4%".
5. **IN FY2004 — which criterion does a denial carry?** Portage City and Lake County were
   *requested* on an LSA theory (Portage as a listed city, Lake via the multi-state Chicago
   LMA) but *denied* on FNS's own 20%-above-national backstop arithmetic. The agent coded
   `lsa`, matching the request, and flagged `pct20_above_natl` — the dispositive
   calculation — as the reasonable alternative. Needs a rule; it changes the criterion mix on
   every denied row corpus-wide.
6. **IN FY2004 misspells Noble as "Nobel" in FNS's own recalculation table (p.7)** while the
   state's field-8 listing spells it correctly, twice. The agent used "Noble" for BOTH `name`
   and `orig_text`. This departs from the usual "orig_text is verbatim" convention because
   the document prints both spellings — confirm which instance `orig_text` should hold.
7. **IN FY2000 date error, acknowledged by FNS on the form.** Field 17 states the state's
   request letter dated "February 18, 1999" was "clearly intended to read February 18, 2000."
   The agent used 2000-02-18 per FNS's own reconciliation.
8. **IN FY2003-b field 8 is garbled**: "...20 percent above the national average for 24
   during either the Federal Fiscal years 2001 and 2002" — missing "months", and "during
   either" does not parse. Treated as the standard 24-consecutive-month test per field 7.
9. **IN FY2003-b field 18's label is backwards**: printed as "Date of regional office
   transmittal of RESPONSE to NATIONAL OFFICE" (2003-06-30), which cannot be a response
   transmittal since field 16 (national office action) is blank. Mapped to
   `date_ro_transmittal_request` as the best fit.
10. **IN FY2008 — Region 12's printed total (5.6) cannot be reproduced from member rates**
    (unweighted mean ≈ 6.1, a ~0.5 pt gap). Same for FY2007's Sub-region 12 (printed 5.9,
    unweighted mean ≈ 6.45). No labor-force counts are printed in either document, so the
    weighting is unverifiable. Confirm the printed totals are transcribed correctly, since
    both land exactly on their thresholds.

### B. Internal counts and labels that do not reconcile

11. **IN FY2002 field 9 says "the following 8 counties and 3 cities"** for the LSA approval,
    but the table lists 5 LSA counties + 3 LSA cities = 8 areas total, not 8 counties.
12. **IN FY2004 field 9 says FNS approves "the 30 counties contained in the 7 sub-areas"**,
    but the sub-area tables sum to 28 (5+3+3+5+3+5+4). The 30 appears to conflate the 28 with
    Vermillion and White, approved the same day under the same rule but in no sub-area.
13. **IN FY2007 cover memo says "20 additional counties"**; field 8's list, the "24 of those
    counties... were additions" passage, and the table tally (24 new + 26 old = 50) all say
    **24**.
14. **IN FY2007 field 9 says "the 26 counties and one city previously approved"**; the cover
    memo and field 8 both say **three cities** (Elkhart, New Albany, South Bend).
15. **IN FY2003-b cover letter says "9 additional counties and 7 additional cites"** [sic].
    The count reconciles only if the denied Lake County is included among the 9.
16. **Region 5's table header omits the "Sub-region of" prefix in BOTH FY2007 and FY2008**
    while its own total row reads "Total for Sub-region." Recurring across years, so a
    form-preparation habit rather than a one-off typo. FY2008 has the same issue on Regions
    6 and 7.
17. **Form numbering skips 18 → 20 (no field 19) on IN FY2003-a and FY2005**, so
    `date_ro_transmittal_request` is null on both. Recurring form artifact.
18. **IN FY2003-a typist code implies the memo was typed 2003-04-08**, ~2.5 weeks *after*
    field 18's transmittal date of 2003-03-21. `response_date` left null rather than pick.
19. **IN FY2001 handwritten signature date reads ~"2-2-01"**, preceding the covering letter's
    typed 2001-02-05.
20. **IN FY2011 email chain is chronologically impossible as printed**: the forward is
    stamped 2010-04-16 8:53 AM, the original message it forwards is stamped the same date at
    9:27 AM.
21. **IN FY2008 field 8 reads "requesting to to extend"** [sic].

### C. Transcription / OCR calls made against the geography reference

22. **IN FY2002 prints "Green" twice** (field 8 prose and field 9 table) for **Greene**
    County. One-character repair; `orig_text` preserves "Green".
23. **IN FY2002's text layer renders "Perrv" where the page image shows "Perry."** The PDF is
    *not* a scan — its text layer is simply corrupt. Argues for image-reading even
    text-bearing documents.
24. **IN FY2007 prints "Dekalb"/"Dearbon" in narrative roll-calls** but "DeKalb County"/
    "Dearborn County" in its tables. The reference settled an *intra-document* inconsistency;
    table spellings used.
25. **IN FY2008 "Lagrange" → `name: "LaGrange"`**, `orig_text` verbatim "Lagrange County".
26. **Marion is the CITY (Grant County), not Marion County (Indianapolis)**, in FY2002,
    FY2003-a and FY2006. Flagged in each group's evidence field. Same shape as the GA Macon
    county-vs-city trap.

### D. Recurring traps for `2224` specific to IN

27. **Container/contained inversion.** Lake County is DENIED in FY2003-b and FY2004 while
    East Chicago, Gary and Hammond — all inside Lake — are approved in those same documents,
    and East Chicago/Gary hold approvals continuously from FY1999. A county-year panel that
    propagates a county's disposition to its cities will get Indiana wrong. This is D-14's
    mirror image and it recurs.
28. **Serial 970155 spans FY1999–FY2008** (ten documents, repeatedly modified and extended),
    with FY2003-a possibly mis-stamped 970088. Same shape as AR 980013 and NE 970152 —
    reinforces D-04.
29. **FY2021 is two documents, one coverage sequence, different serials.** FY2021-a (serial
    2210002) approves 5 months statewide; FY2021-b (no serial printed at all) extends the
    same coverage to 12 months on the same trigger notice. FY cannot separate them; serial
    cannot join them.
30. **`unknown` `qualifying_basis` arrives by two different routes** (31 rows total). FY2004
    prints counts but no per-county rates — the combined rates re-derive exactly (7/7) but the
    load-bearing member is unidentifiable. FY2007/FY2008 print rates but no counts — the
    weighting is unrecoverable outright. Preserve both, do not impute; the routes mean
    different things.
31. **Additions vanish at group level.** IN FY2008 folds its three modification counties
    (Huntington, Lagrange, Floyd) into the existing Region 3 and Region 12 aggregate tables
    with no "newly added" group. D-12's defect with the opposite sign.

### E. What this run adds to existing decisions

- **D-12** gains three IN drop instances (FY1999 Terre Haute/Vigo, Fayette, Sullivan;
  FY2001 Vermillion "no longer meets the criteria"; FY2003-b Gary as case (c)) **and a third
  shape**: FY2002's Randolph is neither dropped nor denied but *re-qualified under a different
  rule* (LSA → 20%) in the same document, leaving no trace. FY2006 then restores Vermillion,
  Fayette and Sullivan, so drops are not exits — which is exactly why they need rows.
- **D-07** gains IN FY2013, a letter referencing an unattached FNS memo naming **46 states**
  at once (third state, after IA and SC), and reproduces the vocabulary split *within one
  state*: FY2012 "on the trigger list" → `eb_trigger`, FY2013 "qualify for suspending" →
  `null`.
- **D-10** gains the FY2007/FY2008 variant above — `unknown` because the aggregation method
  is unrecoverable, not because nothing was printed.
- **D-14** gains its mirror image (item 27).
- **D-11** is not exercised: IN's joint bundles are Workforce Investment Planning Regions,
  which are contiguous economic regions by construction.
- **D-06** gains a fourth instance by a new route: IN FY2011 emits a group with **zero
  units** — not an unenumerated *denial* (DE FY2026, WI FY2009, SC FY2004-c) but an
  unenumerated *request*.

---

## Agent judgment calls and deviations — IN run (2026-08-14)

Every place the spec did not determine the answer and an agent therefore chose, plus
protocol deviations. Nothing here needs a ruling on its own, but a call that recurs is how a
D-nn entry gets born.

### A. Calls that change row counts

1. **Dropped areas → no group** (FY1999 ×3 areas, FY2001 Vermillion, FY2003-b Gary). All
   three agents read the spec's case (c) and recorded the drop in `request_level.notes`.
   ≈5 areas produce no row in this state. Straight D-12.
2. **FY2011 emitted 1 group with ZERO geographic units**, the agent declining to invent a
   statewide Indiana unit because LSA is inherently a per-unit DOL designation and the
   document never claims whole-state LSA status. **FY2013's agent, on a comparable
   state-request document, emitted a statewide Indiana unit instead.** Same document class,
   incompatible unit handling, both defensible — new D-nn candidate.
3. **FY2008's three modification counties folded into existing aggregate groups**, no
   separate "newly added" group, because the document itself folds them into the Region 3 and
   Region 12 tables.
4. **FY2007's regional bundles kept whole** rather than split into previously-approved vs
   newly-added members, per the "scope of a joint set" rule — the document evaluates each as
   one reconstituted set with one combined rate.
5. **FY2005's Terre Haute and Vermillion kept as two per_unit groups**, not one, on the
   memo's explicit per-area language ("each have unemployment rates 20 percent above");
   adjacent table cells treated as a layout artifact. Same call for FY2004's Vermillion and
   White, each of which has its own standalone calculation table.

### B. Calls that change a coded value

6. **FY2002's two-national-rate ambiguity → per_unit** (item A1 above). 11 groups.
7. **FY2004's denials coded `lsa` (as requested) rather than `pct20_above_natl` (as
   decided)** (item A5 above).
8. **Region 7 coded `joint_aggregate` in BOTH FY2007 and FY2008 despite every member clearing
   the threshold alone** — a named set with a printed combined total is a STRONG signal under
   the tie-break hierarchy, and its sibling regions share identical construction. **Two
   independent blinded agents converged on the same reading**, which is evidence the
   hierarchy is written clearly enough to be applied consistently.
9. **FY2005's Benton/Warren denied group coded `joint_aggregate` rather than `unknown`**,
   because the document frames the denial in terms of the original joint Sub-Region 4.
10. **FY2003-a's pct20 trio (Crawford, Randolph, Vermillion) coded
    `qualification_level = unknown`** — no per-county rates, no combined rate, no set label,
    so no evidence tier resolves it. Kept as ONE group because splitting would assert a
    per_unit determination the document does not support. Model D-10 refusal.
11. **`national_unemployment_rate_cited.value` left null in FY2007 and FY2008** because only
    the inflated threshold is printed and back-solving (5.9/1.2, 5.6/1.2) would invent a
    value. Two agents, same refusal, independently.
12. **`soft_criterion_invoked = false` throughout** — FY2000 and FY2003-a both reasoned that
    the statutory "insufficient number of jobs" recital in fields 6–10 is boilerplate citation
    of the legal standard, not an independent soft-criterion rationale. Consistent with, and
    relevant to, **D-13**.
13. **FY2013 refused to infer a criterion at all** (`null`), the letter never stating which
    rule made Indiana one of the 46 states, and explicitly declined `federal_suspension`
    despite suspension-flavoured vocabulary because FFY2013 falls outside both statutory
    windows. The v1_5 waiver-period anchoring catching a false positive.
14. **FY2005 recorded a two-label case via `criterion_other_explanation`** for units marked
    "(LSA)" inside 20%-rule sub-region tables, following `2220b`'s two-label instruction over
    the schema description's note that the field is normally used only when
    `criterion_code = other`. **The two-label tie-break has no dedicated field — worth
    resolving in `2220c`.**

### C. Calls on dates

15. **Stamp handling is inconsistent across agents.** FY2000's agent promoted a "MAR 2 8
    2000" filing stamp into `response_date` (flagging it as a stamp); FY2001's agent refused
    an equivalent "APR-2 2001" stamp and used field 19's typed date instead; FY1999's agent
    refused a "MAR 0 8 1999" stamp and left `response_date` null; FY2003-a's agent left it
    null on account of the typist-code conflict. Four documents, three treatments. Small
    D-nn candidate.
16. **Derived FFY bounds.** FY2012 converted "FFY 2012" to 2011-10-01/2012-09-30 and FY2013
    converted "the time period allowable" to 2012-10-01/2013-09-30, both from the standard
    federal fiscal year rather than printed dates.
17. **FY1999 left `waiver_effective_date` null though arithmetically inferable** (~1999-04-01
    from "one year" + a 2000-03-31 expiry), reading "never invent values" as controlling over
    date arithmetic. FY2002 and FY2003-a made the same call for the same reason.
18. **FY2003-b derived the unemployment window as 2000-10 → 2002-09** from "Federal Fiscal
    Years 2001 and 2002" — a fixed convention, not an invented figure — and flagged the
    inference per group.
19. **FY2021-a preserved a conditional expiry.** The printed date 2021-02-28 went in the date
    field; the "or until the date at which new waiver standards become effective, whichever
    occurs earlier" clause was kept in `waiver_duration_text` rather than dropped.

### D. Conventions that drifted between agents

20. **`orig_text` granularity.** FY1999/FY2000/FY2001 stored the bare printed name
    ("Orange") because the type word appeared only in a shared prefix ("the counties of
    Orange, Randolph, and Vermillion"); FY2005 stored the fuller "LaPorte County" form from
    the breakdown tables in preference to the bare form used in the final approval table.
    Both defensible, opposite choices.
21. **`fns_region` normalisation.** FY2006 stored "Midwest Region", FY2013 stored "Midwest
    Regional Office" verbatim, FY2021-b left it null rather than infer the region from the
    area code of a phone number (a good refusal). Unnormalised — a `2224` cleaning task.

### E. Protocol deviations

22. **Batch asymmetry, mine not the agents'.** The 16 agents ran in two batches of 8. The
    second batch's prompts carried a generic DOC-CLASS WARNING (the `*-abawd-response-*`
    filename convention is unreliable; code `document_type`/`group_action` from what the
    document actually is) that the first batch did not receive. It names no document and
    gives no answer, and it was added because three of the second batch are 1-page files
    where the distinction is decisive — but FY2011/2012/2013's clean doc-class calls were
    made with a hint the FY1999–2005 agents lacked. **Recommend making it standard prompt
    language for all future runs.**
23. **FY2011's agent did not read the rules KB**, judging `2220b`'s restatement of the LSA
    definition and ARRA window sufficient. Within the allowed source list, not beyond it.
24. **FY2004's agent read `0_lit/00_abawd_rules/002_rules_machine.yaml`** to confirm the
    `pct20_above_natl` and `lsa` effective windows cover FY2004. Permitted source; no anomaly
    found.
25. **FY2008's agent attempted `pdfplumber`/`PyPDF2`** (not installed in the `snap` env) and
    fell back to the Read tool. Tooling note, not an extraction deviation.

### F. Where the agents were right to refuse

26. Back-solving the national rate from a printed threshold (FY2007, FY2008).
27. Inferring a criterion for a blanket-qualification letter that names no rule (FY2013).
28. Inferring `fns_region` from a phone area code (FY2021-b).
29. Picking between two printed rate floors (FY2000) or two national reference rates
    (FY2002); both preserved with the alternative recorded.
30. Silently correcting the FY2005 sub-region totals that sit just below the recomputed
    threshold — the tension was recorded instead.

**Blinding.** All 16 returned compliance lines and **zero agents disclosed listing anything
under `1022_extractions/`**, down from one in KS/NE/MS, six in SC/AR and roughly a dozen in
KY/GA. The forbidding language stayed in the write step where the SC/AR writeup recommended
putting it.

---

## Verification checklist — MO run (2026-08-15)

Per-document facts to check against the source PDFs. Agents transcribe suspect values
faithfully rather than correcting them, so these are the known-suspect cells in the MO slice.

### A. Would change extracted values — check first

1. **MO FY2004 prints a national average that is inconsistent with the threshold it then
   applies, and 56 unit-rows ride on the resolution.** The letter states the criterion is
   "20 percent above the national average" AND that "the national average unemployment rate
   was 6.3" — which implies a 7.56 cutoff. But every approved sub-area total clusters at or
   just above **6.3**, and the closing paragraph restates the operative cutoff as "at least
   6.3." The agent treated 6.3 as the applied threshold (the only reading consistent with what
   was actually approved) and recorded the tension in `request_level.notes` and every group's
   evidence field. If 6.3 is instead the *pre-inflation* national rate, five of the eight
   sub-areas fail and the FY2004 exhibit changes shape. **Highest-priority item in this run.**
2. **MO FY2002 — field 8's narrative and field 9's disposition table disagree on a county
   name, and the two candidates have opposite dispositions.** The field-8 list prints
   "Caldwell" in the slot where the field-9 approval table prints "Crawford" (with a rate).
   Caldwell is separately and consistently identified — in the cover memo and in field 9's
   denial paragraph — as one of the counties added later and denied. The agent treated field 9
   as authoritative (Crawford approved, Caldwell denied), which also avoids a double-count.
   Reads as a drafting error in the original letter, not a scan artifact. Confirm.
3. **MO FY2002 cover memo says the state's original criteria were "10 percent above the
   national average"** — almost certainly a typo for 20, given the rest of the document's
   consistent 20%-rule arithmetic. Transcribed as printed.
4. **MO FY2003 — Dallas County is in the approval table but not in the request narrative.**
   Field 8 / the cover letter describe 29 areas ("28 counties and one city"), never naming
   Dallas; the field-9 approval table lists 30 rows including Dallas (LSA = Yes, 6.7%). The
   agent coded Dallas approved on the table. Confirm the table row exists and is Dallas.
5. **MO FY2003 prints three conflicting data windows for the same rates.** Cover letter: 24
   months "ending 2001-12-31." Field 9 narrative: "ending 2000-12-31." The rate table's own
   column header: "(01/2000–12/2002)" — a **36-month** span despite being labelled 24-month
   everywhere else. The agent used the table header (it is attached to the printed rates) and
   flagged the conflict. Same shape as the 36-month window already flagged in an earlier run.
6. **MO FY2008 — the Lower Southeast sub-region's printed total (7.9) exceeds every member's
   own rate (max 7.4).** Arithmetically impossible for any weighting of those four counties.
   Transcribed verbatim as a source anomaly; confirm the printed figure.
7. **MO FY2004 — Madison County's printed unemployment count (98,111) against a labor force
   of 112,694** implies an 87% unemployment rate in the Lower East Central-Cape table. Almost
   certainly a source-table error; left as printed.
8. **MO FY2011 — the letter's own text and its attached DOL trigger notice disagree on the
   state's TUR.** The cover letter says the 3-month TUR "was: (1) **6.5** percent and (2) 138
   percent of the … second year"; the attached Trigger Notice table prints Missouri's 3-month
   S.A. TUR as **9.4** with "Percent of Prior Year" = 138 (matching the second figure exactly).
   The agent used 9.4 and preserved both. The 6.5 looks like the generic statutory threshold
   re-used one paragraph later by mistake.
9. **MO FY2013 prints "88 percent"** where the statutory second prong is 110 percent of the
   prior year's corresponding 3-month average. Plausibly a scanned "110"; transcribed as
   printed rather than corrected.
10. **MO FY2001-b — field 18's date precedes the events it should follow.** RO transmittal of
    the *response* is dated 2001-05-15, before both the national office action (2001-06-05) and
    the RO's transmittal of the *request* (2001-05-29). Also, field 2 reads "Initial" although
    the document is described throughout as an amendment to a waiver approved 2001-02-08.
11. **MO FY2001-b — Shelby County's rate is exactly 4.9%, i.e. AT the threshold**, while the
    narrative says eight counties "resulted in rates **higher than** 4.9 percent." Kept as
    approved / `own_rate` (the operative standard is "at least 20 percent above"), tension
    flagged. Reynolds County in the same document uses a **different 24-month window**
    (Apr 1999–Mar 2001) because it failed the standard window (4.8 vs 4.9) — confirm that
    second window is printed as such.
12. **MO FY2007-b — `response_date` (2006-11-02) was taken from the memo's preparer footer**
    (`...CPerkins:mcl:11/02/06`) because the top-of-page date stamp is OCR-illegible. Confirm
    against the page image.
13. **MO FY2003 — a partially legible page-1 stamp reading roughly "MAY 21 20_3"** was NOT used
    for `response_date` (its function was unclear and fields 16/18 are blank). Confirm what it
    is; if it is the national-office action date, that field is currently null.
14. **MO FY1998-a — the memo prints the routing waiver once as "Waiver #270129"** where the
    subject line and opening paragraph both say #970129. Recorded as a typo; `970129` used.

### B. Internal counts and labels that do not reconcile

15. **MO FY2008**: field 8 says "**38 contiguous counties**," field 9 says "**36 counties and
    two cities**" (38 areas), and the printed tables enumerate **36 areas** (34 counties +
    2 cities). The agent followed the tables.
16. **MO FY2001-a**: field 8 says the request rests on "the designation of the **26 counties**
    and the City of St. Louis," but only **20 counties + 1 city** are named and approved.
17. **MO FY1998-b**: field 8 says "**28 counties and 1 city**"; field 9's LSA sentence names 27
    counties + St. Louis city, plus Buchanan described separately. Reconciled as 27 + Buchanan
    = 28 counties, + 1 city = 29 groups.
18. **MO FY2006**: the state's request cites LSA designation for "two consecutive fiscal years
    **2003–2004**," while FNS's approval says it reviewed the ETA LSA notice for **FY2005–2006**.
    Both preserved; neither resolved.
19. **MO FY2007-a / FY2007-b**: two counties (Madison, Ripley) and one city are printed in the
    tables **without the trailing "County"** word. Kept verbatim in `orig_text`, `area_type`
    inferred from context. Same in FY2004 for Shelby.
20. **MO FY2007-a / FY2007-b / FY2008 — no raw national rate is ever printed**, only the
    already-inflated threshold ("national average plus 20 percent was 6.0"). All three agents
    correctly left `national_unemployment_rate_cited.value` null rather than storing the
    threshold there. Confirm this is the convention `2224` expects.

### C. Transcription / OCR calls made against the geography reference

21. **MO FY2008: "Dunkin" → Dunklin** and **"Laciede" → Laclede** — two one-character repairs,
    `orig_text` kept verbatim. The only name corrections the reference produced in the whole MO
    slice; every other document's names matched exactly. Confirm both against the page images.
22. **MO FY2008: Ste. Genevieve City** is flagged `non_standard_geography = true` (a sub-25,000
    place, absent from the state's LAUS 25k+ city list) and reasoned through its parent county
    for contiguity. The single `non_standard_geography` row in the state.
23. **St. Louis city vs St. Louis County** was handled consistently across all 10 independent-
    city rows (`name = "St. Louis"`, `area_type = "independent city"`, `orig_text` verbatim).
    St. Louis County appears nowhere in the MO corpus — worth confirming that is really true
    rather than an artifact of every agent mapping the string the same way.

### D. Recurring traps for `2224` specific to MO

24. **`possible_double_counting` is document-scoped by design, and the flat file broadcasts it
    to every row.** The field lives under `request_level` in `2220c` ("true if a single
    geographic unit appears in MORE THAN ONE group in this request"), so `2223` replicates it
    across all rows of the document, exactly as it does every other request-level column. In MO
    that means all **37** FY2005 rows read `true` because Kansas City alone appears in two
    groups — a row-level read overstates the affected units by ~18×. Not an agent error and not
    new to MO (the same broadcast produced "67 rows" in SC/AR), but MO is the sharpest ratio so
    far. `2224` should either use `double_counting_note` (which names the units and groups) or
    re-derive the flag at unit level from the emitted groups; a `GROUP BY
    possible_double_counting` over the flat file is meaningless as it stands.
25. **Three FY2007 documents, one serial, three distinct actions** (see the protocol writeup,
    item 4). `(state, FY)` and `(state, serial)` are both lossy. D-04 material.
26. **Serial 970129 carries FY1998–FY2006 (296 unit-rows) and 2070002 carries FY2007–FY2013.**
    Two long-lived serials cover the entire state; a serial-keyed join collapses a decade.
27. **~18 dropped areas produce no row** (FY1999 six, FY2000 five, FY2001-a seven) while 7
    dropped areas DO get rows as `withdrawn_by_state` (FY2005, FY2006). Same event class, two
    encodings, one state. D-12.
28. **The four late statewide documents (FY2011, FY2012, FY2013, FY2016)** are MO's only
    statewide rows and only `EUB` rows, and two of them carry `group_action = null` because
    they are state requests with no FNS decision. Any "did MO apply / was MO covered" measure
    must not read those nulls as non-application.

### E. What this run adds to existing decisions

- **D-14 (qualification by containment)** gains a third direction: Buchanan County (MO) is
  approved because St. Joseph city inside it is the LSA. With NE (contained qualifies via
  container) and IN (contained approved, container denied), the gap is in the *relation*, not
  in one direction of it. Two MO agents independently used `own_designation` as the least-bad
  enum value and both said so explicitly.
- **D-12 (dropped areas)** — see item 27; MO is the strongest single-state case yet.
- **D-04 (serial / coverage-interval key)** — see items 25–26.
- **D-07 (blanket national action)** — MO FY2011/FY2012 are state-authored EB-trigger adoptions
  under `-response-` filenames, the same class as KS FY2011–13 and IN FY2011–13.
- **D-11 (contiguity)** — no new instances. Every MO joint bundle checked contiguous against
  the adjacency lists, including the two "Greater St. Louis Region" sets whose members
  (Crawford, Gasconade, Montgomery) sit well southwest of St. Louis — a MERIC planning-region
  label, not a proximity claim, and mutually adjacent regardless.

**Blinding.** All 19 returned compliance lines. One agent (FY2006) disclosed running `ls -la`
on its output directory and seeing two sibling *filenames* from a different state, after its
judgment was formed and without opening either. The forbidding language was in the write step;
the residual is agents checking the directory exists before writing, so the next prompt
revision should state that the directory is guaranteed present and needs no check.

---

## Agent judgment calls and deviations — MO run (2026-08-15)

Every place the spec did not determine the answer and a blinded agent therefore chose. Nothing
here needs a ruling on its own; a call that recurs across runs is how a D-nn entry gets born.
Read this before trusting the run's counts.

### A. Calls that change row counts

1. **FY2007 (unsuffixed) — a prior-approval recital was NOT re-emitted as groups.** Field 8
   recites that a 2007-01-30 action on the same serial had already approved Dent and Wright
   plus six sub-regions covering 18 counties, and that their data "remains unchanged." Field 9
   decides only the increment (Clinton into the KC sub-region, Montgomery into Greater St.
   Louis, Schuyler alone). The agent emitted **3 groups / 11 units**, not ~26, extending the
   v1_5 "recited statutes get no group" rule by analogy to a recited prior *action*. This is
   the single largest row-count call in the run and it is the right one — but note the rule as
   written in `2220b` is about statutes, not prior dispositions, so the extension was the
   agent's inference.
2. **~18 dropped areas produce no rows** — FY1999 (6 counties that lost LSA status), FY2000
   (Camden, Carter, Laclede, Ripley, plus Buchanan-via-St.-Joseph), FY2001-a (7 removed from
   the prior waiver). All recorded in `request_level.notes` under case (c). Straight D-12.
3. **7 dropped areas DO produce rows** — FY2005 (Kansas City as an individual LSA candidate;
   Clay/Cass/Jackson/Platte/Kansas City as a withdrawn `joint_aggregate` "cluster") and FY2006
   (Henry County). Same event class as item 2, opposite encoding, same state. Also D-12.
4. **FY2003 — Dallas County was emitted on the strength of the approval table alone.** It
   appears in field 9's 30-row table (LSA = Yes, 6.7%) and nowhere in the field-8 / cover-letter
   narrative, which counts 29 areas. The agent treated the disposition table as authoritative.
   +1 row; reversible if the table row is a transcription artifact (checklist item 4).
5. **FY1998-a — Wright County was emitted as a fourth group under a second serial.** The memo
   moves Wright out of #970117's approval list into #970129 on LSA grounds. The agent read the
   memo's own "we placed the request … based on the county's designation as an LSA" as an FNS
   action statement rather than an aside, and emitted it. +1 row, and it is why that document
   is the run's only one carrying two serials (`970117; 970129`).
6. **FY1998-b and FY1999 — St. Joseph city was NOT emitted as its own unit** although it is
   the LSA that carries Buchanan County. Both agents treated it as the basis, not a requested
   area (case (c)). Consistent across the two documents; see D-14 for why the relation itself
   has no representation.
7. **FY2005 — Kansas City occupies two rows** because it was withdrawn in two originally
   distinct roles (individual LSA candidate; member of the pct20 cluster). Deliberate, flagged,
   and the sole cause of the document's `possible_double_counting = true`.
8. **FY2004 and FY2003 — unnamed 15%-exemption areas produce no groups.** Both letters note
   that some counties will instead be covered under 273.24(g) but name none, so no group could
   be built. Distinct from ND FY2003, where the areas *were* named and
   `state_alternative_coverage` therefore had somewhere to land.

### B. Calls that change a coded value

9. **FY2004 — the operative threshold was read as 6.3, not 7.56.** See checklist item 1; this
   governs 56 unit-rows and the run's headline threshold-hugging exhibit.
10. **FY2002 — field 9's table beat field 8's narrative on a name conflict**, making Crawford
    approved and Caldwell denied rather than the reverse.
11. **FY2011 — the attached DOL trigger notice (9.4) beat the letter's own prose (6.5)** for
    `unemployment_rate`, with both preserved in text.
12. **FY2008 — two OCR repairs applied**: `Dunkin` → Dunklin, `Laciede` → Laclede, `orig_text`
    verbatim in both. The only name corrections in the state.
13. **Buchanan County's `qualifying_basis` was set to `own_designation`** in FY1998-b and
    FY1999 as the least-bad enum value, with the containment logic pushed into
    `qualification_level_evidence`. Both agents said explicitly that no value fits. **This is
    the MO half of D-14** and the two agents agreed with each other while disagreeing with the
    NE FY2013-a agent's `carried_by_group` on the same relation.
14. **FY2005 — the withdrawn "cluster" was coded `joint_aggregate` with no recoverable
    arithmetic**, purely on the named-set signal ("cluster", "for consideration as one unit").
    The state never supplied supporting data, which is why the request collapsed — so the
    strongest evidence tier available was the label.
15. **FY2008 — two sub-regions were coded `joint_aggregate` although every member clears the
    threshold alone** (Lower Southeast, Springfield), on the "state constructed and named the
    set" tier rather than on arithmetic. Defensible under the spec's evidence ladder, but it
    means `joint_aggregate` in MO mixes load-bearing and non-load-bearing bundles — relevant
    to any D-10-style margin computed off `qualification_level`.
16. **FY2007-a and FY2007-b — Dent and Wright were split into two `per_unit` groups** rather
    than one bundle, on the absence of a combined total row, while the six named sub-regions in
    the same tables got `joint_aggregate`. The two agents made the identical call independently,
    which is a good sign for the splitting rule's determinacy on this shape.
17. **FY2002 — three `rejected` rows carry `soft_criterion_invoked = true`**, the corpus's
    first instance of that flag on a denial. See the D-16 addendum.

### C. Calls on dates

18. **`waiver_effective_date` was left null on 153 of 392 rows** rather than back-inferred from
    a stated duration plus an expiry. Five agents (FY1998-a, FY1998-b, FY1999, FY2000, FY2001-a)
    each said so explicitly, in one case declining to infer 2000-03-01 from the prior waiver's
    2000-02-29 expiry. Consistent and conservative; confirm `2224` wants nulls rather than
    derived starts.
19. **`response_date` was recovered from non-obvious page furniture in four documents** —
    FY1998-a from a typist/routing code line, FY1999 from the FEB 10 1999 stamp (in preference
    to a `final:2/9/99` routing note), FY2000 from the FEB 16 2000 stamp with field 16 blank,
    FY2007-b from the preparer footer `...CPerkins:mcl:11/02/06` because the page stamp is
    OCR-illegible. Each agent named its source in `notes`.
20. **FY2003 — a partly legible "MAY 21 20_3" stamp was deliberately NOT used** for any date
    field because its function was unclear and fields 16/18 are blank. `date_national_office_
    action` is null on 270 of 392 rows overall, so this is the common case, not the exception.
21. **FY2013 — `date_state_request` came from the state's cover letter (2012-04-11)** because
    the Waiver Request form's own field 15 is blank on the scan.

### D. Conventions that drifted between agents

22. **`data_nonconformance` on the four late EB-trigger documents is coded four different
    ways** for what is essentially one methodology (DOL 3-month seasonally-adjusted TUR):

    | doc | non_bls_source | seasonally_adjusted | nonstandard_averaging |
    |---|---|---|---|
    | FY2011 | true | true | true |
    | FY2012 | null | null | null |
    | FY2013 | true | true | null |
    | FY2016 | null | null | null |

    The FY2011 and FY2013 agents both added notes clarifying that DOL-SA data is the *prescribed*
    basis for the EB route rather than a defect — i.e. they used the nonconformance block to
    describe the method, while the FY2012 and FY2016 agents left it empty on the view that
    nothing is nonconforming. Both readings are reasonable and the field cannot support both.
    Corpus-wide the flags are sparse (`non_bls_source` true on 6 rows, `seasonally_adjusted` on
    2), so this is small but it is exactly the kind of drift that makes a flag uncountable.
    **Candidate for a one-line rule in `2220b`: the nonconformance block records departures
    from the criterion's own prescribed method, not from BLS/LAUS in the abstract.**
23. **`data_nonconformance` sub-fields are set to `null` by some agents and `false` by others**
    when the document is simply silent (FY2007-a chose null explicitly, "the memo only says
    'U.S. Department of Labor data'"; most others chose false). 355 nulls vs 31 falses on
    `non_bls_source`. Same distinction-without-a-rule as above.
24. **`national_unemployment_rate_cited.value` was left null wherever only the inflated
    threshold is printed** (FY2007-a, FY2007-b, FY2008 — three agents, same reasoning,
    independently). This is the right call and it is now consistent enough to be worth writing
    into `2220b` before an agent stores a threshold there.
25. **Officials named on the form vs named in the letter.** FY2001-a declined to put an FNS
    regional-office addressee in `state_official_name`; FY2016 put the letter's addressee and
    signer in the state/FNS fields and pushed the form's two contact-field names into
    `request_level.notes`. No rule exists for which of up to four named people belongs in which
    of two fields.

### E. Protocol deviations

26. **One blinding disclosure.** The FY2006 agent ran `ls -la` on its output directory before
    writing and saw two sibling filenames from another state
    (`ar-abawd-response-fy2005.json`, `ar-abawd-response-fy2006.json`), after its judgment was
    formed and without opening either. Up from zero in the IN run. The forbidding language was
    in the write step as recommended; the residual behaviour is *checking the directory exists*,
    so the next prompt revision should state that it is guaranteed present.
27. **No batch asymmetry.** The DOC-CLASS WARNING recommended at the end of the IN writeup was
    carried by all 19 prompts, both batches. The FY2007 trio also received an explicit note that
    three files share the FY and that only the assigned one may be read — a targeted addition,
    naming no content, made because same-FY siblings are the one case where an agent might
    reasonably go looking. Recommend keeping both as standard language.

### F. Where the agents were right to refuse

28. **FY2012 — refused to invent an FNS decision.** A Waiver Request form with no action field,
    no national-office date and no FNS signature was coded `state_request_only` /
    `group_action = null`, exactly as the DOC-CLASS WARNING asks.
29. **FY2008 — refused to correct an impossible total** (Lower Southeast prints 7.9 against a
    member maximum of 7.4).
30. **FY2004 — refused to correct Madison County's implausible unemployment count** (98,111
    against a labor force of 112,694).
31. **FY2013 — refused to "fix" a printed "88 percent"** to the statutory 110.
32. **FY2003 — refused to reconcile three conflicting data windows**, using the one attached to
    the printed rates and recording the other two.
33. **FY2001-b — refused to normalise an impossible date sequence** (response transmitted
    2001-05-15, before the 2001-06-05 action it transmits).
34. **FY2002 — refused to silently adopt a "10 percent above the national average" phrase** that
    the rest of the document contradicts, flagging it as a probable typo instead.

---

## Verification checklist — AL run (2026-08-15)

Per-document items to check against the source PDFs. These are values an agent transcribed
faithfully that look wrong, plus internal inconsistencies the document never resolves. They
are **not** decisions; they exist because agents record what the page says rather than
correcting it, so a suspect cell is otherwise findable only by re-reading free text.

### A. Would change an extracted value

1. **FY2006 — a bundle approved below its own printed threshold.** The "Sub-region of
   Region 4" prints an aggregate of **6.9 percent**, but its own printed totals
   (156,822 unemployed / 2,284,825 labor force) compute to **≈6.86%** — below the document's
   stated 6.9% threshold, and further below the correctly-derived 20%-above-national figure
   of **6.96%** (5.8 × 1.2). **4 of its 6 member counties** are below threshold on their own
   derived rates. FNS approved it. Confirm the printed totals and the aggregate; this is the
   AL analogue of the IN FY2005 below-threshold approvals and is potentially a paper exhibit,
   so the numbers need to be right.
2. **FY2006 — a mis-rounded threshold applied to four groups.** The document derives its
   threshold as 5.8 × 1.2 and prints **6.9**; the product is **6.96**, which rounds to 7.0.
   The error recurs across all four CY2003–2004 groups. It flips no other group's outcome, but
   it is the difference between item 1 being a near-miss and a clear failure. Check whether
   6.9 is printed or was derived by the agent.
3. **FY2000-a — Dallas County at 9.95% approved on a substituted data window.** FNS rejected
   the state's round-up of 9.95 to "10 percent," then recomputed on **Nov 1998–Oct 1999**
   (the other seven counties use Dec 1998–Nov 1999) because current BLS data was unavailable,
   and approved. The recomputed rate is **not printed**. Confirm the 9.95, the two different
   windows, and that no replacement figure appears. See D-16.
4. **FY2008 — an aggregate rate cited that matches no bundle in the document.** Field 8's
   opening sentence cites "aggregate average unemployment rates of 5.6 percent" as the
   qualifying figure, but the three named bundles print 5.8, 5.7 and 6.0. The only 5.6 in the
   document is Prichard City's own individual rate. Determine whether 5.6 is a drafting
   artifact or a fourth figure the extraction missed.
5. **FY2003-a — a state-request date that postdates the response.** Field 17 prints
   **December 3, 2003** for the state agency's request, against a response letter dated
   2003-01-13 and a field-18 transmittal of 2002-12-11. Almost certainly a typo for 2002;
   transcribed literally. Confirm and record the intended year.
6. **FY2003-a — four counties decided but never requested.** Field 8's account of the request
   never mentions Clarke, Pickens, Sumter or Winston, yet fields 9 and 13 discuss and extend
   them. Check whether field 8 is incomplete or the extension is genuinely unrequested — it
   changes whether these are D-19 bridges or something else.
7. **FY2005 — a one-day disagreement on the request date.** The cover memo dates the state's
   memorandum 2005-02-25; form field 17 prints 2005-02-24.
8. **FY2016-b — two different CFR subsections for one action.** Field 9 cites
   **7 CFR 273.24(f)(1)(ii)**; fields 6 and 8 both cite **273.24(f)(2)(ii)**. The document
   does not reconcile them. Field 8's was used. Confirm which is correct.
9. **FY1999-a / FY2001-a — `data_nonconformance` flags that may be era-normal, not
   departures.** Both agents set `non_bls_source` and `nonstandard_averaging` true because the
   data is attributed to the Alabama Department of Industrial Relations over a 12–14 month
   window. Both flagged that these documents **predate the 2006 24-month guidance**, and that
   AL DIR is very likely the BLS-LAUS cooperating agency. Decide whether the flags mean
   "departure from the standard" or "pre-standard vintage" — as written they will read as
   the former in `2224`. FY2003-a's agent, facing the same 12-month window, deliberately did
   **not** flag it, so the corpus is already inconsistent on this.

### B. Internal count / citation mismatches (no value change)

10. **FY2002-a — "Winton" for Winston.** Field 8's recap sentence; the same field's opening
    list and field 9 both spell it correctly.
11. **FY2003-a — "Winton" for Winston** again, in field 13. Same document family, same typo,
    two documents apart.
12. **FY1999-a — "Green" for Greene** in field 8; field 9 and the cover memo are correct.
13. **FY2007 — a region's total row labelled as a sub-region's.** Region 6's table header reads
    "Region 6:" but its total row reads "Total for Sub-Region." Likely copy-paste; confirm it
    does not imply a further split.
14. **FY2007 — "request to for an extension of modification"** in the cover memo (grammatical,
    transcribed as-is).
15. **FY2001-b — an LSA designation window shorter than the waiver it supports.** The cited DOL
    designation runs 2000-10-01→2001-09-30; the waiver is granted through **2002-03-31**, six
    months past it. The document does not address the gap. Check whether this recurs across
    970225's other years — if it does, it is a systematic feature of the LSA waivers, not an
    oversight.
16. **FY2009 — a routing-footer date used as the response date.** The letter itself carries no
    "Date:" line; the agent used the internal finalisation stamp (2009-01-27).
17. **FY2002-a / FY2001-a — blank field 16** ("date of national office action") on forms that
    are themselves that action. Cover-memo dates were used instead.
18. **FY2000-a — two staff clearance dates** in the page-1 routing block (2000-01-25 and
    2000-01-28). Routing variance, not a data problem.

### C. Recurring traps for `2224`

19. **`possible_double_counting` is false on all 371 AL rows — and that may be wrong.**
    Prichard **city** appears as its own unit in FY2007, FY2008 and FY2009 while Mobile
    **County**, which contains it, is a unit in FY2005 (denied) and inside Region 6 in other
    years. Anniston, Bessemer, Birmingham and Gadsden cities appear in FY2007 alongside county
    bundles. The FY2009 agent checked and found Mobile absent from that document's 31 counties,
    which is correct *within* the document — but the flag is document-scoped, so cross-document
    city/county overlap is invisible. Same class as the MO note that the flag fires per
    document rather than per row.
20. **Serial is a `float` in the flat file.** `waiver_serial_number` reads `970043.0` /
    `970225.0` / `2150024.0`. Cast to string before any join, and note **970043 and 970225
    are live simultaneously** (see D-18) so a serial-keyed join must not assume one per
    state-year.
21. **The FY2016 pair straddles fiscal years.** `fy2016-a` covers 2016-01-01→2016-12-31 under
    a filename and FY label of 2016. `_fy_from_name` parses it fine (no D-03 instance), which
    is precisely why it is dangerous: the row is *keyed* correctly and *covers* the wrong
    span. See D-04.
22. **FY2011 contributes a unit-row with a null area.** The zero-unit group flattens to one
    row with `geographic_unit_name` null — 371 flat rows against 370 units. Any unit-level
    count must decide whether that row exists.
23. **AL has no `state_alternative_coverage`, no `soft_criterion_invoked`, and no
    `non_standard_geography` anywhere** (0 of 371 rows each). Alabama is entirely standard
    counties plus seven LAUS cities, as the tier registry predicted. Useful as a negative
    control when those columns are exercised elsewhere.

---

## Agent judgment calls and deviations — AL run (2026-08-15)

Every place the spec did not determine the answer and an agent therefore chose. Nothing here
needs a ruling on its own; a call that recurs is how a D-nn entry gets born — D-18 and D-19
both came out of this list.

### Calls that became decisions

1. **The transfer-to-a-sibling-serial call (FY1999-a, FY2000-a, FY2001-a).** Three agents,
   three documents, one coding: `group_action = denied`, with the transfer explained in
   `criteria_summary_text` and `request_level.notes`. All three stated the enum has no
   value for it; the FY2001-a agent named `null` as the defensible alternative. **8 unit-rows.**
   → **D-18**.
2. **The bridge-extension call (FY2002-a, FY2003-a).** Two agents, identical encoding:
   `approved` / `criterion_code = null` / `qualification_level = unknown`, rather than force
   `per_unit` (false — the rates fail) or import the sibling serial's LSA basis (not claimed
   by this document). **6 unit-rows.** → **D-19**.
3. **The zero-units-vs-statewide-unit call (FY2011 vs FY2013).** Opposite choices, both
   correct, and they resolve D-17's split — see that entry.

### Calls left open, no D-nn yet

4. **FY2007 — an unlabelled continuation table read as `per_unit`.** Seven areas (Greene,
   Lamar, Anniston, Bessemer, Birmingham, Gadsden, Prichard) appear in a table with **no region
   heading and no printed total**, unlike the three bundles above it. The agent coded them
   `per_unit` on the spec's decisive test, and flagged the tension with field 9's blanket
   statement that "approval is based on the unemployment rates for the designated multi-county
   areas" — which more plausibly describes only the three named bundles. Worth confirming
   against the PDF: it is the difference between 7 per-unit groups and one more bundle.
5. **FY2005 — a spec/schema conflict the agent resolved toward the schema.** `2220b` says to
   record a unit's independent LSA-eligibility footnote in `criterion_other_explanation`, but
   `2220c` restricts that field to `criterion_code = "other"`. The groups in question are
   `pct20_above_natl`, so the agent put the note in `criteria_summary_text` instead and
   reported the conflict. **This is a genuine inconsistency between the two spec files and
   should be fixed in one of them.**
6. **FY2005 — Mobile/Morgan coded `denied`, not `withdrawn_by_state`.** FNS *suggests* the
   state use its 273.24(g) 15% exemption, but the document does not show the state electing
   it. The agent coded `denied` on the ground that FNS adjudicated. Correct under S-4's test,
   and worth noting as the corpus's cleanest case of the suggestion-without-election shape.
7. **FY2013 — `document_type = other_nonstandard` for the SERO broadcast**, with
   `fns_response_only` named as the runner-up (FNS's email does convey a disposition, but
   region-wide rather than to Alabama). Also `criterion_code = eb_trigger` **inferred** from
   "ABAWD Trigger Notice"; the document never says "Extended Benefits." Both flagged.
8. **FY2013 — dates deliberately left null.** The agent declined to translate "FY 13" into
   2012-10-01→2013-09-30, on the ground that the document states no calendar dates. Conservative
   and consistent with the spec; note it means the row carries no coverage interval at all,
   which D-04's key cannot absorb.
9. **FY2011 — `non_conforming_document = false` on a nearly contentless document.** The agent
   judged the one-line state request to be genuine request content and pushed the unknowns to
   null within a single group, rather than declaring the document non-conforming with zero
   groups. It named this as the extraction's biggest call and arguable either way.
10. **FY1999-a — an inferred effective date.** No effective date is printed; the agent derived
    1999-01-01 from "extended for a period of 1 year" plus the predecessor's 1998-12-31 expiry.
    Arithmetic from stated facts, but flagged as inference.
11. **FY2006 — per-county rates derived, not printed.** The agent computed each member's rate
    from printed labor-force and unemployed counts to run the threshold test, and recorded them
    in `unemployment_rate` marked as derived in `qualification_level_evidence`. This is what
    produced the item-1 finding above; it is also a departure from the more common practice of
    setting `qualifying_basis = unknown` when no rate column is printed (cf. IN FY2004, where
    the agent derived the totals, reproduced them exactly, and *still* set `unknown`). **The
    corpus is inconsistent on this and D-10 should say which is intended.**
12. **FY2005 / FY2008 / FY2009 — contiguity checked and confirmed** against the adjacency lists
    for every joint bundle, including FY2009's 31-county chain. No D-11 instance in Alabama.

### Deviations and tooling notes

13. **No blinding failures.** All 20 agents returned compliance lines; **zero** disclosed
    listing anything under `1022_extractions/` — matching the IN run and improving on MO's one.
    The write-step language was carried in all 20 prompts and now includes the MO writeup's
    recommended addition that the directory is *guaranteed* to exist and needs no check. That
    addition appears to have closed the residual: the one MO disclosure was an existence check.
    **Keep this wording.**
14. **Two agents read `0_lit/00_abawd_rules/002_rules_machine.yaml`** in addition to `2220b`
    — in scope (the rules KB is on the allowed list), disclosed anyway.
15. **The DOC-CLASS WARNING was carried by all 20 prompts, with no batch asymmetry**, and two
    prompts (FY2011, FY2013) carried an additional vintage-specific sentence noting that
    FY2011/FY2013 files have repeatedly proved to be state-authored notices. Both documents did
    turn out to be exactly that. **This is a deviation worth recording:** the extra sentence
    names no document and supplies no answer, but it is a hint the other 18 agents did not get,
    and it was given precisely to the two documents where it would matter. It should either
    become standard for all prompts or be dropped — the current middle position is the same
    asymmetry the IN writeup flagged.

---

## Verification checklist — UT/LA run (2026-08-15)

45 documents (UT 23, LA 22), 45/45 schema-valid on the first pass, 455 unit-rows. Per-document
facts to check against the source PDFs before the values below are trusted. Agents transcribe
suspect values faithfully rather than correcting them, so these are the cells the corpus is
knowingly carrying as printed.

**Before using this list, read item 6 under "Pending work that is not a decision."** Three of
the flags agents raised in this run were false positives from the 24-month cumulative-count
convention and are deliberately **not** listed below.

### A. Would change an extracted value — check first

1. **LA FY2001 — the denial that becomes an approval.** The packet denies Calcasieu (balance),
   Livingston and West Feliciana against a "national rate" of 5.28%, then two later FNS
   documents in the same PDF recompute (5.28% was 120%-of-national, not national), re-round,
   and approve all three. The extraction emits **both** the denied and the approved groups.
   Confirm that is the wanted record rather than final-state-only, and confirm Livingston's
   5.25 → 5.3 round-half-up, which is outcome-determinative and unstated. See D-16, D-02.
2. **LA FY2001 — Plaquemines.** Approved under a heading reading "Average Unemployment Rate
   Greater Than 120% of National" at 5.05% against a cited national 5.04% — 100.2%, not 120%.
   No supporting arithmetic is shown for Plaquemines, unlike the other six parishes. Either the
   heading does not govern this row or the approval does not follow the rule.
3. **LA FY2001 page 5 is an Arkansas spreadsheet.** "ARKANSAS ABAWD WAIVER REQUEST FOR FY 2001
   UNEMPLOYMENT." Confirm it is a scrape artifact and carries no LA content. See non-decision
   item 7.
4. **LA FY2003 — approval on a substituted, older data window.** The state's submitted
   CY2001–2002 figure (6.04% vs a 6.08% threshold) **fails**, and FNS says so, then approves on
   CY2000–2001 (5.7% vs 5.2%). Confirm which window the panel should record; the extraction
   carries 5.7 as the unit rate and `older_vintage = true`.
5. **LA FY2024 — the threshold is mis-rounded in the grant direction.** National 4.4% → the
   document states a 5.2% threshold; 4.4 × 1.2 = 5.28 → 5.3. The bundle's own rate is 5.2%, so
   it clears the stated threshold and fails the correct one. Same defect as AL FY2006.
6. **UT FY2009-a — San Juan.** 5.6% against a cited national 4.7% is 119.1% above, not the "20
   percent above" the letter claims; the literal threshold is 5.64%. Approved.
7. **UT FY2008 — the data window contradicts itself.** Page 1 calls March 2005–February 2007
   "a 24-month period" (correct); field 9 calls the identical range "a 12-month period."
   `window_type` was coded `24_month_moving_average` on the page-1 reading.
8. **UT FY2017 — the data window contradicts itself, the other way.** Field 8 states "the
   24-month period of April 2014 through March 2016"; the page-2 table header prints "April
   2013 – March 2016" (36 months). The agent took the narrative's 24-month window and left
   `nonstandard_averaging` null as undeterminable. One of the two is a typo; which one changes
   the rate.
9. **UT FY2003 — the state's own submission disagrees with itself on the requested end date.**
   Waiver Request field 12 says "until March 31, 2004"; the state's cover letter of the same
   date and the FNS grant both say April 30, 2004. `applied_waiver_end_date` carries
   2004-03-31 (the structured field).
10. **LA FY2017-b — the requested end date.** Field 7 prints "through August **21**, 2018"
    against August **31**, 2018 in the cover letter, field 11, and the "12-month period"
    framing. Transcribed as printed into `applied_waiver_end_date`.
11. **UT FY1998 — the requested duration is arithmetically impossible.** Field 8 records the
    state asking to "extend the waiver for a period of 2 years, expiring on November 30, 1998"
    from a Dec 1 1997 start. FNS granted 1 year.
12. **UT FY2000 — duration mismatch.** Field 8 says the state requested **14 months** ending
    2001-01-31; field 13 grants "**1 year**," same end date. No start date is printed to
    reconcile them; both figures were preserved.
13. **LA FY2006 — field 17 date.** "Date of State agency's request: October 26, 2004," thirteen
    months before the Dec 2005 e-mail the letter answers and before the Nov 2005–Oct 2006
    waiver period. Probable template carry-forward or a typo for 2005.
14. **UT FY2009 — two conflicting dates, one of them impossible.** The letter says the current
    waiver "expired on September 30, **2009**" while extending it through January 30, 2009 — a
    date before the stated expiry. It also gives the revised-request deadline as December 30,
    **2009** in one paragraph and December 30, **2008** in another. Chronology implies 2008 in
    both cases; both were transcribed as printed.
15. **UT FY1999-a vs UT FY2000 — the same action, two granted expiry dates.** The Word draft
    grants the five approved counties to **2000-01-31**; the PDF grants them to **2001-01-31**.
    Everything else in the two extractions is identical. Decide which is authoritative before
    either enters the panel — it is a full year of coverage for five counties. See D-02.
16. **UT FY1999-a — "seven counties" for six.** The alt-procedures paragraph enumerates six
    counties (Duchesne, Emery, San Juan, Garfield, Uintah, Grand) and then calls them "the seven
    counties." The extracting agent notes this cannot be a conversion artifact, since `textutil`
    does exact character extraction rather than OCR pattern-guessing — so it is a drafting error,
    plausibly a leftover from an earlier seven-county list.
17. **UT FY1999-a — no signature block survives the conversion.** No state or FNS official name
    appears anywhere in the converted text, which is unusual for a Waiver Response. This may be
    a genuinely unsigned working copy or a signature image / text box the `.doc`→text conversion
    dropped; the two cannot be distinguished from plain text. The official-name fields are null
    and should be treated as **unknown, not absent**. Same for `date_ro_transmittal_request`,
    which never appears in the converted text at all.
18. **LA FY2016 — type of request.** Form field 2 says "Initial"; the RE line and cover letter
    call it an Extension. Field 2's value was kept. Note also that all three processing dates
    (state request, RO transmittal, national-office action) print as the same day,
    2016-01-13, and the approval postdates the waiver's own Dec 1 2015 start by six weeks —
    which the letter acknowledges and justifies as an exceptional retroactive approval.

### B. Internal count / citation mismatches (no value change)

19. **The page-header serial is corrupt on four documents, in two states — and it is in the
    source, not the scan.** UT FY1999-b, UT FY2000 and UT FY1999-a all print `907138` for
    `970138` in the page-2/3 running header while every other occurrence is correct; LA FY2000
    prints `907775` for `970075` in the same position. UT FY1999-a settles the cause: it is a
    **native Word file**, extracted as text rather than OCR'd, and the transposition is still
    there — so this is a defect in the documents themselves (a template's header field), not a
    scanning artifact. **No serial should ever be read from a page header.**
20. **`7 CFR 274.24` for `273.24`** on UT FY2003 (both copies of the Waiver Response, field 3)
    and LA FY2009-a (field 9, while field 10 is correct). Same typo already recorded on four
    Kansas forms. Now three states.
21. **UT FY2005 — the form's field numbering is broken.** Two fields are both labelled "10.",
    the next is "11." (should be 12), then "12." (should be 13), then it jumps to "14." Fields
    were mapped by label text, not number. Field 10 also prints "an insufficient number of
    jobs." twice in succession.
22. **UT FY2001 — the recited prior list omits a county it then removes.** Page 6 lists seven
    prior counties (and misspells Garfield as "Garfiled"); the next sentence removes "Wayne and
    Uintah," though Uintah is not in the list just given. The second Waiver Response in the same
    packet (pp. 4–5) is **truncated after field 8** — no decision text — and misspells Uintah as
    "Unitah". UT FY2002 repeats the "Unitah" misspelling.
23. **LA FY2024 — "Table 1: Counties" heads a table of 33 rows each labelled "… Parish."**
    Louisiana has no counties. `area_type` was coded `parish` from the row labels. The same
    document's contact email prints as `Timothy.Jenkins@DCFS@la.gov` (two @ signs), and its
    routing footer carries a 2021 date inside a 2023 document.
24. **LA FY2002 / FY2003 — garbled boilerplate in field 7.** "…does not have a sufficient
    number of jobs to provide employment for the individuals benefits because they were exempt
    from these requirements" — a non-sequitur present in both documents, i.e. a template defect
    rather than a scan artifact. Not schema-relevant; recorded so it is not chased.
25. **LA FY1999 / FY2017-b / LA FY2001 — signed by someone other than the named official.**
    Cursive signature over a different typed name (FY1999); "[Casey/Cany] McConnell FOR Sasha
    Gersten-Paal" (FY2017-b); "for Esther Phillips" (FY2001). `fns_official_name` carries the
    typed name in all three. If signatory identity ever matters, it is not captured.
26. **LA FY1998-a — field 6 prints "MWRO"** (Midwest) on a Louisiana document whose cover letter
    is addressed to the Southwest Regional Office and whose cc list reads "All Regions (except
    SWRO)." Transcribed as printed. Compare the MS FY2003 "Florida" trap.
27. **LA FY2009-a — a stray "Total for Sub-region 5.8"** appears after the parish table with no
    other sub-region structure anywhere in the document; reads as a template leftover repeating
    the threshold value.
28. **UT FY2016 — the superseding letter misdescribes what it supersedes**, two different ways,
    two sentences apart. See D-02.

### C. Threshold-hugging bundles (extends the KY/GA, SC/AR, KS/NE/MS and MO tables)

Utah and Louisiana become the **tenth and eleventh** states in this pattern.

| doc | bundle | aggregate | threshold | members below it |
|---|---|---|---|---|
| UT FY2016 | Garfield, Grand, San Juan, Wayne | **7.7** | **7.7** | 1 of 4 (Grand ≈6.58) |
| LA FY2024 | 33 parishes | **5.2** | **5.2** (as stated; 5.3 correctly) | not determinable — no per-parish rates |
| LA FY2008 | 61 parishes | 6.3 | 6.3 (= 120% of 5.25 exactly) | **25 of 54** rated parishes (min ≈5.1) |
| LA FY2009-a | 55 parishes | not printed | 5.8 | **27 of 48** rated parishes (min 4.1) |
| LA approval-2018 | statewide | 5.6 | 5.6 | n/a (single unit; clears on unrounded figures) |
| UT FY2017 | 6 counties | 6.7 | 6.6 | 2 of 6 (Carbon 5.47, Emery 5.79) |
| UT approval-2018 | same 6 counties | 6.9 | 5.9 | 1 of 6 (Carbon 5.85) |
| UT FY2007 | Emery, Grand, San Juan | 6.8 | 6.3 | 2 of 3 — and Emery+Grand alone ≈6.05 **fails** |
| UT FY2006 | Five County AOG (Garfield, Kane) | 6.9 | 6.5 | 1 of 2 (Kane 4.4) |
| UT FY2005 | Five County (Garfield, Kane); Uintah Basin (Daggett, Duchesne) | 7.8; 8.0 | 7.1 | 1 of 2 each (Kane 4.4; Daggett 4.7) |

Two of these are worth separating from the rest. **LA FY2008 and FY2009-a are the largest
carried populations in the corpus** — 25 and 27 sub-threshold parishes riding a single
statewide-scale bundle, which is set-packing at the scale of a whole state rather than a
region. And **UT FY2007 is a rare case where the bundle fails without its load-bearing
member**: drop San Juan and the remaining two counties come to ≈6.05 against 6.3. That is the
v1_5 drop-the-unit-and-recompute tie-break firing correctly on a new state — see the judgment
calls list, item 3.

### D. Recurring traps for `2224` specific to this pair

29. **`area_type` is `parish` for all 287 Louisiana unit-rows and `county` for Utah's 114.** Any
    join keyed on `area_type = 'county'` silently drops Louisiana entirely.
30. **The MSA row.** LA FY2008 emits 7 parish rows for the New Orleans-Metairie-Kenner MSA with
    null rates; LA FY2009-a emits **one** row of `area_type = metropolitan statistical area`
    covering the same 7 parishes. Unit counts for the two documents are not comparable and a
    parish-year panel will have a hole in FY2009-a. See D-20.
31. **`possible_double_counting = true` on 15 rows, and the semantics differ from every prior
    run.** UT FY2001's 15 rows are flagged because six counties appear in both an FY2001
    approved group and an FY2002 requested (null-action) group **in the same bundled packet** —
    i.e. the same area in two sequential annual cycles, not simultaneous double coverage. The MO
    run flagged the opposite problem (document-scoped flagging inflating the affected count);
    here the flag is row-correct but *temporally* misleading. `2224` must not read this column
    as "covered twice."
32. **Zero rows carry `non_standard_geography` or `soft_criterion_invoked`** across both states.
    UT is standard counties plus LAUS cities and LA is standard parishes plus LAUS cities, as
    the tier registry predicted. LA's three `balance of county` rows (Bossier) are the only
    non-whole-unit geography.
33. **`fiscal_year` is non-null on all 455 rows**, including both period-named `approval-*`
    files. No D-03 instances. (455 is the flat-CSV figure, i.e. the 45 PDFs; UT FY1999-a's 6
    rows are not in it — see non-decision item 7.)
34. **`state` is normalised to `Louisiana` / `Utah` on every row.** No repeat of the MS
    `Florida` trap.
35. **UT FY2009 contributes 2 groups and 0 units**, so a unit-level join loses the document
    entirely, including a real FNS denial. See D-06.

---

## Agent judgment calls and deviations — UT/LA run (2026-08-15)

Every place `2220b` did not determine the answer and an agent therefore chose. Nothing here
needs a ruling on its own; a call that recurs is how a D-nn entry gets born, and six did in
this run (D-20 … D-25).

### A. Calls that became decisions

1. **The MSA row: expand or hold** — LA FY2008 (expand into 7 parishes) vs LA FY2009-a (hold as
   one unit). Same serial, adjacent years, same table shape. → **D-20**.
2. **`qualifying_basis` for a lone statewide unit under a rate rule** — LA FY2002 and FY2019
   chose `own_rate`; LA FY2003 and the 2018 approval chose `statewide`. All four flagged it.
   → **D-21**.
3. **`data_nonconformance` where the criterion has its own data regime** — LA FY2004 and FY2006
   set the flags true with an explanatory note; LA FY2005 and FY2023 left the object null.
   → **D-22**.
4. **Duration trims** — LA FY2002 (17 months asked, 12 granted), UT FY1998 (2 years asked, 1
   granted), UT FY2007 (17 months "as an exception"). All three agents kept one `approved`
   group and used the `applied_*` vs granted date pair; one argued explicitly against emitting
   a second denied group. → **D-23**.
5. **A disaster-relief basis with no code** — LA FY2009 (Stafford Act §402 / FNA §5(h), post
   Gustav/Ike). The agent grepped the rules KB for a disaster code, found none, and refused to
   force `other`, calling it "the single most consequential call in this extraction."
   → **D-24**.
6. **Derived per-unit rates: populate or leave null** — UT approval-2018 and FY2017 populated
   `unemployment_rate` from printed counts; UT FY2007 and FY2016 computed the same rates, used
   them to set `qualifying_basis`, and left the field null as "not printed." → **D-25**.

### B. Calls that change a coded value

7. **UT FY2007 — the drop-the-unit-and-recompute tie-break, applied unprompted.** The prose
   attributes San Juan's qualification to its FY2007 LSA designation, which would pull it out
   into its own `lsa`/`per_unit` group. The agent recomputed Emery+Grand without it (≈6.05%
   against a 6.3% threshold — fails), concluded San Juan is load-bearing where the table puts
   it, and kept the three-county `joint_aggregate` group with San Juan's LSA mention recorded
   as the secondary label. That is the v1_5 rule from the ND FY2006 Rolette adjudication firing
   correctly in a new state, in the opposite direction (keeping a unit in rather than moving
   one), with the arithmetic shown. **Positive control.**
8. **UT FY2006 — three evaluated sets from one "contiguous sub-region" sentence.** Fields 8/9
   describe all ten areas as one contiguous sub-region with an aggregate rate; the tables show
   two named AOG sets with printed totals plus four areas with no set total, and two of the ten
   are geographically remote from the rest. The agent emitted 6 groups on the table structure
   plus the adjacency lists. Alternative: one 10-area `joint_aggregate` group per the literal
   prose. See D-11.
9. **UT FY2006 — Southeast AOG coded `joint_aggregate` though every member clears alone.** The
   agent ranked the spec's "named set + printed combined total" signal above the per-area
   counterfactual, and said so; the counterfactual test would have given `per_unit`. This is the
   one place in the run where two spec signals point in different directions and neither is
   marked as dominant.
10. **UT FY2000 — Uintah coded `denied`** for falling off the FY2000 LSA list, though FNS never
    uses the word "denied" (only "does not include Uintah County … may submit additional data").
    The agent flagged the soft edge. UT FY2002 coded the same event as no-group. → D-12.
11. **UT FY1999-b — Kane County's criterion set to `null` rather than carried-forward `lsa`.**
    FNS states Kane is not on the FY1999 list and extends it anyway; coding `lsa` would assert a
    designation the document disclaims. → D-19.
12. **UT FY1998 — Carbon and Piute kept as ONE `withdrawn_by_state` group**, not split per area,
    because no rule is being evaluated for a removal so the per-unit splitting logic has no
    purchase. Defensible either way; it is the only place in the run where a multi-unit group
    carries a non-approval action.
13. **LA FY1999 — ten parishes recoded from `pct10_statutory` to `lsa`.** They entered under
    970025 on a rate basis; this document re-approves them under 970075 "based on their
    designations as LSAs." The agent coded the document's own stated basis. The rule migration
    leaves no trace in the emitted data — the IN FY2002 Randolph problem at ten times the scale.
    → D-04.
14. **LA FY2000 — "Bossier (except for Bossier City)" as one balance-of-county unit**, rather
    than a plain Bossier unit (which erases the printed exclusion) or an invented Bossier City
    unit (which asserts an adjudication the letter does not make). → D-14.
15. **LA FY2011 — the ARRA recital declined.** The letter says "the current waiver is pursuant
    to [ARRA]" and then rests the FY2011 extension on the EB trigger. FFY2011 lies wholly
    outside the ARRA window, so the agent treated the ARRA sentence as background about the
    prior waiver and coded `eb_trigger`. Correct application of the v1_5 recital rule.
16. **LA FY2022 — `eb_trigger` kept inside the FFCRA window.** Coverage period Sep 2021–Aug 2022
    sits entirely within the federal suspension window; the disposition rests on DOL Trigger
    Notice 2020-34 and the letter never mentions the suspension. The agent coded the stated
    basis. **Another positive control for the v1_5 disposition-based rule**, which held on every
    document in this run that tested it (also LA FY2011, LA FY2013, UT FY2011).
17. **LA FY2009 — no group for the superseded 61-/55-parish waiver.** The letter recites a prior
    action that FNS had already taken elsewhere; the agent put it in `request_level.notes`
    rather than inventing a group, extending case (c) to "previously decided elsewhere."

### C. Calls on dates

18. **UT FY1999-b — "end of February 1999" resolved to 1999-02-28.**
19. **UT FY1999-b — a garbled date stamp ("JAN 2 1 1999") resolved to 1999-01-21** using the
    routing box's 1/19 and 1/20 sign-offs; 1/2/99 would predate the signatures.
20. **UT FY2016 — a cover-letter stamp OCRs as "SEP 1 6 1018"**; resolved to 2015-09-16 from the
    form's field 14.
21. **UT FY2009 — the letter date OCRs as "NOV 2 1 znnn"**; resolved to 2008-11-21 from internal
    chronology, with the year digits flagged as unclean.
22. **UT FY1998 — `response_date` taken from a routing/typist footer** ("…DRAFT:1/14/98:FINAL:
    1/20/98:va") because no letterhead date is visible. Explicitly flagged as an inference from
    a routing code.
23. **UT FY2000 — `response_date` taken from a "DEC 09 1999" received-stamp**, the only date on
    the page.
24. **Several agents declined to back-compute a missing start date** from duration + expiry
    (UT FY1998, FY1999-b, FY2000, FY2002; LA FY1998-a, FY1999, FY2000), leaving
    `waiver_effective_date` null. Consistent across the run and consistent with "never invent
    values" — worth keeping as the convention, but it means a large block of early rows have no
    start date at all.
25. **FFY-to-calendar conversion split.** LA FY2013 converted "through FFY 2013" to
    `applied_waiver_end_date = 2013-09-30` but left the start null; LA FY2012 did the same;
    UT FY2011 put its stated end date in `waiver_expiry_date` rather than `applied_waiver_end_date`,
    reasoning that eb_trigger is self-certifying so the state's declared window is effective
    rather than merely applied-for. That last call is inconsistent with the other four
    state-request documents in the run and is the one to standardise. See D-23's field-population
    contract.

### D. Conventions that drifted between agents

26. **`orig_text` for distributive lists — a three-way drift inside one serial.** The FNS forms
    print "Counties of A, B, C" or "…, and West Carroll Parishes", with the type word appearing
    once for the whole list. Within UT serial **970138** alone: FY1998 bare tokens, FY1999-b bare
    tokens, FY2000 appended "County" to each, FY2002 bare tokens, FY2015 appended "County".
    Louisiana split the same way (FY1998-a and FY2008 reconstructed "<Name> Parish"; others kept
    the bare name). This is not a decision so much as a missing sentence in `2220b`, but it lands
    directly on the channel `2225` scores — gold stores the verbatim print, and "Carbon" vs
    "Carbon County" is a name miss. **Recommend stating the rule explicitly** (reconstruct the
    distributive type word, since gold's own convention is `<Name> County`), and note that
    `name` is unaffected either way.
27. **"St. John the Baptist" — two agents, opposite calls, same parish.** LA FY2000's agent
    declined to expand the printed "St. John Baptist" because the missing word "the" exceeds the
    spec's "a character or two" tolerance; LA FY1999's and LA FY2001's agents expanded it,
    calling it an unambiguous match to exactly one reference entry and flagging the stretch.
    Both preserved the verbatim in `orig_text`. The tolerance rule needs a word-level clause.
28. **Uncontroversial repairs, applied consistently** where they did fall inside tolerance:
    `Clairborne`→Claiborne, `DeSoto`→De Soto, `Point Coupee`→Pointe Coupee, `La Salle`→LaSalle
    (LA); `Unitah`→Uintah and `Garfiled`→Garfield left as printed in `orig_text` (UT). The
    geography reference did real work in Louisiana, where parish spellings are the corpus's
    most error-prone.
29. **`state_official_name` / `fns_official_name` have no stable mapping.** The modern forms name
    three or four people — letter addressee, state agency contact, FNS regional contact, FNS
    signer — and the schema has one slot each side. Agents split between "addressee + signer"
    (most) and "contact fields" (a few), and several recorded the unused names in
    `request_level.notes`. Harmless today; would break any attempt to use signatory identity.
30. **`possible_double_counting` semantics.** UT FY2001 set it `true` for the same county
    appearing in two *sequential annual cycles* within one bundled packet, noting the literal
    condition was met though it does not mean simultaneous double coverage. Most single-group
    documents left it null per the spec's moot rule. See checklist item 28.
31. **Whether to populate `applied_waiver_*` when the request and grant coincide.** UT FY2019,
    UT FY2020, UT approval-2018, LA approval-2018 and LA FY2016 populated them identically to the
    granted dates ("the document states both"); others left them null on the reasoning that
    identical values carry no information. This is exactly the field-population contract D-23
    needs tightened, because "null" currently means both "not stated" and "same as granted."

### E. Where the agents were right to refuse

32. **LA FY2009 refused `other`** for a disaster waiver rather than absorb a different statute
    into the soft-jobs catch-all (→ D-24).
33. **UT FY1999-b and UT FY2009 refused to invent a criterion** for bridge extensions (→ D-19).
34. **UT FY2009 refused to fabricate placeholder units** for two groups whose areas the document
    never names, emitting empty arrays instead (→ D-06).
35. **LA FY2024 set `qualifying_basis = unknown` on all 33 parishes** rather than
    `carried_by_group`, because with no per-parish rates printed, "carried" would overclaim.
    Correct under D-10 and the reason 40 of LA's 322 rows are `unknown`.
36. **UT FY2001 refused to emit a group from a truncated Waiver Response** (pp. 4–5, fields 9–20
    missing from the scan) even though its cover letter says "our response is attached."
    Emitting an approval would have fabricated the disposition.
37. **LA FY2001 preserved a mislabelled figure as printed.** The Waiver Response calls 5.28% "the
    national unemployment rate" when the later corrections show it is 120% of national; the agent
    transcribed each document instance as written rather than harmonising to the corrected value.

### F. Protocol deviations and tooling notes

38. **All 45 returned blinding compliance lines. Seven disclosed a deviation — a regression, and
    the run's main procedural finding.** Four agents ran `ls` / `ls -la` on their output
    directory (LA FY2004, LA FY2001, UT FY2003, LA FY2019); three ran `mkdir -p` on it (UT
    FY1998, UT FY2004, LA approval-2018). Every disclosure states the action came *after* the
    extraction judgment was formed; the four `ls` cases each saw one or two Alabama sibling
    **filenames** (`al-abawd-response-fy2000-a/-b.json`, `al-abawd-response-fy2005/2006.json`,
    `al-abawd-response-fy2016-a.json`) and none opened a file. The three `mkdir -p` cases
    revealed nothing at all — they are protocol violations without any information content.
    (Separately, LA FY2022 disclosed `ls`-ing its own GEO file and PDF to confirm they existed;
    those are allowed paths and this is not the same class of deviation.)

    **This is 7 of 45 against zero in the IN and AL runs, and the write-step wording was
    unchanged** — the AL run's "the directory is *guaranteed* to exist and needs no check"
    sentence was carried verbatim. So the wording is not what closed AL's gap, or not the only
    thing. The one structural difference in this run is item 39 below: the instruction lived in a
    task **file** the agent had to read rather than inline in the prompt. That is the leading
    hypothesis and it is testable — restore inline prompts for one state and compare. Until then
    the honest statement is that this run's blinding hygiene is the worst since SC/AR, that the
    exposure was filenames of an unrelated state and cannot have informed any UT or LA judgment,
    and that the self-reporting worked in every case.

39. **Protocol deviation, deliberate and disclosed: the prompt was factored into a shared file.**
    All 45 agents received a two-paragraph dispatch pointing at one task file
    (`fanout_task_ut_la.md`) holding the full spec-reading order, geography rules, DOC-CLASS
    WARNING, blinding block and write step, plus their own PDF/GEO/OUT/PAGES. Prior runs inlined
    the whole task in every prompt. The motive was the asymmetry the IN and AL writeups both
    flagged and both asked to be fixed — under this scheme every agent provably received
    byte-identical instructions and the DOC-CLASS WARNING was generic across all vintages, naming
    no document and no fiscal year. That goal was met: there is **no prompt asymmetry in this
    run**. The cost is item 38's regression. Recommend keeping the identical-instruction
    property and testing whether inlining the *write step and blinding block* while keeping the
    rest in the file recovers AL's zero.

40. **A short blinding backstop was inlined in each dispatch** (read only the spec, KB, GEO and
    PDF; no gold, no comparison CSV, no other extraction JSON, no listing under
    `1022_extractions/`) so that an agent that somehow skipped the task file would still be
    blinded. No agent skipped it.

41. **Two agents used scratchpad tooling.** LA FY1999 wrote a throwaway Python script to validate
    its own JSON against `2220c` (schema-only, no comparison to gold or other extractions) and
    deleted it; LA FY2001 built its JSON via a scratchpad generation script. Both disclosed.
    Neither touched a forbidden path.

42. **Several agents read `0_lit/00_abawd_rules/002_rules_machine.yaml`** — in scope, on the
    allowed list, disclosed anyway. LA FY2009 grepped it specifically for
    `disaster`/`stafford`/`d-snap`/`402` before concluding no code exists (→ D-24), which is
    exactly the behaviour the KB is there to support.

43. **No agent read a gold sheet, comparison CSV, ledger, validator, protocol writeup, or another
    extraction JSON, and none searched git history.** The substantive blinding held on all 45.

---

## Verification checklist — MT/SD run (2026-08-15)

Per-document facts to check against the source PDFs. Agents transcribe suspect values faithfully
rather than correcting them, so these are the known-suspect cells in the MT/SD slice.

**Run provenance caveat.** 41 of these 57 documents were extracted in an earlier session that hit
a budget cap and stopped before collating; 15 were never dispatched and 1
(`mt-abawd-response-fy2017`) was written as invalid JSON. This session re-ran those 16 and
collated/flattened the whole slice. The 41 are **not** re-verified here beyond schema validity and
the flat-CSV aggregates — items below drawn from them come from the flat CSV and the JSON free
text, not from a fresh agent report, and are marked *(prior session)*.

### A. Would change extracted values — check first

1. **MT FY2016 — two 7-county bundles in which EVERY member is below threshold.** Group 1
   (Flathead, Toole, Liberty + 4) and Group 2 (Treasure, Rosebud, Petroleum, Musselshell, Golden
   Valley, Wheatland + 1) clear only in aggregate, at 8.1% and 8.07% against an 8.1% threshold.
   Flathead computes to ~7.1%, Toole ~3.5%, Liberty ~3.3%. Confirm the printed unemployed and
   labor-force counts, since **no per-county rate is printed** and every figure above is derived
   (see D-25). The whole group's `joint_aggregate` coding rests on this arithmetic.
2. **MT `approval-2018` — same construction, and confirm the 31 units.** 9 of 14 counties in
   Group 1 and 10 of 11 in Group 2 compute below the 5.8% threshold; only Big Horn (8.3%) clears
   in Group 2. Also confirm the page-4 table headed **"Contiguous towns and cities"** whose every
   row is a county — read as a template artifact and transcribed as counties.
3. **MT FY2017 — the "contiguous" 5-county bundle that is not contiguous.** Big Horn, Petroleum,
   Prairie, Rosebud, Treasure; **Prairie borders none of the other four** per the adjacency lists
   (→ D-11). Confirm the membership list is transcribed correctly before treating this as a state
   error rather than an extraction one.
4. **MT FY2017 vs FY2016 — same serial, opposite rate encoding.** FY2017 left
   `unemployment_rate` null for its 16 counties; FY2016 and `approval-2018` populated it with
   derived values (→ D-25). Nothing to verify in the document; flagged here because a reader
   comparing the two years will see a data gap that is a convention difference, not a source
   difference.
5. **SD FY2002 — the expiry year contradicts itself.** The cover memo says the waivers "will
   expire on April 30, **2002**"; the Waiver Response field 13 and the FNS transmittal letter both
   say **2003**, and a stated 13-month duration is only consistent with 2003. The agent used 2003
   throughout. Confirm which the form actually prints.
6. **SD FY2002 — field 8 lists two reservations under BOTH tests, with different rates.**
   Flandreau Santee Sioux and Lower Brule appear under the 10%/12-month test and the
   20%/24-month test (e.g. 11.4% vs 11.7%). Field 9 and the transmittal letter list each once,
   under the 10% test only; the agent followed field 9 as the operative decision. Confirm field 9.
7. **SD FY2023 — field 8 contradicts field 7 and the subject line.** Field 8 reads as a blanket
   approval and never mentions the Lake Traverse denial, though field 7 denies it and the letter
   is titled "Partial Approval." Confirm the denial is real before trusting the 8-approved /
   1-denied split.
8. **SD FY2023 — Yankton's ACS rate is below the benchmark the document claims for it.** Printed
   10.7% against the "over two times national" (10.8%) benchmark the letter says applies to all
   five approved soft-criterion areas. Approved anyway. Check the printed figure.
9. **SD FY2020 — Yankton sits exactly at the threshold** (4.8% vs 4.8%), and **SD FY2025's
   "Combined Area 2"** likewise (4.4% vs 4.4%). Both approved. Confirm both printed rates and
   thresholds; exact-equality cases decide how `2224` must round (cf. the LA FY2001 rounding
   reversal).
10. **SD FY2002 — Marshall County remainder denied at 5.09%/5.1% against ~5.3%.** The only
    denial in that document and the margin is small; confirm the printed rate and threshold.

### B. Internal counts, labels and geography

11. **MT FY2017 OCR artifact.** The PDF text layer renders "Northern Cheyenne Indian Reservation"
    as "orthem Cheyenne…" (dropped leading N); the page image shows it in full. `orig_text` was
    taken from the image. Confirm.
12. **MT FY2016 "Big Hom" → Big Horn.** Classic `rn`→`m` OCR artifact; canonical spelling in
    `name`, "Big Hom" verbatim in `orig_text`.
13. **SD FY2025 "Bennet County"** (Table 3) and **SD FY2024 cover letter "Bennet"** — both single
    printed typos for Bennett, and in SD FY2024 the form's own Table 2 spells it correctly in the
    same document. `name` = Bennett, `orig_text` verbatim.
14. **SD FY2002 "Melette" vs "Mellette"** — the document uses both spellings for the same county
    in one document. Canonical in `name`, "Melette" in `orig_text`.
15. **SD FY2016 prints "Shannon"**, correctly for its vintage — the Shannon→Oglala Lakota rename
    is 2015 and this document straddles it. Kept as printed, **not** harmonised. SD FY2025 and
    FY2024 print "Oglala Lakota." Confirm no year was silently renamed in either direction.
16. **MT `approval-2018` and MT FY2021-b print no serial number at all**, as do MT FY2023/2024/2025
    and SD FY2022/2023/2024/2025 — a newer Waiver Response template whose field numbering starts at
    "Request Type" with no serial field. Coded `null`. Confirm the field is genuinely absent rather
    than missed, since serial is the join key for D-02/D-18.
17. **MT FY2021-a vs FY2021-b are different instruments, not an a/b split of one.** FY2021-b is a
    statewide EB-trigger approval effective 2021-03-01; FY2021-a approves 13 named areas effective
    2021-08-01 on the 20% rule. Confirm both, since a reader will expect siblings to match.

### C. Recurring traps for `2224` specific to this pair

18. **221 SD unit-rows carry `possible_double_counting = true` for reservation–county territorial
    overlap, not name duplication** (→ D-14 update). The flag cannot currently distinguish the two
    cases by query; the distinction lives only in `double_counting_note` free text.
19. **The contiguity check is unperformable on all 289 reservation-area rows** — the geo-context
    files map no reservation to a parent county (→ D-11 update). Not an extraction defect.
20. **SD's soft-criterion route is concentrated, not incidental**: 29 of the pair's 33
    `soft_criterion_invoked` rows, including 5 of 11 groups in FY2024 and 6 of 9 in FY2023 decided
    on EPOP/ACS evidence with no rate test. A rate-threshold-based revealed-preference measure
    drops this class entirely, and it is concentrated in tribal geographies — the same places
    `qualifying_basis = unknown` concentrates. Treat D-10 and the soft-criterion question as one.
21. **SD FY2016's EPOP groups use `qualifying_basis = own_rate` as a closest-fit only** — EPOP has
    no fixed numeric threshold and the enum has no better value. Flagged by the agent rather than
    asserted.
22. **`data_non_bls_source` fires on 188 rows** because reservation tables cite ACS alongside BLS.
    Per D-22 this is the criterion's own data regime, not a nonconformance — reservations have no
    LAUS series, so ACS is the only construction available. Do not read these as data defects.

### D. What this run adds to existing decisions

23. **D-03** — the requested corpus-wide sweep is complete (18 files, 18 states, all
    `approval-<YYYY>`); mechanical fix applied; options (2) and (3) still open. See the D-03 update.
24. **D-11** — MT FY2017 Prairie County; plus the reservation-adjacency gap.
25. **D-12 / D-16** — SD serial 990047 **denies** Standing Rock in FY2020 and **approves** it in
    FY2021, both with explicit rows. A positive control: unlike D-12's vanishing areas, the
    sequence is fully recoverable.
26. **D-14** — the SD overlap corpus (221 rows) adds a fifth direction to the containment table.
27. **D-25** — MT/SD split 3–1 to populate derived rates; combined with UT the tally is 7 agents,
    5–2. The MT FY2016/FY2017 pair puts the inconsistency *within one serial*.

---

## Agent judgment calls and deviations — MT/SD run (2026-08-15)

Covers the **16 documents re-extracted in this session**. The other 41 predate the interrupt and
have no agent report on file (see the provenance caveat above).

### A. Calls that change row counts

1. **"Aggregate" read as temporal, not spatial — 4 agents, one recurring phrase.** MT FY2021-a,
   FY2023, FY2024 and SD FY2021 all print some form of *"aggregate average unemployment rate 20
   percent above the national average"* — wording that reads as a joint-bundle test. All four
   agents coded **`per_unit`** (splitting into 13, 4, 5 and 9 groups respectively) on the same
   grounds: a rate is printed for every area, every one clears the threshold alone, no combined
   figure or bundle name appears anywhere, and the clause immediately following names the
   24-month window — so "aggregate" describes the *averaging*, not cross-area pooling. SD FY2020's
   agent found the decisive tell: the same letter uses "aggregate average unemployment **rates**"
   (plural, per-area) a sentence later. SD FY2022's agent noted the phrase is also used for a
   *single-county* paragraph, where spatial aggregation is impossible.
   **This is the highest-leverage recurring call in the run** — it sets group counts on 31 groups
   — and all four agents landed the same way with the arithmetic supporting them. Worth a
   one-line rule in `2220b` so it stops being re-litigated per document.
2. **SD FY2020 — Standing Rock held as ONE unit though its rate is built from two counties.**
   The document computes it from "the two counties' aggregate" (Corson + Dewey). Coded as a single
   `per_unit` reservation rather than two county units, on the grounds that the reservation is the
   requested area and county-combination is how any reservation rate must be built. Directly
   relevant to D-14.
3. **SD FY2002 — reservations held at reservation level, not decomposed.** Same call, stated
   explicitly: the document gives one blended rate per reservation and never isolates
   county-level rates within one.
4. **SD FY2002 — Bennett and Marshall each split into reservation portion + explicit remainder**,
   yielding two groups per county. Flagged `possible_double_counting` per the spec's
   balance-of-county guidance even though the sub-areas are complementary and non-overlapping.

### B. Calls that change a coded value

5. **SD FY2025 — `possible_double_counting = true` set for a relation the field does not
   describe.** Three reservations overlap counties approved in the same document; no unit name
   repeats. The agent set the flag deliberately and explained in `double_counting_note` that this
   is territorial overlap, not name duplication, "since the document itself never addresses the
   overlap and it's exactly the kind of double-coverage risk the field exists to surface." The
   judgment is sound; the field is overloaded (→ D-14 update).
6. **MT FY2021-b — `eb_trigger` kept over `federal_suspension` although the waiver window sits
   entirely inside the FFCRA suspension.** The document's own stated basis is DOL Trigger Notice
   2020-16. Coded to the document; tension recorded in `request_level.notes`. SD FY2021 made the
   identical call for the identical reason. Correct per spec, and worth confirming the spec means
   to keep saying so, since it produces `eb_trigger` rows for periods when the time limit was
   federally suspended anyway.
7. **Five agents excluded an FFCRA recital from `groups[]`** (MT FY2021-a, FY2023; SD FY2021,
   FY2022, FY2023) under the "a recital is not a group" rule. Consistent across the run.
8. **MT FY2023/FY2024/FY2025, SD FY2020–FY2025 — `data_non_bls_source = true` on every
   reservation group** because tables cite ACS alongside BLS. Applied consistently; see checklist
   item 22 for why these should not be read as defects.
9. **SD FY2016 — `qualifying_basis = own_rate` for the two EPOP groups as closest enum fit**,
   with the imprecision flagged rather than concealed.
10. **SD FY2024/FY2023 — `nonstandard_averaging = true` on the soft-criterion groups** because
    ACS 5-year estimates replace the standard 24-month BLS window. Defensible, but note this makes
    the flag fire on the criterion's *normal* data regime, which is the D-22 question.
11. **MT `approval-2018`, FY2016, SD FY2016 populated derived per-county rates; MT FY2017 did
    not** (→ D-25).

### C. Calls on dates and officials

12. **SD FY2002 — 2003 chosen over 2002 for expiry** on a two-against-one document reading
    (checklist item 5).
13. **SD FY2023 — revised request date (Sept 22, 2022) used over the initial (Aug 19, 2022)**,
    the revision having merged "Northern Cheyenne River Reservation" into "Cheyenne River" and
    added Lake Traverse. Both recorded in `notes`.
14. **MT FY2017 — cover letter dated Dec 5, 2016 vs field 14 stamped Dec 6, 2016.** Both recorded
    as printed.
15. **Officials fields drifted between agents.** MT FY2024, FY2025 and SD FY2022 used the form's
    dedicated numbered *contact* fields; MT FY2023 and SD FY2016 used the letter's *signatory*
    because only the signatory carried a title. MT FY2024 and SD FY2024 both hit DocuSign
    "signed by X **for** Y" blocks and recorded the title-holder, noting the proxy. Low stakes,
    but it is an unruled convention — the same document class yields different `fns_official_name`
    depending on which agent read it.

### D. Protocol deviations and tooling notes

16. **One document was re-extracted from scratch rather than repaired.** `mt-abawd-response-fy2017`
    existed as invalid JSON from the interrupted session. It was **deleted before dispatch** so the
    replacement agent could not read its own prior answer, and the agent was told only that a prior
    attempt had produced broken JSON and to verify its output parses. It did. Hand-patching was
    rejected because the break was a nesting error that could equally have indicated a truncated
    `groups` array — a repair would have silently preserved whatever was lost.
17. **`fna_extraction_results.py` was edited mid-run** to fix the `fiscal_year` parse (D-03). It
    does not hash into `run_id`, so the arm is unaffected; `collate` and the flattener were re-run
    afterwards and the flat CSV regenerated. Verified: 0 null `fiscal_year` corpus-wide, all
    pre-existing filename shapes parse unchanged.
18. **Several agents listed the output directory** to confirm their write path and disclosed doing
    so, noting they opened no file. Listing is not reading; no deviation.
19. **No agent read a gold sheet, comparison CSV, ledger, validator, protocol writeup, or another
    extraction JSON, and none searched git history.** All 16 confirmed compliance explicitly. The
    blinding held.
20. **The blinding block was inlined in every dispatch prompt** (rather than referenced from a
    task file), continuing the AL/UT/LA practice.

---

## Verification checklist — MD/MI run (2026-08-16)

Per-document facts to check against the source PDFs. Agents transcribe suspect values faithfully
rather than correcting them, so these are the known-suspect cells in the MD/MI slice. All 46
documents were extracted fresh in one session and all 46 are schema-valid.

### A. Would change extracted values — check first

1. **MD FY2003 — Wicomico printed at exactly the threshold and DENIED.** The document states the
   qualifying threshold as "at least 5.3 percent" and prints Wicomico's own rate as **5.3%**, then
   lists it among the denied counties. The agent kept the document's action and flagged the tension.
   Either the printed rate is rounded from something below 5.3, or the denial is an error. Compare
   against MD FY2008, where **Dorchester at exactly 5.6 vs a 5.6 threshold was APPROVED** — the same
   state, the same rule, opposite treatment of equality. One of the two is wrong and the pair decides
   whether the 20% test is inclusive.
2. **MD FY2003 — Cecil is both approved and denied in one letter.** Denied under the soft
   "insufficient jobs" criteria, approved under FNS's own supplementary 20%-rule check. The agent
   emitted both groups per the splitting rule. Confirm this is what the letter says and not an
   agent reconciliation; it is the load-bearing case for the criterion-track double-counting problem
   (protocol item 4) and for whatever `2224` does with 18 twice-listed MD counties.
3. **MD FY2002 — field 13 expiration predates the letter.** Printed as "February 28, 2002" on a
   letter signed 2002-03-14 responding to a 2002-01-23 request, and before the September 2002 end of
   the cited LSA designation period. Almost certainly meant 2003. Transcribed verbatim.
4. **MD FY2001 — the document contradicts itself on which county has the low E/P ratio.** Page 4–5
   narrative names **Calvert**; Table 5 on page 8 names **Caroline**. Table 2's own printed numbers
   (Calvert .49, Caroline .52) support the narrative. The agent followed the narrative. Two different
   tables are also both labelled "Table 4" in this document.
5. **MD FY2000 — field 8 and field 9 give different county lists for the same soft-criterion claim**
   (16 counties vs 14, differing on Dorchester/Kent/Somerset vs Wicomico). The agent used the field-9
   list, which is what the supporting table actually analyses.
6. **MD FY2006 — page 4 prints Allegany County twice** with identical figures, and field 9 claims
   "four separate jurisdictions" where only three distinct names appear. The agent emitted one
   Allegany unit and did not invent a fourth.
7. **MD FY2006 — serial 2060039 appears once in field 8** where the header, subject line, field 1 and
   field 13 all say **2060034**. Treated as a typo.
8. **MD FY2004 — cover memo says "extension of waiver #790073"** where every form field says
   **970073**. Same transposition appears in MD FY2003. Treated as a typo both times.
9. **MI FY2019 — the request date postdates the response by a year.** Letter dated 2018-11-09 says it
   responds to the State's "October 2, 2019" request, for a waiver period starting 2019-01-01.
   Transcribed verbatim (`date_state_request = 2019-10-02`); almost certainly meant October 2018.
10. **MI FY2023 — cover letter says "two years," the form grants one.** Field 7 and the approved
    period (2023-03-01 to 2024-02-29) are both exactly 12 months.
11. **MI FY2026 — two internal window inconsistencies.** Table 2's header prints "Sept 2024–March
    2025" while its own narrative says September 2024 through August 2025; Table 5's header verbatim
    repeats Table 1's header while its narrative states a Jan–Mar 2025 three-month window. The agent
    used the narrative periods for `local_unemployment_*` and flagged both.
12. **MD FY2020-a — the dateline is duplicated and garbled**: "December 6, 2019 December 5, 2019".
    Coded as 2019-12-06.

### B. Threshold margins (extends the KY/GA, SC/AR, KS/NE/MS, MO and MT/SD tables)

13. Computed from the flat CSV as `local_rate − 1.2 × national_rate` over every `percent_20` group.
    **MI: all six `joint_aggregate` bundles within ±0.06** (FY2017 +0.036, FY2018 −0.040, FY2019
    −0.020, FY2020 −0.020, FY2024 −0.060, FY2025 −0.020), plus both modern statewide computations
    (FY2016 −0.040, FY2023 +0.060). The two pre-2010 statewide ones are off the line (FY2007 −0.400,
    FY2008 +1.140), as are all of MI's per_unit city/reservation grants (+0.38 to +34.18) — so the
    hugging tracks the constructed-bundle era, not the state. **MD is dispersed** (−0.06 to +0.62)
    with four groups hugging: FY2016 +0.000, FY2018 −0.040 twice, FY2023 −0.020, FY2024 −0.060. This is a stronger form of the regularity than
    the "members below threshold" version recorded for the thirteen earlier states — see protocol
    item 1. Worth re-running over the whole arm before it is written up as a result.
14. **MI's excluded counties are the tell.** FY2020's 77-county bundle excludes exactly Allegan, Kent,
    Livingston, Oakland, Ottawa and Washtenaw; FY2024 excludes only Oakland; FY2018/FY2019 exclude 14.
    Verify these lists against the PDFs — the exclusion set is the choice variable, and it is derived
    by set-difference against the geo reference, not printed in the documents.

### C. Internal counts, labels and geography

15. **MD FY2002 — field 8 says "21 counties and one city"**; 20 counties + 1 city are actually named.
    No 21st was invented.
16. **MD FY1998-a and FY1998-b are the same modification** (Kent County added to waiver 970073) seen
    twice: a Waiver Response form and its transmittal memo. Both emit 1 group / 1 unit. Confirm they
    are two documents and not a duplicate scrape; if they are one event, `2224` will count Kent twice.
17. **MD FY1998-a/b — FNS granted a longer expiry than the state applied for** (1998-12-31 vs the
    requested 1998-09-30), stated explicitly as staggering. Not an error; check it is not read as one.
18. **"Worchester" for Worcester** appears in MD FY2004, FY2007 and FY2001; **"Allegheny" for
    Allegany** in MD FY1999; **"Garret"** in MD FY2000; **"Chiooewa"/"Momoe"** for Chippewa/Monroe in
    MI approval-2018. All corrected in `name`, verbatim kept in `orig_text`, per the reference rule.
19. **Baltimore city vs Baltimore County.** Agents split on the `name` convention — "Baltimore",
    "Baltimore city" and "Baltimore County" all appear across documents, with `area_type` carrying the
    distinction. `2224` must not join on `name` alone for MD. MD FY2001's "Baltimore (less Baltimore
    City)" was coded as plain Baltimore County with `balance_of_county = false`, on the reasoning that
    an independent city was never part of the county — check that reading.
20. **MI FY2017-a names no areas at all.** The letter modifies only the duration of a prior grant and
    cross-references "the same 79 areas" in a document not in the corpus. Emitted as 1 group with an
    empty `geographic_units` array. It is the only document in the pair with a group and no units.
21. **MI reservation contiguity is unperformable.** `mi_geo_context.md` maps no reservation to a
    parent county, so the check `2220b` mandates cannot be run on the 18 FY2025/FY2026 reservation
    rows. Same gap as MT/SD. Non-decision item; it is a geo-context build gap, not an extraction one.

### D. What this run adds to existing decisions

22. **D-11** gains four MD instances of a bundle the adjacency lists refute: Baltimore city + Harford
    in FY2017, FY2018, FY2019 and FY2020, plus FY2024's Eastern Shore four (Kent adjacent to none of
    the others) and FY2016-a's seven-county set (Kent sits between Cecil and the rest, and is not a
    member). All kept as drawn, all flagged. MD is now the state where a contiguity-based check fails
    most often.
23. **D-14** gains its missing positive control. MI FY2024 approves 82 counties (all but Oakland) as
    one bundle and Oak Park city — inside Oakland — separately; FY2025 repeats the pattern for three
    cities, excluding each parent county. This is the containment relation handled *correctly*, in
    contrast to SD's silent double-coverage. Whatever rule `2224` adopts for SD must leave MI's counts
    untouched.
24. **New, no D-nn yet — criterion-track double counting.** All 42 `possible_double_counting` rows in
    the run are MD, all from FY2003, all the same shape: one county adjudicated under two different
    criteria in one letter, per the splitting rule, sometimes with opposite outcomes (item 2). Not the
    schema's core case and not D-14's. If it recurs in another state it should become a D-nn.
25. **New, no D-nn yet — mislabelled request-only documents.** MD and MI FY2011/FY2012/FY2013 — the
    whole `FY2010-2014` batch for this pair — are `state_request_only` despite `*-response-*`
    filenames. Three carry no criterion, three no serial. Check the download/pairing layer: the FNS
    response for these six state-years may simply be absent from the archive.

## Agent judgment calls and deviations — MD/MI run (2026-08-16)

### A. Calls that change row counts

1. **MD FY2003's 18 twice-listed counties → 42 rows, not 24.** The agent applied the splitting rule
   literally (one group per rule/action combination) and emitted a separate group for each county's
   soft-criterion denial and its 20%-rule evaluation. A reader expecting one row per county per
   document will find 42 where 24 places exist. See checklist item 24.
2. **MD FY1999 — Dorchester gets no group under serial 980052.** The document itself says Dorchester
   "will be moved to Waiver #970073," so the agent emitted it once, under the LSA group, rather than
   as a denial or a withdrawal. The document prevented the double count, not the spec.
3. **MD FY1998-a/b — the five other areas already covered by waiver 970073 got no rows.** Both agents
   read field 8/13's reference to Allegany, Cecil, Worcester, Annapolis and Baltimore City as
   background rather than as re-adjudication, by analogy to the "recital is not a group" rule, and
   recorded the reasoning in `request_level.notes`. Both flagged this as their biggest call. An
   alternative reading adds up to 5 LSA rows per document.
4. **MI FY2017-a — 1 group, 0 units** rather than 79 invented county rows or a `non_conforming`
   document. See checklist item 20.
5. **MD FY2013 — 0 groups.** The state's one-page transmittal names no jurisdiction, no criterion and
   no rate; the agent emitted an empty `groups` array with `non_conforming_document = false`, reading
   the QC rule's "unrelated cover page" example as narrower than "on-topic but contentless." Flagged
   by the agent as its most debatable call.
6. **MD FY2006 — Worcester's declined LSA route got no denial group.** The state asked for a 2-year
   LSA waiver for Worcester; FNS declined the LSA basis (not designated that year) and covered
   Worcester instead inside the 20%-rule bundle. The agent recorded one approved row, not an approval
   plus a denial, on the reasoning that the area ends up covered. A criterion-level reading would add
   a `rejected` LSA row.

### B. Calls that change a coded value

7. **`qualifying_basis` for members of a bundle with no printed per-unit rates split three ways
   across agents.** MD FY2019/FY2020-a and MI FY2020-b/FY2024/FY2025 coded `unknown`; MD FY2007 and
   MI FY2019 coded `carried_by_group`; MD/MI documents that print per-county *counts* (approval-2018
   both states, MI FY2017-b, MD FY2016-a/FY2017) derived each unit's rate and split `own_rate` vs
   `carried_by_group` arithmetically. All three are defensible readings of the same schema field and
   the mix is visible in the aggregate (unknown 262, own_rate 178, carried_by_group 170). **This is
   the most consequential convention drift in the run** — it makes `qualifying_basis` non-comparable
   across documents unless `2224` normalises on whether per-unit rates were printed.
8. **Deriving unit rates from printed counts.** Where documents print labor force and unemployment
   counts but no rate, several agents computed the rate and populated `geographic_unit_unemployment_rate`,
   despite the schema field saying "as printed." MI approval-2018 (31 of 69 members below threshold),
   MI FY2017-b (36 of 79), MD FY2016-a and MD FY2017/approval-2018 all did this, and in each case the
   arithmetic is what settled `joint_aggregate`. Useful, but the field now mixes printed and derived
   values with no flag distinguishing them.
9. **MI FY2017-b — Mecosta at 6.8908% against a 6.9% threshold** was coded `carried_by_group` on
   unrounded arithmetic though it displays as 6.9. Consistent with the equality question in
   checklist item 1, decided the other way.
10. **MD FY2016-a — five per_unit soft-criterion groups rather than two bundles.** Allegany/Garrett
    (approved) and Kent/Talbot/Washington (denied) were each split per area because the letter
    discusses "each area's ratio" with no combined figure — unlike the same document's two
    `pct20_above_natl` groups, which have explicit combined tables. Same document, two different
    bundling verdicts, each grounded in the evidence tiers.
11. **MD FY2016-a — Kent/Talbot/Washington coded `denied`, not `withdrawn_by_state`.** FNS's
    suggestion that the state "might consider using 15 percent exemptions" is FNS's own post-denial
    advice, not a state declaration. Correct per the spec's case (a)/(b) distinction.
12. **`eb_trigger` documents and `data_nonconformance`.** MI FY2006-a flagged `non_bls_source`,
    `seasonally_adjusted` and `nonstandard_averaging` all true (the DOL trigger notice is a 3-month
    seasonally-adjusted non-BLS series) with a note that this is the statutory methodology, not a
    defect; MI FY2005-a faced the identical text and left the object null on the same reasoning. Two
    agents, one fact pattern, opposite encodings. `2224` should treat `data_nonconformance` as
    uninformative on `eb_trigger` rows.
13. **`state_request_only` documents and `group_action`.** MD FY2012 coded `approved` (reasoning that
    EB-trigger waivers are self-executing per the rules KB); MD FY2011, MI FY2011/FY2012/FY2013 all
    coded `null` on the same document shape. The null coding is the majority and the more conservative
    reading; MD FY2012's `approved` is an inference the document does not support and should be
    reviewed.
14. **`criterion_code = null` on three state letters.** MI FY2011/FY2012/FY2013 cite only "7 CFR
    273.24" with no rate, no LSA, no trigger. Every agent declined to infer `eb_trigger` despite it
    being the likely real mechanism. Correct under "never invent," but it means these state-years
    carry a waiver with no recoverable basis.

### C. Calls on dates and officials

15. **`waiver_effective_date` left null where only expiry + duration are printed.** MD FY2004, FY2005
    and FY2003 all state "1 year" and an expiry but no start; three agents independently declined to
    back-compute the start, reading the prompt's arithmetic licence as scoped to `qualification_level`.
    Consistent across the run.
16. **`fns_official_name` split between the letter's signer and the form's "FNS Regional Office
    Contact" field.** MD FY2024, MI FY2022-b, FY2024, FY2025 and FY2020-b used the contact field; MD
    FY2019, MI FY2017-b and most older documents used the signer. On the newer 14/15-field form
    template the two are different people (e.g. MD FY2024: signer Catrina Kamau vs contact Christopher
    Nasados). The field is not comparable across form generations.
17. **`expiration_date` (request level) kept as verbatim range text** where the form field restates the
    full effective period rather than a single date — MD FY2016-b, MI FY2016-b, MD FY2020-b, MI
    FY2020-a. The clean date is in the group-level `waiver_expiry_date` in every case.
18. **Conditional expiries preserved rather than nulled.** MD FY2020-b and MI FY2020-a both expire on
    a date "or the date at which the new waiver standards become effective, whichever occurs earlier";
    both agents kept the printed calendar date in `waiver_expiry_date` and moved the condition to
    `waiver_duration_text`. These are the 2019-rule-litigation documents; the truncations in MD
    FY2020-a (12 months requested, 3 granted) and MI FY2020-b (12 requested, 2 granted) are real
    partial approvals driven by that rule change, not by any labor-market fact.

### D. Protocol deviations and tooling notes

19. **Roughly ten agents ran `ls` on the output directory** and self-disclosed it, several treating it
    as a blinding breach because this run's prompt explicitly forbade listing. In every case only
    filenames were seen, no file was opened, and the filenames were other states'. Listing is not
    reading and no extraction decision was affected — but the prompt caused the anxiety by forbidding
    something agents do reflexively before writing. **Fix for the next run: state in the prompt that
    the output directory already exists (the worklist creates it) and that no check is needed.** The
    two re-dispatched prompts carried this wording and neither agent listed.
20. **The 20-agent concurrency cap bounced two dispatches** (`mi-abawd-response-fy2019`,
    `md-abawd-response-fy2021`) out of 46. Both were re-dispatched once slots freed; neither had
    written a file, so no document was extracted twice and no output was overwritten. Batch size
    should be held at ~16 rather than pushed to the cap.
21. **No agent read a gold sheet, comparison CSV, ledger, validator, protocol writeup, or another
    extraction JSON, and none searched git history.** All 46 confirmed compliance explicitly. The
    blinding held.
22. **The blinding block was inlined in every dispatch prompt**, continuing the AL/UT/LA/MT/SD practice.

### E. A document that no worklist could ever select (found by reconciling against the manifest)

23. **`mi-response-abawd-fy2008.pdf` was invisible to the pipeline.** Every other file in the corpus
    is named `<code>-abawd-<class>-...`; this one is `<code>-<class>-abawd-...`, doc class and
    "abawd" transposed. `_state_from_name` in `fna_extraction_results.py` matched on
    `^([a-z]{2,4})-abawd`, so it returned `None`, the row was dropped from `build_worklist`, and **no
    state filter could ever select the document** — `--states MI` included. Nothing warned: the
    worklist simply reported 21 MI documents and looked complete.

    It surfaced only because the run was reconciled against `1020_download_manifest.csv` after
    collating (manifest MI = 22, worklist MI = 21). **Corpus-wide it is 1 file of 1135**, so the blast
    radius is one document — but the failure mode is the same one D-03 keeps re-finding: a filename
    shape the parser did not anticipate, failing silently rather than loudly, discovered by accident.
    This is now the fifth time. D-03's option (3) — a parser that refuses to return `None` quietly,
    or a startup assertion that worklist rows equal manifest rows per state — would have caught both
    this and every earlier instance on the first run. **It is still open and this run is another
    argument for it.**

    Fixed by allowing an optional middle token (`^([a-z]{2,4})-(?:[a-z]+-)?abawd`); the code must
    still resolve against `STATE_CODE_TO_NAME`, so a stray leading token cannot invent a state.
    Verified corpus-wide: worklist rows 1133 → **1134**, unresolved state codes **0**, every
    pre-existing stub unchanged, MI 21 → 22. `fna_extraction_results.py` does not hash into `run_id`,
    so this changed no arm — same as the D-03 fix in the MT/SD run. The recovered document was then
    extracted under the same v1_5 spec and collated into the arm.

    **The same regex was written a second time, independently, in `2226_progress_table.py`** (the
    run-status scan at line ~193 matched `^([a-z]{2,4})-abawd-` against the extraction JSON
    filenames). So even after the worklist was fixed and the document extracted, the progress table
    kept reporting MI as `🔄 — 21/22`, i.e. an incomplete run, because it could not see the JSON it
    had just been handed. Both copies are now fixed and MI reads `✅`. Two independent
    reimplementations of the same brittle parse, in the two places that decide *what to extract* and
    *whether extraction is done*, is the concrete argument for D-03 option (3): this parse should
    exist once, in one function, and refuse to fail silently.

24. **One further manifest/worklist gap is real but not a bug.** `ut-abawd-response-fy1999-a.doc` is a
    Word file, and `build_worklist` globs `*.pdf`/`*.PDF` only. UT therefore shows 22 in the manifest
    and 21 in the worklist. The extractor reads PDFs, so skipping it is correct — but the document is
    a genuine FY1999 UT response that **no arm has ever extracted**, and UT's run is recorded as
    complete. Convert it or record it as knowingly out of scope; do not leave it looking extracted.

---

## Verification checklist — VA/OH run (2026-08-17)

39 documents (VA 20, OH 19), 370 groups, 1,038 unit-rows, 39/39 schema-valid, arm `fe5d1b3c`.
Neither state has a gold sheet. Per-run narrative and the threshold-margin tables are in
`2222_extract_claude_protocol.md` § "VA + OH extraction".

### A. Would change an extracted value — check first

1. **OH FY2008 — the 20%-rule claim the arithmetic refutes, at 88 counties.** Printed aggregate
   **5.7** against a printed national **4.8**; the threshold is 5.76, so the aggregate *misses*, and
   **37 of 88 counties** print rates below it (Mercer 3.9, Delaware 4.1, Auglaize 4.5, Warren 4.8).
   FNS approved on "all of the data submitted by the State meets the requirements of approval." The
   extraction records both numbers as printed and flags the tension in `qualification_level_evidence`.
   Confirm the 5.7 and 4.8 against the source, because this is the largest such case in the corpus and
   the second state (after TN FY2007) where an asserted claim is refuted in the approval direction.
2. **OH FY2007 Sub-Region of Northern EDR — approved 0.1 below its own threshold.** Cuyahoga, Lake,
   Lorain, Geauga print a combined **5.7** against the document's own printed **5.8** threshold, with
   no per-county rates given, and are approved without comment. All four are newly added in this
   modification. Confirm the 5.7/5.8 pair.
3. **OH FY2006 and FY2006-a — are the EDR aggregates computed over the union or the decided subset?**
   Both documents' tables include counties labelled "currently waived" (prior action, not adjudicated
   here). If the printed regional aggregate is computed over the union — which both agents concluded —
   then **every OH FY2006/FY2007 margin in the protocol's table is not comparable to the rest of the
   arm**, because the group's rate is not a function of its members. This is the single highest-value
   check in the run and it is what D-27 turns on.
4. **VA FY2000 Henry County + City of Martinsville.** A `pct10_statutory` group coded
   `joint_aggregate` on a **combined 6-month average of 12.85%**, with no individual rate printed for
   either unit, sourced from a Virginia state website and the Virginia Employment Commission rather
   than BLS. Three departures at once (joint filing of a per-unit rule, 6-month window, non-BLS
   source). Verify the 12.85 and the window; `data_nonconformance` carries
   `nonstandard_averaging = true` and `non_bls_source = true` on this group.
5. **VA FY2005 — no per-county rates anywhere, and the "20% Threshold" column equals the combined
   rate.** The 49-county "Southern Region" prints Total Unemployed 41,829 / Total Labor Force 588,832
   → **7.1%**, against a printed "20% Threshold" of **7.1%**. Because no per-unit rate is printed, all
   49 units carry `qualifying_basis = unknown` and the load-bearing/carried split is unrecoverable
   (D-10, D-25). Confirm whether the document prints a bare national average anywhere; if it does not,
   the group's margin cannot be computed and its exclusion from the margin table is correct.
6. **VA FY2004 Giles County — approved at 6.3 against a 6.36 threshold.** National 5.3, 24-month
   window CY2001–2002. The document asserts the 20%-above relationship without showing the arithmetic
   reconciles; 5.3 × 1.2 = 6.36 > 6.3. Extracted as printed with the near-miss flagged.
7. **VA FY2015-a Richmond County — printed at exactly 8.1 against an 8.1 threshold** while the
   document's narrative says the per-unit jurisdictions qualify on rates "exceeding" it. Extracted as
   printed.
8. **VA FY2006's third group — 19 counties/cities approved with no criterion, no rate and a
   two-month window** (2006-05-01 to 2006-06-30), the stated rationale being administrative (staff
   retraining as areas lose exemption). Coded `criterion_code = null`,
   `qualification_level = unknown`, `group_action = approved`. Second instance of D-19's
   approval-resting-on-no-criterion after the UT bridge extension; confirm no criterion is printed.
9. **VA FY2006 Williamsburg — labor force printed as 113,008** for a city whose population was
   ~12,000. Almost certainly a labor-market-area figure the form prints in a city row. Kept verbatim.
   Also in this document: FNS approves Williamsburg on its 7.6% *rate* although the state requested it
   on an expiring LSA designation, so `criterion_code` is `pct20_above_natl` and not `lsa` — a
   D-16-adjacent requested-vs-dispositive call, made here on an approval.
10. **OH FY2005 field 18 predates the request it answers.** Printed as "Date of regional office
    transmittal of response to national office: May 2, 2005" against a state request of May 12, 2005.
    OH FY2004 has the same field with a label that contradicts the cover letter's account of what the
    date means (the RO forwarding the *request* upward, not the response downward); its agent mapped
    it to `date_ro_transmittal_request` and left `date_ro_transmittal_response` null, while FY2005's
    agent mapped the same field to `date_ro_transmittal_response`. **Two agents, one form, one field,
    opposite mappings** — settle which before `2224` reads either column.
11. **VA FY2004 request date, three values.** Cover memo says the state requested March 29; field 17
    says March 16; field 18 (RO transmittal) says March 29. The extraction follows the form fields.
12. **VA FY2023 data-extraction footnote dated 2022-04-18** on tables whose window ends Nov 2022 and
    which answer an April 2023 request. Stale boilerplate; recorded in notes, no coded field altered.
    Same document's narrative gives the five per-unit localities' average as "5.9 percent" where
    Table 1's own values average 6.0.

### B. Transcription / OCR calls made against the geography reference

13. `Definace` → **Defiance** (OH FY2006-b and OH FY2007, twice on the same serial).
14. `Mahonig` → **Mahoning** (OH FY2006-b).
15. `Perrv` → **Perry** (OH `approval-10.2017-9.2018`).
16. `Ottowa` → **Ottawa** (OH FY2017).
17. `Caroll` → **Carroll**, `Geuaga` → **Geauga** (OH FY2006-a).
18. `Dickinson` → **Dickenson** (VA FY2014). `Mecklenburg Cow1ty` → **Mecklenburg**
    (VA `approval-5.2018-4.2019`, type-word artifact only). VA FY1998 field 8 spells `Allegheny` and
    `Mecklenberg` where field 9 spells them correctly; the extraction sourced units from field 9.
19. **OH FY2016 is the one document where the text layer and the rendered image disagree
    systematically** — the embedded text is badly garbled (`Momoe`, `Adanis`, `CPR` for `CFR`) while
    the page images are clean. The agent transcribed from the images and reported all 18 names
    matching the reference. Worth one spot check, and worth noting for any future text-layer-based
    tooling: this document would defeat a `pdftotext` extractor while reading cleanly as an image.
20. OH FY2007's prose names an added county `Lorian` where the operative page-3 table spells it
    **Lorain**; the extraction used the table.

### C. Contiguity findings

21. **Virginia's "southern Virginia" / "Southern Region" bundle is neither southern nor contiguous,
    in eight documents, flagged by eight independent blinded agents** (FY2006, FY2007, FY2008, FY2014,
    FY2016, FY2017, FY2019, `approval-5.2018-4.2019`). Membership includes the Eastern Shore
    (Accomack, Northampton), the Northern Neck (Lancaster, Northumberland, Richmond County,
    Westmoreland), northwestern mountain counties (Highland, Bath, Alleghany, Craig, Covington City)
    and Hampton Roads (Hampton, Portsmouth, Williamsburg). Williamsburg city and Franklin city are
    outright exclaves in several years. All eight kept the set as drawn. Largest D-11 instance in the
    corpus and, like TN's Sub-Area 4, a stable multi-year defect rather than a one-document error.
22. **VA FY2017's two-county "Shenandoah Valley … same economic region"** bundle is Bath + Page, which
    share no border (Bath: Alleghany/Augusta/Highland/Rockbridge; Page: Greene/Madison/Rappahannock/
    Rockingham/Shenandoah/Warren). A clean small counter-example to the state's own claim.
23. **OH FY2006's Northwest, Southern and Southeast EDR decided-subsets are non-contiguous as
    emitted and contiguous once the excluded already-waived counties are restored** — a D-11 violation
    manufactured by the exclusion rule, not present in the document. See D-27.
24. **OH FY2006-a's two denied joint groups are not contiguous either**, and the document itself
    grouped them: Franklin/Hamilton/Montgomery/Summit are four separate metros (Columbus, Cincinnati,
    Dayton, Akron); Cuyahoga/Geauga/Lake/Medina are a genuine Cleveland cluster but Stark is adjacent
    to none of them and sits in a different MSA. Kept as the document grouped them (shared map and
    MSA-study evidence), flagged as lower-confidence.
25. **Confirmed contiguous** (the reference doing its job in the other direction): OH FY2019 and
    FY2020's Hocking/Ross/Vinton "Combined Area" — all three mutually adjacent, matching the
    document's own "3 contiguous counties" claim; VA FY2023's 9-unit Combined Area, connected through
    Dinwiddie; VA FY2024's two bundles; VA FY2015-a's 34-unit chain; OH FY2006-b's nine EDR bundles.

### D. Recurring traps for `2224` specific to this pair

26. **`area_type` is `city` in two VA documents and `independent city` in fifteen** — see **D-26**,
    which sweeps the same split across MD (both values inside one document) and MO.
27. **A *de facto* statewide grant can arrive as an all-county `joint_aggregate`.** OH FY2008 covers
    every one of Ohio's 88 counties under `pct20_above_natl` and is correctly *not*
    `qualification_level = statewide` (the spec reserves that for rules with no area test). Any query
    for statewide coverage that filters on `qualification_level` will miss it. Related: D-21.
28. **Ohio never names a sub-county area.** 477 unit-rows: `county` 472, `statewide` 5,
    `non_standard_geography` true on **zero**. The registry's Tier 3 wart for OH ("71 LAUS cities
    against 88 counties") describes exposure that the corpus never realises. Virginia's wart is real
    but benign — 142 city rows, all independent cities, all standard LAUS county equivalents, again
    zero non-standard geography. Both states were cheaper than their tier implied; the
    LAUS-cities-vs-counties heuristic in `2226a` over-predicted for this pair.
29. **`possible_double_counting` is true on zero rows in both states** — the first pair in the arm
    with none, against TN's 271 of 840. A useful negative control for whatever `2224` does with the
    (five-mechanism, overloaded) flag.
30. **63 OH and 70 VA rows carry `qualifying_basis = unknown`**, concentrated in the documents that
    print no per-unit rates at all (VA FY2005, OH FY2006-b, OH FY2020's Combined Area 1). Preserve,
    do not impute — D-10.

---

## Agent judgment calls and deviations — VA/OH run (2026-08-17)

### A. Calls that change a coded value

31. **`group_action` on a state EB-trigger adoption letter — split within one state's own series.**
    VA FY2011 coded `approved`; VA FY2012 and FY2013 coded `null`. Three near-identical one-page
    Virginia DSS letters, consecutive years, same addressee, same authority. FY2011's agent reasoned
    the EB route is self-executing so the state's statement of intent is the disposition; FY2012's and
    FY2013's reasoned that `2220b` mandates `approved` only for `federal_suspension` and this document
    records no FNS action. All three cite the spec. **Sharpest instance of D-15 in the corpus** — every
    prior one was cross-state or cross-document-class.
32. **`criterion_code` on the same document class — `eb_trigger` in VA, `null` in OH.** VA
    FY2011/12/13 all `eb_trigger`; OH FY2011/12/13 all `null`. Internally consistent in each state and
    opposite across them, on the identical event (a state adopting a nationally-broadcast DOL trigger
    determination). The difference is purely the letter's wording — Virginia's name "extended
    unemployment benefits," Ohio's cite only 7 CFR 273.24 plus a referenced-but-absent FNS memorandum.
    Ohio's three agents each declined to infer the rule from a document they could not read, which is
    correct and leaves three documents with no criterion. Evidence for **D-07**.
33. **The criterion a DENIED group carries, both ways inside one state.** OH FY2006-a codes 11 denied
    counties `other` (the *dispositive* soft evidence: an ARC "distressed" designation, a regional
    economic-indicator report, two maps, an MSA-ranking study); OH FY2023 codes 3 denied counties
    `percent_20` (the *requested* basis). Direct within-state evidence for **D-16**.
34. **`pct10_statutory` coded `joint_aggregate`** (VA FY2000, Henry + Martinsville) against the spec's
    "per_unit by the nature of the rule" default, on the ground that the document computes and cites
    only a combined rate and says Martinsville is "part of the County." The agent documented the
    override in `qualification_level_evidence`. A county/independent-city pair is the natural unit
    here; the spec should say whether the default is rebuttable.
35. **`qualifying_basis` for members of a bundle with no printed per-unit rates — three encodings.**
    OH FY2019's Hocking/Ross/Vinton → `carried_by_group` ("the state's own action was to rely solely
    on the joint figure"); OH FY2020's identical Combined Area 1 → `unknown` ("could be any mix of
    load-bearing and free-riding members"); OH FY2006-b's ten bundles → `unknown`; VA FY2024's two
    Combined Areas → `carried_by_group`. **The same three counties, one serial, adjacent years, coded
    differently.** This is the D-10/D-25 fork arriving in `qualifying_basis` rather than in
    `unemployment_rate`, and it is now within-serial, which is what made D-25 urgent.
36. **Derived per-unit rates: populate or not (D-25) — the split continues.** VA FY2016, FY2017 and
    `approval-5.2018-4.2019` computed per-unit rates from printed counts and **populated**
    `unemployment_rate`; VA FY2008 and FY2015-a computed them, used them to set `qualifying_basis`, and
    **left the field null**, putting the arithmetic in `qualification_level_evidence`. Running total
    across UT, MT, SD and now VA: **12 agents, 8–4 to populate.**
37. **`state_official_name` when the form has both an addressee and a labelled contact.** Roughly ten
    agents chose the letter's addressee; three chose the field-labelled "State agency contact"
    (OH `approval-10.2017-9.2018` → Betsy Suver, OH FY2016 → Betsy Suver, VA FY2016 → Nikole Cox).
    Every one flagged the ambiguity. The schema has one slot and the forms print two people; this is
    a small, purely mechanical drift that a one-line rule in `2220b` would end.

### B. Calls that change row counts

38. **"Currently waived" counties excluded from `geographic_units`** (OH FY2006, FY2006-a) — case (c),
    notes only. This is the D-27 shape; see item 3 above. FY2006's agent verified the exclusion
    against the document's own "26 additional counties."
39. **Pike County (OH FY2005) excluded** — exempt under the prior waiver, dropped from this extension
    because its own rate fell below 10%, and the document observes it would still qualify via LSA
    designation without the state acting on that route. No group emitted; notes only. A clean
    revealed-preference observation with no row (**D-12**).
40. **VA's prior-waiver areas, both encodings, same state.** VA FY2000 emitted **six**
    `withdrawn_by_state` groups (Bath, Highland, Nottoway, Pittsylvania, Washington, Wythe;
    `criterion_code` null) and VA FY2015-a emitted **two** more (Covington City, Lexington City, the
    state having said it was "unlikely to adopt the waiver"). But VA FY1998 dropped
    Allegheny/Alleghany, Page and Covington City with **no group at all**, and VA FY2001/FY2002
    recite whole prior-waiver rosters and areas whose "local officials decided not to seek inclusion"
    as notes only. Same state, same event, both encodings, thirteen years apart (**D-12**).
41. **VA FY2005's 16-into-49 fold.** The state requested 33 counties under the 20% rule and 18 areas
    on LSA grounds; FNS folded 16 of the 18 into the aggregate and decided 2 (Page, Williamsburg)
    separately as LSA. The agent reproduced the arithmetic (33 + 16 = 49; 49 + 2 = 51 = the state's
    stated total) before settling the group structure. Worth recording as the pattern where the
    *requested* criterion and the *granted* criterion differ for a named subset — D-16 on approvals.

### C. Protocol deviations and tooling notes

42. **Six VA agents disclosed listing a directory under `1022_extractions/`; zero OH agents did.**
    In every case the listing came after the extraction judgment was formed and exposed only other
    states' filenames (`al-abawd-response-*`). **The cause was mine, not the prompt language.** I gave
    the five pre-2005 VA agents a batch directory that does not exist (`FY1998-2004`; the corpus uses
    `FY1997-1999` and `FY2000-2004`), so the assigned READ path was wrong and the only way to finish
    the task was to search — the forbidden operation. The blinding block was word-for-word the FL and
    TN one, both of which returned zero disclosures.
43. **Three JSONs were written to a batch directory the worklist never uses** (`FY1998-2004`:
    `va-abawd-response-fy2000`, `-fy2001`, `-fy2004`). Moved to `FY2000-2004`, the stray directory
    removed, and the arm re-collated: 39/39 valid, no document extracted twice, nothing overwritten.
44. **The rule this earns: every path in a fan-out prompt must be copied verbatim from the `worklist`
    output, never reconstructed.** `worklist` prints the exact READ and WRITE paths for each document
    precisely so this cannot happen; the failure here was reading a truncated worklist and inferring
    the remaining batch names. A wrong path does not merely fail — it turns the blinding rule into an
    instruction the agent cannot satisfy, and a conscientious agent will break blinding to finish.
45. **What did work:** the OH batch carried every path copied from `worklist`, the
    `1022_extractions/` no-listing sentence inside the write step, and an explicit "do not verify the
    directory first; just write." 19 of 19 complied silently. Third consecutive run (FL, TN, OH) in
    which that placement produced zero disclosures.
46. **Two agents reported that `2220c` has no `fiscal_year` field** (`va-abawd-approval-5.2018-4.2019`,
    `oh-abawd-approval-10.2017-9.2018` — the two period-named files, i.e. exactly the documents where
    an agent would look for one). FY is derived from the filename by `_fy_from_name`, never extracted.
    One agent considered adding the field and correctly did not, since `additionalProperties: false`
    would have failed it at collate. **Say this in `2220b`**: FY is not the extractor's job. Related:
    the VA approval covers May 2018 – April 2019, so the trailing-year rule assigns 12 months of
    coverage split 5/7 across two federal FYs wholly to FY2019 — defensible, arbitrary, and precisely
    the lossiness **D-04** is about.
47. **No agent read a gold sheet, comparison CSV, ledger, validator, protocol writeup, or another
    extraction JSON, and none searched git history.** All 39 confirmed compliance explicitly.
    The blinding held on content; only the directory-listing rule was breached, and only where my
    prompt made compliance impossible.
