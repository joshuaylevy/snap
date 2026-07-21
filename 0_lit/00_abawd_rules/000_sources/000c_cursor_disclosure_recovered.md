# ABAWD Waiver Rules Disclosure — Recovered from Cursor Chat History

**Recovered:** 2026-07-21 by automated search of local Cursor AI chat storage.
**Status:** Recovered successfully. One primary disclosure passage found (verbatim below), plus one derivative artifact (the extraction-prompt file) that restates the same taxonomy in partially-corrected form.

---

## Provenance

| Field | Value |
|---|---|
| Source DB | `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` |
| Table | `cursorDiskKV` |
| Key | `bubbleId:b04fa295-c2d0-4886-a438-e1f8f987f665:0d29e043-5e3b-4b42-8fba-bd39e9c1074f` |
| Bubble type | `1` (user message) |
| Composer (chat) name | **"ABAWD waiver application data extraction"** |
| Composer ID | `b04fa295-c2d0-4886-a438-e1f8f987f665` |
| Chat created | 2026-03-16 16:02:48 (local) |
| Chat last updated | 2026-03-16 16:49:58 (local) |
| This bubble | first user turn of a 70-bubble conversation |
| Workspace | `/Users/joshuaylevy/Documents/Work/USC/snap` (workspaceStorage hash `698945aa40562ae386c9ffb067a2d8f8`) |

The same text is also mirrored in the snap workspace DB
(`workspaceStorage/698945aa…/state.vscdb`, `ItemTable` key `aiService.generations`,
generation UUID `dec06939-6620-47a2-8450-ed933f375759`, timestamp 2026-03-16 16:37:54)
as the `textDescription` of the composer prompt — confirming the same passage.

**Note on authorship:** This "disclosure" is a *user-authored* message written into the
Cursor chat (Josh explaining the ABAWD waiver rules to the model in order to have it
build an extraction prompt). It was never saved as a repo file. It is the passage the
project flagged for recovery.

---

## Recovered disclosure text (VERBATIM)

The rules-defining portion of the message. Quoted exactly as stored (including original
typos such as "Consequetnly", "ot", "eligiblity"):

> I am passing in many .PDFs of applications/responses to applications for "ABAWD waivers" submitted to the USDA. Since 1996, states have instituted "work requirements" for many sections of the population to enroll in SNAP (formerly known as food stamps). However, some "able bodied working adults without dependents" (ABAWDS) (the definition of this group changes over time) may be made exempt from those work requirements if local economic conditions are very poor, the idea being that if jobs are scarce, even a good-faith effort ot work may not get an able bodied working adult to the work-requirement threshold. Consequetnly, states allowed to apply for "waivers" for ABAWDS in geographic areas that, for example, have high unemployment. These requirements are submitted to the USDA FNS which evalutes whether an waiver/exemption can be applied in accordance with the rule/statute.
>
> There are a number of ways a geographic area could be eligible for a waiver (independent of whether the state requests a waiver for that geographic area). these include being designated a "labor surplus area" (LSA) by the Department of Labor (this is also called the "10% rule"); if local unemployment is greater than 120% of the national unemployment rate (sometimes called the "20% rule"); if there is a congressional federal waiver (applies to all parts of the country if such a federal waiver exists -- only ever done by statute); if a state is on a "trigger list" (there has recently been a spike in local unemployment insurance enrollments -- as measured by the department of labor; this is sometimes labelled as the "EUB" rule). From the perspective of a state, the most "restrictive" (only applies in the most dire economic conditions) rule for eligiblity is the 10% rule, followed by the 20% rule, the EUB rule, and finally the federal waiver.
>
> There are some additional complications
> 1) just because a geographic area would be eligible for a waiver does not mean that the state must apply for a waiver for that location (there is some local bureaucratic discretion in application decisions)
> 2) when constructing an application, if multiple rules would make a geographic area eligible, the local bureaucrat can cite only one rule as justification even if it is not the most generous rule
> 3) although the relevant statute constructed the waiver system to allow for waivers due to economic distress in certain "areas" it did not define what an "area" was. This was left to the discretion of the USDA in implementing the statute. The USDA ultimately decided that an "area" could be any geographically contiguous set of counties (AKA "parishes" in Louisiana "planning regions"/"councils of government" in CT, etc.) or an "economic area" (definition unclear) that met the above definitions. As a consequence of this last quirk, bureaucrats can submit an application for an "area" made up of multiple counties that collectively satisfied at least of the definitions of economic distress even if not all of the counties individually satisfied those criteria. State level agencies could construct any number of  disjoint (cannot share a county) geographic areas that satisfy the criteria
> 4) when constructing the "geographic areas" when submitting an application, bureaucrats could cite different sources of BLS data (which can be updated over time; i.e. there are "vintages" of BLS data). Additionally, bureaucrats would have to justify their unemployment statistics for constructed geographic areas using a 24 month moving average but they had some amount of discretion in picking which 24 month they would use)

*(The remainder of the message is a list of fields to extract from each PDF and a request
to draft a GPT prompt — not part of the rules disclosure. Available in the same bubble if
needed.)*

---

## FLAGGED ERRORS AND IMPRECISIONS

### 1. PRIMARY / KNOWN ERROR — LSA conflated with the ">10% unemployment" criterion

> "...being designated a **'labor surplus area' (LSA)** by the Department of Labor **(this is also called the '10% rule')**..."

and, reinforcing it:

> "...the most 'restrictive' ... rule for eligiblity is **the 10% rule**, followed by the 20% rule, the EUB rule, and finally the federal waiver."

**This is the terminology error the project flagged.** The passage treats "Labor Surplus
Area (LSA)" and "the 10% rule" as the *same thing*. They are distinct waiver-qualifying
criteria under 7 CFR 273.24(f):

- The **LSA** criterion qualifies an area that DOL has *designated* a Labor Surplus Area
  (DOL's LSA formula: local unemployment ≥ 20% above the U.S. average over a 2-year
  reference period, subject to a 6.0%–10.0% floor/ceiling band). It is a *designation*, not
  a raw ">10% unemployment" test.
- The **">10% unemployment" criterion** is a separate statutory/regulatory test: a recent
  12-month average unemployment rate over 10%. *This* is what is colloquially called the
  "10% rule."

By writing "LSA ... (this is also called the '10% rule')," the disclosure collapses two
different criteria into one, and then propagates the error into the ranking ("the most
restrictive ... is the 10% rule"), where "10% rule" again stands in for LSA.

### 2. "20% rule" definition is stated as an over-the-national comparison but labeled loosely

> "if local unemployment is greater than 120% of the national unemployment rate (sometimes called the '20% rule')"

The *math* here (local > 120% of national, i.e. 20% above national) is the correct
"20%-above-national" concept. The imprecision is only nominal/definitional: this
"20%-above-national" test is essentially the criterion embedded in the **LSA** designation
formula (DOL uses ≥20%-above-national with the 6–10% band). So the passage's own split —
"LSA = 10% rule" vs. "20% rule = 20% above national" — arguably has the association exactly
backwards: the 20%-above-national logic is the LSA logic, not a separate "20% rule." Treat
this labeling as unreliable and defer to the CFR/statute definitions in the companion
source files.

### 3. "EUB" gloss on the trigger-list criterion is imprecise

> "if a state is on a 'trigger list' (there has recently been a spike in local unemployment insurance enrollments ... this is sometimes labelled as the 'EUB' rule)"

The trigger criterion in 273.24(f) references qualification for **extended unemployment
benefits (EB / EUC-type triggers)** — i.e., an area qualifying for *extended UI benefits*
under a state or federal EB program (IUR/TUR triggers). The disclosure's paraphrase ("a
spike in local unemployment insurance *enrollments*") is a loose, not-quite-right
restatement of the EB-trigger mechanism; "EUB" is the user's own shorthand, not the
statutory term. The underlying triggers are Insured Unemployment Rate (IUR) / Total
Unemployment Rate (TUR) thresholds, not enrollment counts per se.

### 4. Federal waiver characterization

> "if there is a congressional federal waiver (applies to all parts of the country if such a federal waiver exists -- only ever done by statute)"

Reasonable as a high-level gloss, but "only ever done by statute" overstates. Nationwide /
broad waivers have also been effected administratively (e.g., pandemic-era nationwide
ABAWD time-limit suspensions) and via legislation. Flag as imprecise, not clearly wrong.

### 5. Minor: the internal "restrictiveness" ordering rests on the conflation

The ranking "10% rule > 20% rule > EUB > federal waiver" (most to least restrictive)
inherits error #1: its top rank ("10% rule") is really doing duty for LSA, so the ordering
should not be read as authoritative for whether LSA or the true >10%-unemployment test is
the tightest criterion.

---

## Secondary / derivative artifact (same chat)

The extraction-prompt file the model produced in this chat,
`2_scripts/22_extract/221_abawd_waivers/2210b_extraction_prompt.txt`, was also recovered
from the DB (key `ofsContent:344c892e-…:file:///…/2210b_extraction_prompt.txt`). Its
`rule_type` enumeration **partially corrects** the conflation — it lists `percent_10`,
`LSA`, and `percent_20` as *separate* categories:

> Use exactly one of: **"percent_10"** (unemployment above 10% for 12 consecutive months),
> **"percent_20"** (local unemployment 20% higher than national over 24 months),
> **"LSA"** (Labor Surplus Area designation by DOL), **"EUB"** (trigger list / un...),
> "trigger" (same as EUB), "federal_waiver" (congressional/federal waiver), "other".

So the downstream prompt *does* separate LSA from the 10%-unemployment test. **However, the
residual imprecision persists**: elsewhere the prompt still refers to "the **10% rule's** 12
consecutive months," continuing to attach the "10% rule" label to the >10%-unemployment
criterion. (This is arguably the *correct* attachment — the >10% test is the real "10%
rule" — but it coexists in the project with the primary disclosure that instead pins "10%
rule" onto LSA, so the label is used inconsistently across the two artifacts.)

---

## Search coverage (for credibility of the recovery)

- **DBs searched:**
  - Snap workspace DB `workspaceStorage/698945aa…/state.vscdb` — `ItemTable` fully
    enumerated; `cursorDiskKV` empty (0 rows). Values of `aiService.prompts`,
    `aiService.generations`, `composer.composerData`, `interactive.sessions`,
    `history.entries`, `workbench.backgroundComposer.workspacePersistentData` dumped and
    grepped.
  - Global DB `globalStorage/state.vscdb` (694 MB) — tables `ItemTable`,
    `composerHeaders`, `cursorDiskKV`. Ran `value LIKE` scans for `%ABAWD%`,
    `%labor surplus%`, `%10% rule%`; 4,577 ABAWD-bearing rows, 88 `labor surplus` rows.
    Isolated the distinctive disclosure phrasing (`also called the "10% rule"`) to three
    rows, all tracing to the same chat/message (user bubble + its request-context blobs).
- **Search terms used:** ABAWD, LSA, "labor surplus", "10% rule", "10 percent", "20% rule",
  "20% above"/"above national", "120%", EUB, "trigger", "federal waiver", 273.24,
  "time limit", "insufficient jobs", IUR, TUR.
- **Workspace identified** via each `workspaceStorage/<hash>/workspace.json` `folder`
  field; the snap folder maps to hash `698945aa40562ae386c9ffb067a2d8f8`.
- **Read-only:** all access was `sqlite3` `SELECT` only; no Cursor DB was written or copied
  over. Intermediate dumps went to `/Users/joshuaylevy/.claude/jobs/05ae2246/tmp/`.

Only one substantive ABAWD *rules disclosure* passage exists in the history (the user
message above); the many other ABAWD hits are file-context echoes, code diffs, and
pipeline-architecture discussion, none of which enumerate the waiver criteria.
