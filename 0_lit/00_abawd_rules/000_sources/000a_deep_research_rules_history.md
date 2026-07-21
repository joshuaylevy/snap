# ABAWD SNAP Time-Limit **Waiver** Rules — Cited Legal/Regulatory History

**Purpose.** A primary-source knowledge base on the qualifying criteria for waivers of the
SNAP ABAWD (Able-Bodied Adults Without Dependents) time limit — statutory basis, the
implementing regulation, FNS guidance, the DOL cross-references (LSA, EB), federal
suspensions, and the 2025 statutory overhaul — with per-criterion effective windows and a
mapping to canonical criterion codes for the project's dataset.

**Compiled:** 2026-07-21. **Author:** deep-research pass (background agent).
**Verification stance:** every non-obvious claim is checked against at least one PRIMARY
source (statute text on govinfo.gov, regulation text on eCFR/govinfo, DOL notices,
Federal Register rules). Direct quotes are drawn from PDFs downloaded into this folder
(see the download manifest at the end) and read with `pdftotext`, or from the eCFR API
XML (`src_7cfr_part273_ecfr_current.xml`). The Dec-1996, Dec-2016, and Sep-2021 FNS guides were
downloaded in full (Internet Archive `id_` snapshots) and read; the Aug-2006 guide could not be
located (existence/role confirmed via the 2016 guide). Claims not confirmed against primary text
are marked **UNVERIFIED**. The companion file `000b_paper_rule_definitions.md` records how the
project's own working paper (Duggan & Levy, draft 2026-06-03) labels these criteria; where
this KB and the paper diverge, it is flagged in §"Conflicts & open questions."

> **Terminology guard-rail (do not conflate).** There are *three* distinct numeric
> thresholds that outside readers routinely muddle:
> 1. the **statutory ">10% unemployment"** waiver test (FNS/USDA; 7 U.S.C. 2015(o)(4)(A)(i));
> 2. the **DOL Labor Surplus Area** designation (DOL/ETA; "120% of national" = "20% above,"
>    **with a 6% floor and a 10% auto-qualify ceiling**); and
> 3. FNS's own **"20% above the national average" 24-month** waiver criterion (FNS/USDA;
>    **no floor, no ceiling**).
> The LSA formula *contains* a 10% ceiling parameter, which is a *different* "10%" from the
> statutory ">10%" test. Keep `lsa` and `pct10_statutory` strictly separate. See §4, §2, and
> the distinction table in §"Conflicts."

---

## 1. Dated effective-timeline table (criterion × valid window × authority)

Canonical codes are defined in §10. "Valid window" = the dates during which the criterion
was a legally available basis for an area/state waiver.

| Canonical code | Criterion | Valid-date window | Governing authority / citation |
|---|---|---|---|
| `pct10_statutory` | Area unemployment rate **over 10%** | **1996-08-22 → present** (survives OBBB) | PRWORA §824 → FNSA §6(o)(4)(A)(i), **7 U.S.C. 2015(o)(4)(A)(i)**; **7 CFR 273.24(f)(1)(i), (f)(2)(i), (f)(3)(i)** |
| `pct20_above_natl` | Area **24-mo avg ≥20% above national** avg (no floor/ceiling) | **2001 → 2025-07-04** (as standalone criterion; repealed w/ "insufficient jobs" prong; operational wind-down ~Nov 2025) | Codified **7 CFR 273.24(f)(2)(ii),(f)(3)(iii)** by 2001 final rule (66 FR 4437/4469, Jan 17 2001); statutory umbrella §6(o)(4)(A)(ii) |
| `lsa` | Area designated a **Labor Surplus Area** by DOL/ETA | **1996 → 2025-07-04** (repealed w/ "insufficient jobs" prong) | **7 CFR 273.24(f)(2)(ii),(f)(3)(ii),(f)(4)**; DOL **20 CFR 654.5**; annual LSA FR notice (e.g., FY2026 **90 FR 47340**) |
| `eb_trigger` | Area/state **qualifies for Extended Benefits (EB)** (or EUC, in-window) | **1996 → 2025-07-04**; *2019 rule tried to remove it → vacated 2020, restored* | **7 CFR 273.24(f)(2)(ii)**; Fed-State EUC Act of 1970 (P.L. 91-373); FNS statewide-EB waiver guidance (Jan 2009) |
| `federal_suspension` | ABAWD time limit **suspended nationwide** (no application) | **2009-04-01 → 2010-09-30** (ARRA); **2020-04-01 → 2023-06-30** (FFCRA) | ARRA §101(e), **P.L. 111-5**; FFCRA §2301, **P.L. 116-127** |
| `noncontig_1p5x` **(NEW)** | Noncontiguous state (AK/HI) statewide rate **≥1.5× national** | **2025-07-04 → present** | OBBB §10102(b), **P.L. 119-21**, amending §6(o)(4)(A)(ii) |
| `other` | Softer "insufficient jobs" evidence: low/declining **employment-to-population ratio**; lack of jobs in **declining occupations/industries**; **academic study**/publication | **1996 → 2025-07-04** | **7 CFR 273.24(f)(2)(ii)** |

Notes on the table:
- `statewide_eb` from the project's proposed set is **not listed as a separate criterion** —
  EB qualification is inherently state-level and yields an automatic *statewide* waiver, so it
  is the same *criterion* as `eb_trigger` operating at statewide *scope*. See §10 for the
  recommendation to represent statewide-blanket coverage as a scope flag, not a distinct code.
- All "insufficient jobs"-family criteria (`pct20_above_natl`, `lsa`, `eb_trigger`, `other`)
  share a single sunset: **OBBB struck the "insufficient number of jobs" prong on 2025-07-04**,
  leaving only `pct10_statutory` (48 states + DC) and the new `noncontig_1p5x` (AK/HI).

---

## 2. Statutory basis (Topic 1)

### 2.1 PRWORA §824 (1996) — creation of the ABAWD time limit and the waiver authority

**Citation:** Personal Responsibility and Work Opportunity Reconciliation Act of 1996,
**Pub. L. 104-193, §824, 110 Stat. 2323–2325** (Aug. 22, 1996). Enacting text VERIFIED against
`src_prwora_1996_sec824_110stat2323.pdf` (govinfo STATUTE-110 scan, header "PUBLIC LAW
104–193—AUG. 22, 1996"; §824 heading at 110 Stat. 2323).

§824(a) amended §6 of the Food Stamp Act of 1977 (7 U.S.C. 2015) to add **subsection (o)** —
the ABAWD work requirement and the **3-months-of-benefits-in-any-36-month-period** time
limit. Age range as enacted: covered individuals are **18 through 49** (the (o)(3) exception
was "under 18 or over 50 years of age"). VERIFIED (verbatim).

**Waiver authority, as originally enacted in §824 (VERIFIED verbatim):**
> "(4) WAIVER.—(A) IN GENERAL.—On the request of a State agency, the Secretary may waive the
> applicability of paragraph (2) to any group of individuals in the State if the Secretary
> makes a determination that the area in which the individuals reside— **(i) has an
> unemployment rate of over 10 percent; or (ii) does not have a sufficient number of jobs to
> provide employment for the individuals.**"

So the **two disjunctive prongs date to 1996**: "(i) over 10 percent" vs. "(ii) does not have
a sufficient number of jobs." (An earlier §824 draft version added "and with the support of
the chief executive officer of the State" to (A) — see §6(o)(4) current text below.)

### 2.2 Current statutory waiver authority — FNSA §6(o)(4), 7 U.S.C. 2015(o)(4)

**Citation:** Food and Nutrition Act of 2008, §6(o), codified at **7 U.S.C. 2015(o)**. (The
1977 "Food Stamp Act" was renamed the "Food and Nutrition Act of 2008" by the 2008 Farm
Bill; the section number §6(o) and codification 7 U.S.C. 2015(o) are unchanged.) Pre-OBBB
text VERIFIED against `src_7usc_2015_workreq_2024ed.pdf` (govinfo U.S. Code 2024 ed.).

**§6(o)(4) (pre-OBBB text, as it stood 2018–July 2025) — VERIFIED:**
> "(4) WAIVER.—(A) IN GENERAL.—On the request of a State agency and with the support of the
> chief executive officer of the State, the Secretary may waive the applicability of paragraph
> (2) to any group of individuals in the State if the Secretary makes a determination that the
> area in which the individuals reside— **(i) has an unemployment rate of over 10 percent; or
> (ii) does not have a sufficient number of jobs to provide employment for the individuals.**"

**Caveat:** the govinfo U.S. Code editions (2023, 2024) predate OBBB (July 2025) and therefore
still print the pre-OBBB two-prong text. For the current post-OBBB text, the authoritative
online source is the Office of Law Revision Counsel (OLRC):
`https://uscode.house.gov/view.xhtml?req=(title:7+section:2015+edition:prelim)` — house.gov's
amendment notes now list "2025: Pub. L. 119-21, §§10102, 10108" amending subsection (o).
(OLRC text is authoritative but not a govinfo PDF; treat the OLRC amendment attribution as
VERIFIED-via-house.gov, the post-OBBB codified wording per §5 below.)

**Distinct mechanism — §6(o)(6) percentage ("discretionary") exemptions.** Separate from the
geographic (o)(4) *waivers*, §6(o)(6) lets a State exempt a *percentage* of covered
individuals from the time limit. The percentage has moved over time (15% FY1999–2019, 12%
FY2020–2023, 8% FY2024+; 15% figure added by Pub. L. 105-33 §1001 (1997)). This is codified
at **7 CFR 273.24(g)** ("Discretionary exemptions"), not the (f) "Waivers" subsection.
UNVERIFIED at the exact-percentage level against primary text; noted so it is not confused
with area waivers.

---

## 3. The ABAWD regulation — 7 CFR 273.24 (Topic 2)

The waiver criteria live in **7 CFR 273.24(f) "Waivers."** The **currently effective** text is
the **pre-2019 ("2001") language** — the 2019 rule that rewrote it was vacated and formally
rescinded (see §3.3). Current text VERIFIED against `src_7cfr_273-24_cfr2025ed.pdf` (CFR 2025
annual ed., "1-1-25 Edition") and the eCFR API XML.

### 3.1 Current codified waiver text — 7 CFR 273.24(f) (VERIFIED verbatim)

**(f)(1) General.** "On the request of a State agency, FNS may waive the time limit for a
group of individuals in the State if we determine that the area in which the individuals
reside: **(i) Has an unemployment rate of over 10 percent; or (ii) Does not have a sufficient
number of jobs** to provide employment for the individuals."

**(f)(2) Required data.** "The State agency may submit whatever data it deems appropriate…
However, to support waiver requests based on unemployment rates or labor force data, States
must submit data that relies on standard **Bureau of Labor Statistics (BLS) data or methods**.
A non-exhaustive list…follows:"
- **(f)(2)(i) — over-10% evidence:** "a **recent 12 month average** unemployment rate over 10
  percent; a **recent three month average** unemployment rate over 10 percent; or an
  **historical seasonal** unemployment rate over 10 percent."
- **(f)(2)(ii) — lack-of-sufficient-jobs evidence:** an area that "Is designated as a **Labor
  Surplus Area (LSA)** by the Department of Labor's Employment and Training Administration
  (ETA); is determined by the Department of Labor's Unemployment Insurance Service as
  **qualifying for extended unemployment benefits**; has a **low and declining
  employment-to-population ratio**; has a **lack of jobs in declining occupations or
  industries**; is described in an **academic study or other publications** as an area where
  there are lack of jobs; has a **24-month average unemployment rate 20 percent above the
  national average for the same 24-month period. This 24-month period may not be any earlier
  than the same 24-month period the ETA uses to designate LSAs for the current fiscal year.**"

**(f)(3) Waivers that are readily approvable.** FNS will approve where it confirms: "(i)…a
most recent **12 month average unemployment rate over 10 percent**; (ii) Evidence that the
area has been designated a **Labor Surplus Area** by the ETA for the current fiscal year; or
(iii)…a **24 month average unemployment rate that exceeds the national average by 20 percent**
for any 24-month period **no earlier than the same period the ETA uses to designate LSAs for
the current fiscal year.**"

**(f)(4) Effective date of certain waivers.** For an area with a most-recent-12-month rate
over 10% **or** an LSA designation for the current FY, "the State may begin to operate the
waiver at the time the waiver request is submitted" (self-certification).

**(f)(5) Duration.** "In general, waivers will be approved for one year."
**(f)(6) Areas covered.** "States may define areas to be covered by waivers."

**Key operational fact (VERIFIED):** in the current regulation the FNS "20% above national
average" criterion has **NO 6% floor and NO 10% ceiling**. The only "over 10 percent" figure
is the *separate* statutory path in (f)(1)(i)/(f)(2)(i). (The 6% floor was a feature of the
*vacated 2019 rule* — see §3.2 — not current law.)

### 3.2 Rulemaking history of 273.24(f)

CFR credit line (from `src_7cfr_273-24_cfr2025ed.pdf`): amendments at **66 FR 4469 (Jan 17
2001); 67 FR 41618 (Jun 19 2002); 71 FR 33384 (Jun 9 2006); 84 FR 66811 (Dec 5 2019); 84 FR
66811 (Dec 5 2020); 86 FR 410 (Jan 5 2021); 86 FR 34605 (Jun 30 2021)**; plus FRA-2023
age/exemption changes at **89 FR 102362 (Dec 17 2024)** and **89 FR 90569 (Nov 18 2024)**.

**(a) 2001 final rule — codification.** "Food Stamp Program: Personal Responsibility
Provisions of PRWORA," Final Rule, **66 FR 4437, Jan. 17, 2001** (doc 01-1025). VERIFIED
against `src_fns_2001_final_rule_66fr4437.pdf`: the amendatory text adding §273.24
**already contains the full (f) menu** — LSA, extended unemployment benefits, low/declining
employment-to-population ratio, declining occupations/industries, academic study, **and the
"24-month average unemployment rate 20 percent above the national average … no earlier than
the same 24-month period the ETA uses to designate LSAs for the current fiscal year."** ⇒ The
"20% above" criterion and the ETA-tied window rule were in the **codified regulation as of
2001**, not first introduced by the 2006 guidance. (See §"Conflicts" for reconciliation with
the paper's "added 2006" claim.)

**(b) 2019 proposed & final rules.** Proposed: 84 FR 980 (Feb 1 2019), RIN 0584-AE57. Final:
"SNAP: Requirements for Able-Bodied Adults Without Dependents," **84 FR 66782, Dec. 5, 2019**
(doc 2019-26044), effective **April 1, 2020**. VERIFIED against
`src_fns_final_rule_2019-12-05_84fr66782.pdf`. What it changed to waiver criteria:
1. **Added a 6% unemployment floor** to the "20% above national average" standard;
2. **Eliminated LSA** as an automatic/readily-approvable basis (tied to redefining "area");
3. **Eliminated the Extended Benefits / EUC** qualification as a core criterion (and thus
   statewide EB waivers);
4. **Restricted grouping** of sub-state areas (areas generally had to align with Labor Market
   Areas; no carving out low-unemployment sub-areas);
5. Retained the **24-month reference period** for the 20% standard.
(Confidence: the *existence* and thrust of these changes VERIFIED against the FR PDF; treat
sub-item precision as high-confidence.)

**(c) 2019 rule VACATED.** *District of Columbia v. USDA*, No. 20-cv-00119-BAH (D.D.C.), Judge
Beryl A. Howell (the coalition included **Bread for the City**; hence *Bread for the City v.
USDA*). Preliminary injunction March 2020; the court **vacated** the 2019 final rule
**Oct. 18, 2020**. The rule never took full effect. (VERIFIED via the vacatur notice below and
the D.C. OAG opinion PDF `https://oag.dc.gov/sites/default/files/2020-10/SNAP-ABAWD-Opinion.pdf`.)

**(d) Formal rescission / Notice of Vacatur.** "SNAP: Rescission of Requirements for ABAWD:
Notice of Vacatur," **86 FR 34605, June 30, 2021** (doc 2021-14045). VERIFIED against
`src_fns_notice_of_vacatur_2021-06-30_86fr.pdf` (contains "vacated," "Vacatur," and reverts
the CFR text). This removed the 2019 rule and **reverted §273.24 to the pre-2019 language**
quoted in §3.1.

**(e) FRA-2023 amendments (2024).** Fiscal Responsibility Act of 2023 implementation, **89 FR
102362, Dec. 17, 2024** (doc 2024-29072), effective Jan. 16, 2025. VERIFIED download
`src_fns_fra2023_final_rule_2024-12-17_89fr102362.pdf`. Changed **age thresholds/exceptions
and discretionary exemptions** — **NOT the (f) waiver criteria**. (The Dec-2024 credit line's
"removing '50'" edit is the ABAWD age ceiling, later superseded by OBBB's age 65.)

**(f) OBBB 2025** — see §5 (statutory) and §"Conflicts." As of this writing the CFR text still
prints the pre-OBBB two-prong (f) language because the annual edition predates OBBB and any
conforming CFR amendment.

---

## 4. Labor Surplus Area (LSA) designation (Topic 4)

**Regulatory basis:** DOL/ETA, **20 CFR Part 654, Subpart A** (implements E.O. 12073). VERIFIED
against `src_20cfr_654_lsa_cfr2025ed.pdf`.

- **20 CFR 654.4(d) — reference period (VERIFIED):** "the **two year period ending December 31
  of the year prior to the October 1** annual date of eligibility determination."
- **20 CFR 654.5(a) — classification (VERIFIED):** an area is an LSA where the BLS-measured
  average unemployment rate for all civilian workers over the reference period is
  "**(1) 120 percent of the national average** unemployment rate…**or (2) 10 percent or
  higher.** No civil jurisdiction shall be classified as a labor surplus area if the average
  unemployment rate…is **less than 6.0 percent.**"
- **20 CFR 654.7 — publication:** the Assistant Secretary publishes the LSA list **annually**
  (fiscal-year basis).

**Annual methodology (FY2026 example — VERIFIED against `src_dol_lsa_fy2026_90fr47340.pdf`,
90 FR 47340, Oct. 1, 2025):** "A LSA is a civil jurisdiction that has a civilian average annual
unemployment rate during the previous two calendar years of **20 percent or more above** the
average annual civilian unemployment rate for all states during the same **24-month reference
period**… a **'floor unemployment rate' of 6 percent** … Any civil jurisdiction that has a
**'ceiling unemployment rate' of 10 percent or higher** is classified an LSA." The list is
"**effective each October 1 and remains in effect through the following September 30**." FY2026
reference period = **January 2023 through December 2024**; national avg rounded to 3.84%; 20%
above = 4.61%, which is below the 6% floor, so **the operative FY2026 qualifying rate = 6.0%**.

So the four LSA elements are confirmed: **120% / "20% above"** ✓; **6.0% floor** ✓; **10%
ceiling** ✓; **24-month reference period** ✓ (two calendar years ending Dec 31 of the year
before the Oct 1 effective date).

**LSA → ABAWD waiver linkage:** LSA designation is (i) enumerated evidence for the "lack of
sufficient jobs" prong in **273.24(f)(2)(ii)**, (ii) a **"readily approvable"** basis in
**(f)(3)(ii)**, and (iii) a **self-certification** basis in **(f)(4)** (waiver may operate at
submission). VERIFIED. Sub-regulatory FNS guidance additionally conditions a *two-year*
LSA-based waiver on LSA designation "for a minimum of **2 consecutive fiscal years** (the year
of the request and the fiscal year prior to the request)" — VERIFIED against the Sep-2021 guide
(`src_fns_guide_2021-09_waive_timelimit_abawd.pdf`, §IX).

**Maps to code `lsa`.** Distinct from `pct20_above_natl` (see the distinction table in
§"Conflicts"): both rest on "20% above national," but LSA is a **DOL designation over "civil
jurisdictions"** carrying a **6% floor / 10% ceiling**, whereas the FNS 20% criterion is
**state-computed over BLS LAUS units** with **no floor/ceiling**.

---

## 5. Federal suspensions (Topic 6) & OBBB 2025 (Topic 7)

### 5.1 ARRA 2009 (VERIFIED verbatim, `src_arra_2009_publ111-5.pdf`)
**American Recovery and Reinvestment Act of 2009, Pub. L. 111-5, §101(e)** ("TREATMENT OF
JOBLESS WORKERS"; note it sits *inside* the SNAP benefit-increase §101, not a standalone
§101). Enacted Feb. 17, 2009.
> "(e)(1) …Beginning with the first month that begins not less than 25 days after the date of
> enactment…and for each subsequent month **through September 30, 2010**, eligibility…shall not
> be limited under section 6(o)(2)…"
> "(2) …Beginning on October 1, 2010…a State agency shall disregard any period during which an
> individual received benefits…prior to October 1, 2010."

**Window:** **April 1, 2009 → September 30, 2010** (start is the computed "first month ≥25 days
after Feb 17 2009 enactment"). Post-9/30/2010, §101(e)(2) wiped pre-Oct-1-2010 countable
months clean. Maps to `federal_suspension`.

### 5.2 FFCRA 2020 (VERIFIED verbatim, `src_ffcra_2020_publ116-127.pdf`)
**Families First Coronavirus Response Act, Pub. L. 116-127, §2301, 134 Stat. 178** ("SNAP
FLEXIBILITY FOR LOW-INCOME JOBLESS WORKERS"). Enacted Mar. 18, 2020.
> "SEC. 2301. …Beginning with the first month that begins after the enactment…and for each
> subsequent month **through the end of the month subsequent to the month a public health
> emergency declaration by the Secretary of Health and Human Services under section 319 of the
> Public Health Service Act based on an outbreak of** [COVID-19] **is lifted**, eligibility…
> shall not be limited under section 6(o)(2)…"

**Window:** **April 1, 2020 → June 30, 2023.** Start = first month after Mar 18 2020 enactment.
End = "end of the month subsequent to" the month the COVID-19 PHE was lifted; the PHE ended
**May 11, 2023**, so the suspension ended **June 30, 2023**; States resumed counting months
July 1, 2023. Maps to `federal_suspension`.

> **Adversarial correction (important — the project's brief conflated two FFCRA provisions).**
> The **Consolidated Appropriations Act, 2023 (Pub. L. 117-328, Div. HH, Title IV, §503)** set a
> hard end to **SNAP Emergency Allotments** (the *extra* pandemic benefit top-ups authorized by
> **FFCRA §2302**), terminating them after the **February 2023** issuance month. It did **NOT**
> set the end of the **§2301 ABAWD time-limit suspension**, which remained PHE-tied and ended
> **June 30, 2023**. Two distinct provisions, two distinct end dates. Do **not** cite CAA-2023
> as the end of the ABAWD suspension. VERIFIED.

### 5.3 OBBB 2025 (VERIFIED verbatim, `src_obbb_2025_publ119-21_sec10102.pdf`)
**Pub. L. 119-21** (H.R. 1, 119th Cong.), enacted **July 4, 2025** (govinfo PLAW header
"PUBLIC LAW 119–21—JULY 4, 2025"). **§10102 "Modifications to SNAP work requirements for
able-bodied adults."**

**Waiver-criterion change — §10102(b) "STANDARDIZING ENFORCEMENT" (VERIFIED verbatim):**
> "Section 6(o)(4) of the Food and Nutrition Act of 2008 (7 U.S.C. 2015(o)(4)) is amended—
> (1) in subparagraph (A), **by striking clause (ii) and inserting** the following: '(ii) **is
> in a noncontiguous State and has an unemployment rate that is at or above 1.5 times the
> national unemployment rate.**'; and (2) by adding at the end [a] DEFINITION OF NONCONTIGUOUS
> STATE…'noncontiguous State' means a State that is not 1 of the contiguous 48 States or the
> District of Columbia'… [and] does not include Guam or the Virgin Islands…"

**Effect:** OBBB **strikes the old (o)(4)(A)(ii) "does not have a sufficient number of jobs"
basis** and its entire evidentiary menu (LSA, EB, employment-population ratio,
declining-industry, academic study, 20%-above-average) and replaces it with a narrow
**noncontiguous-State test** (effectively **Alaska and Hawaii**) pegged to **1.5× the national
rate**. For the **48 contiguous states + D.C., the ONLY remaining waiver basis is
(o)(4)(A)(i), "an unemployment rate of over 10 percent."** VERIFIED.

**Age change (§10102(a), VERIFIED verbatim):** the (o)(3) exception becomes "**under 18, or
over 65, years of age**" (covered ABAWD range now **18–64**), and the dependent-child
exemption drops to a "dependent child **under 14** years of age" (from under 18). Secondary to
waivers but relevant to which individuals face the time limit.

**Effective date:** §10102 carries **no delayed-effectiveness clause** for the waiver
amendment, so the statutory change was **effective on enactment, July 4, 2025.** USDA then
operationalized it administratively — existing "insufficient-jobs" waivers wound down, with
the new regime (waivers only for >10% areas; AK/HI 1.5×) taking operational effect
**~November 1–2, 2025** per FNS/FNA implementation guidance. (Statute: VERIFIED. Operational
implementation date: VERIFIED-via-FNS-reporting; the FNS OBBB memo page is a JS SPA
unreachable via curl here — see download manifest.)

**Grouping restriction:** OBBB's elimination of the "insufficient jobs" prong removes the
statutory hook for the LSA/EB/20%-based grouping of areas; the *precise* geographic-grouping
mechanics appear in FNS administrative implementation rather than a separate quoted statutory
clause. Treat "banned area grouping" as **VERIFIED at the level of 'insufficient-jobs prong
repealed'** but **UNVERIFIED as a distinct statutory grouping ban** — the surviving
`pct10_statutory` test operates on individual geographic units.

---

## 6. Extended Benefits (EB) trigger mechanics (Topic 5)

**Statutory home:** Federal-State Extended Unemployment Compensation Act of 1970, **Pub. L.
91-373, §§202–203** (TUR trigger added by Pub. L. 102-318 §201, 1992); implementing reg
**20 CFR Part 615**. Trigger thresholds VERIFIED against DOL `oui.doleta.gov` extensions page
(`src_dol_eb_extensions_thresholds.html`):

- **IUR trigger (Insured Unemployment Rate):**
  - *Mandatory "on":* 13-week IUR **≥ 5%** AND **≥ 120%** of the **average** of the same 13-week
    period in **each of the prior 2 years**.
  - *Optional:* 13-week IUR **≥ 6%**, regardless of prior years (flat level, no look-back).
- **TUR trigger (Total Unemployment Rate; optional, added 1992):**
  - *Standard:* seasonally-adjusted **3-month average** TUR **≥ 6.5%** AND **≥ 110%** of the
    same 3-month period in **either** of the prior 2 years → up to **13 weeks** EB.
  - *High-unemployment tier:* 3-month TUR **≥ 8.0%** (and 110% look-back) → **20 weeks** EB.

> **Two corrections to common framing (VERIFIED):** (a) the **TUR** uses a **3-month
> seasonally-adjusted average**, not a "13-week average" ("13-week" applies to the **IUR**);
> (b) the mandatory **IUR** look-back is the **2-year average**, whereas the **TUR** look-back
> is **either** of the prior 2 years.

**ETA-539** ("Unemployment Insurance Weekly Claims and Extended Benefits Trigger Data") is the
weekly DOL/ETA report carrying each state's initial claims, continued weeks, 13-week IUR, and
EB trigger status. Data: `https://oui.doleta.gov/unemploy/DataDownloads.asp#ETA_539`; EB
trigger notices: `https://oui.doleta.gov/unemploy/trigger/`.

**EB → ABAWD waiver (statewide, automatic).** Regulatory hook: **273.24(f)(2)(ii)** ("qualifying
for extended unemployment benefits"). Per FNS statewide-EB waiver guidance (dated **January
2009**, referencing the DOL Trigger Notice of Jan 22 2009): FNS approves a **statewide** ABAWD
waiver if the state is listed on the DOL EB Trigger Notice as **"ON" Extended Benefits**;
this holds **regardless of whether the state elected to offer EB itself**, and **regardless of
the criteria by which the state qualified** (the EUC bridge); duration **up to 12 months**.
(Content VERIFIED via the EB research agent's read of the FNS page's rendered text; the FNS
page repeatedly timed out on direct fetch here — treat the exact memo wording as
VERIFIED-via-secondary-render pending a clean primary read.)

**EUC (Emergency Unemployment Compensation).** EUC08 operated **2008–2013** (Supplemental
Appropriations Act 2008, Pub. L. 110-252, through American Taxpayer Relief Act 2012; ended
after week ending Dec. 28, 2013). During that window EUC eligibility served as a qualifying
basis (per the Jan-2009 guidance's "regardless of the criteria" language). Maps to
`eb_trigger` (with EUC-in-window a subtype).

**2019-rule note:** the 2019 final rule sought to eliminate the EB/EUC basis and statewide EB
waivers; that rule was vacated (2020), restoring the EB basis until OBBB repealed the whole
"insufficient jobs" prong (July 2025).

---

## 7. FNS guidance memos (Topic 3) — lineage

FNS operationalized the statutory "insufficient jobs" prong through four principal guidance
documents. The 1996, 2016, and 2021 PDFs were **retrieved in full** (via Internet Archive
`id_` snapshots — see manifest) and read; the Aug-2006 PDF was not located (its existence,
title, and superseded status are confirmed from the 2016 guide's own text). Each guide is a
successor: 2016 "replaces its predecessor, FNS's August 2006 Guidance on Requesting ABAWD
Waivers"; 2021 "updates and replaces FNS's December 2016 Guide."

| Memo | Date | What it established | Primary-source status |
|---|---|---|---|
| "Guidance for States Seeking Waivers for Food Stamp Limits" | **Dec. 3, 1996** | Auto-waiver for a **12-mo avg > 10%** area; **BLS LAUS** data (3-mo moving avg "preferred"); "insufficient jobs" via **LSA**, **EB**, **low/declining emp-to-pop ratio**, **declining occupations/industries**; broad discretion to **combine** geographic units. **No standalone "20% above national" test and no "academic study" criterion yet** (VERIFIED: the 1996 PDF contains "10 percent," "labor surplus," "extended unemployment," "employment-to-population" — but zero "20 percent" and zero "academic"). | **VERIFIED** (full PDF read) |
| "Guidance on Requesting ABAWD Waivers" | **Aug. 2006** | Predecessor to the 2016 guide; carried substantially the same criteria set (LSA, EB, >10%, 24-mo 20%-above). Exact wording/data-standards **not** retrieved. | Existence/title/role **VERIFIED** (via 2016 guide); content **UNVERIFIED-primary** |
| "SNAP – Guide to Supporting Requests to Waive the Time Limit for ABAWDs" | **Dec. 2, 2016** | Four principal routes: **LSA**, **EB**, **>10%**, **24-mo 20%-above**; plus case-by-case **emp-to-pop ratio**, **declining industries**, and (new) **"description in an academic study or other publication."** Data: BLS/BLS-cooperating-agency; LSA from DOL/ETA; EB from DOL UI Service. States: 21 pp. | **VERIFIED** (full PDF read) |
| "Supporting Requests to Waive the Time Limit for ABAWDs" | **Sep. 2021** | Post-vacatur guide re-stating the reverted criteria (same four routes + case-by-case + a **two-year-waiver** route, §IX). Data-access: "BLS Local Area Unemployment Statistics … at www.bls.gov/lau"; EB via the **DOL Trigger Notice archive** (`oui.doleta.gov/unemploy/claims_arch.asp`). This is the **currently-in-force** guide (pre-OBBB). | **VERIFIED** (full PDF read) |

**Note on "ETA-539":** the guides do **not** cite "ETA-539" by name for EB; they cite the DOL
**Trigger Notice archive** (oui.doleta.gov) and BLS LAUS (bls.gov/lau). ETA-539 is the
underlying weekly data report behind the Trigger Notice, but an explicit "ETA-539" citation in
FNS guidance is **UNVERIFIED**.

### 7.1 FNS → FNA rename (Topic 9) — VERIFIED

**As of June 1, 2026, the Food and Nutrition Service (FNS) became the Food and Nutrition
Administration (FNA).** VERIFIED against `https://www.fna.usda.gov/about/reorganization`: "As of
June 1, 2026 the Food and Nutrition Service (FNS) is now the Food and Nutrition Administration
(FNA)." It is a **genuine agency rename + reorganization** (not just a domain change): "the Food
and Nutrition Service **and the Food, Nutrition, and Consumer Services mission area** are now the
Food and Nutrition Administration," with leadership/staff relocated to regional hubs. Announced
in USDA press release **0062.26 (Apr 30, 2026)**; 30-day congressional notification ended May 30,
2026; effective **June 1, 2026**. New primary domain **fna.usda.gov**; legacy **www.fns.usda.gov
URLs now redirect host-for-host to www.fna.usda.gov**.

**Bearing on this KB:** every rule/event documented here (1996–2025) was issued under **FNS**;
the operative statute (7 U.S.C. 2015(o)) and the pre-2026 regulation/guidance say "FNS" /
"Service." Only post-June-2026 materials use "FNA." (The exact first-live date of the
fna.usda.gov host was not independently pinned; June 1, 2026 is the effective-date anchor.)

---

## 8. Operationalization (data, windows, grouping, rounding)

- **Data source & geography.** Waiver unemployment/labor-force data must rely on **standard
  BLS data or methods** (273.24(f)(2)). In practice: **BLS Local Area Unemployment Statistics
  (LAUS)**, **non-seasonally-adjusted**, at LAUS geographic units (states, counties, cities
  ≥25,000, New England towns, select metro/labor-market areas). The national comparison rate
  for the 20% test comes from the BLS national series. The **"not seasonally adjusted" mandate
  is VERIFIED** (Sep-2021 guide §IV: "Use not seasonally adjusted data. Monthly labor force and
  unemployment data must be used"); the guide also gives explicit rounding directions
  (referenced but not reproduced here).
- **Window legality (Topic 8) — the load-bearing rule (NOW VERIFIED verbatim).** The
  regulation (273.24(f)(2)(ii),(f)(3)(iii)) states the qualifying 24-month period **"may not be
  any earlier than the same 24-month period the ETA uses to designate LSAs for the current
  fiscal year."** FNS's guides state and *operationalize* the same rule verbatim (Sep-2021
  guide §V, p. 7; identical wording in Dec-2016 guide §V, p. 9 — VERIFIED against
  `src_fns_guide_2021-09_waive_timelimit_abawd.pdf`):
  > "The State must provide data from BLS or a BLS cooperating agency showing an area has a
  > 24-month average unemployment rate 20 percent above the national average for a recent
  > 24-month period. **The 24-month period can begin no earlier than the period the Department
  > of Labor uses to calculate LSAs for the Federal fiscal year in which the waiver is
  > implemented.** For example, the 24-month period for the Fiscal Year 2021 LSA list runs from
  > January 1, 2018 through December 31, 2019. Thus, a waiver that would start in Fiscal Year
  > 2021 could be supported with a 24-month period beginning **any time after (but not before)
  > January 1, 2018.**"
  - The guide gives an explicit lookup table (VERIFIED verbatim):

    | Waiver FY | FY LSA list effective | 24-mo window may begin no earlier than |
    |---|---|---|
    | 2021 | 10-1-20 → 9-30-21 | **01-01-2018** |
    | 2022 | 10-1-21 → 9-30-22 | **01-01-2019** |
    | 2023 | 10-1-22 → 9-30-23 | **01-01-2020** |
    | 2024 | 10-1-23 → 9-30-24 | **01-01-2021** |

  - **Exact operational rule:** for a waiver starting in fiscal year **FY**, the 24-month
    unemployment window may begin **no earlier than January 1 of the calendar year two years
    before the calendar year in which FY begins** — equivalently **Jan 1 of (FY_label − 3)**
    (FY2021 begins Oct 1 2020 → Jan 1 2018; FY2026 begins Oct 1 2025 → Jan 1 2023). This mirrors
    the DOL LSA reference period (20 CFR 654.4(d): the two complete calendar years ending Dec 31
    of the year before the Oct 1 effective date). The state may then use **any consecutive
    24-month window** on or after that January.
  - **Reconciliation with the working paper.** The paper phrases the rule as "no earlier than
    the **January of two fiscal years prior to** the fiscal year when the waiver takes effect."
    Taken literally that yields ~one year *too late* (FY2021 ⇒ paper's Jan 2019 vs. correct
    **Jan 2018**); the paper's "two fiscal years prior" is a loose gloss for "Jan 1 of the
    calendar year two years before the FY's start-year." The FNS-guide text + table above is the
    controlling primary source. See §"Conflicts" #2.
  - **Secondary window rules (2021 guide, VERIFIED):** the **employment-to-population** route
    (§ "case-by-case", p. 16) requires ETP data over "at least a 4-year reference period, ending
    no earlier than 2 years prior to the year in which the waiver is effective," ETP "at least 1
    percentage point below the national average" and declining, complemented by a 24-mo rate
    ≥10% above national. The **two-year waiver** route (p. 17) is stricter (e.g., a rate >20%
    above national for a 36-month period "ending no earlier than 3 months prior to the request").
  - **10%-rule recency (2021 guide, VERIFIED):** for a >10% waiver the 12-month (or 3-month)
    average must be recent — e.g., for a Jan 1 2018 start the furthest look-back is the 12-month
    period Feb 2016–Jan 2017 (or the 3-month period Nov 2016–Jan 2017). So `pct10_statutory` has
    a *recency* constraint but not the fixed multi-year window the 20% test uses.
- **Application timing degree of freedom.** By choosing a start date in/before September
  (current FY) vs. October (next FY) and applying closer to the start date as newer BLS data
  post, a state expands the menu of usable 24-month windows. (Paper §4.2; consistent with the
  regulation's per-request structure.)
- **Grouping / contiguity.** 1996 guidance gave states "broad discretion in defining areas"
  and allowed **combining** counties/cities/towns; the **2016** guidance clarified groups must
  be **geographically contiguous or part of an 'economic region.'** (Contiguity/economic-region:
  paper §4.3, **UNVERIFIED-primary**.) The regulation itself (f)(6) only says "States may
  define areas."
- **No double-counting.** Per the 2006 guidance, no geographic unit may appear in more than
  one waived group within an application. (**UNVERIFIED-primary**, paper §4.3.)
- **Aggregation/rounding.** The 2006 guidance is said to give a standardized aggregation/rounding
  procedure; the exact rule is **not** reproduced in the paper and is **UNVERIFIED-primary**
  (retrieve from the 2006 memo). The FY2026 LSA notice illustrates the LSA rounding convention
  (national avg rounded to 3.84%, threshold to 4.61%).
- **Self-certification.** For >10% (12-mo avg) or current-FY LSA areas, a state may operate the
  waiver at submission (273.24(f)(4)). VERIFIED.
- **Duration.** Generally one year (273.24(f)(5)); shorter seasonal (e.g., 3-month) or longer
  durations possible with supporting documentation. VERIFIED.

---

## 9. Conflicts & open questions

1. **"20% Rule" origin: 2001 regulation (RESOLVED).** The working paper attributes the
   `[20% Rule]` to the **Aug 2006** FNS guidance. This is **incorrect**. The **Dec 1996**
   guidance had **no standalone "20% above national" test** — it only referenced DOL's LSA
   methodology (which internally uses 20%-above) (VERIFIED: the 1996 PDF contains no "20
   percent" string). The freestanding, state-computed "24-month average 20 percent above the
   national average" criterion was **formalized in the 2001 final rule** (66 FR 4437/4469),
   which codified it verbatim into §273.24(f) *with* the ETA-tied window rule (VERIFIED in
   `src_fns_2001_final_rule_66fr4437.pdf`; corroborated by the 2019 FR rule's own history: "Prior
   to the final rule in 2001 that established Sec. 273.24(f), the Department introduced the use
   of LSAs for waivers in its December 1996 memorandum"). **Effective window for
   `pct20_above_natl` = 2001** (as a standalone criterion), not 2006. The 2006 guide restated
   it; the "academic study" criterion likewise post-dates 1996 (first seen in the 2016 guide).
2. **Window rule (RESOLVED — see §8).** The controlling rule is verbatim-verified from the FNS
   2016/2021 guides + the regulation: window may begin no earlier than the DOL LSA reference
   period for the waiver's implementation FY = **Jan 1 of (FY_label − 3)** (FY2021 → Jan 1
   2018). The regulation's "current fiscal year" = **the fiscal year in which the waiver is
   implemented** (the guides say so explicitly). The paper's "January of two fiscal years prior"
   is an **imprecise gloss** — off by ~one year. Use the FNS-guide table (§8) as canonical.
3. **`10% Rule` reference period.** The statute/regulation's >10% test lists three evidentiary
   forms (recent 12-mo avg, recent 3-mo avg, historical seasonal) — it is **not** a single fixed
   window, unlike the 20% test's fixed 24-month window. The paper's *model* recasts `[10% Rule]`
   as a 24-month-window cap `min{1.2·α̃, 0.10}`; this is a modeling choice, **not** the
   institutional rule. Keep the empirical operationalization distinct from the legal definition.
4. **`eb_trigger` vs. `statewide_eb` redundancy.** EB qualification is **inherently state-level**
   and yields an **automatic statewide** waiver; there is no separate "area-level EB" criterion
   in practice. Recommend collapsing to a single `eb_trigger` code and representing statewide
   scope with a separate flag (see §10). Flag if the dataset actually distinguishes them.
5. **`10% Rule` "weakly dominated" by `20% Rule`.** The paper conjectures (unverified) that any
   area clearing 10% also clears "20% above national," making `pct10_statutory` usually weakly
   dominated except for its self-certification timing advantage. This **fails when the national
   rate is high** (2009–10, 2020–21): 1.2·α̃ can exceed 10%, so a >10% area need not clear
   "20% above." Empirical frequency unestablished.
6. **LSA "civil jurisdiction" vs. LAUS geography.** `lsa` covers DOL "civil jurisdictions"
   (cities ≥25k, certain towns, counties, balance-of-county, some county-equivalents), a
   **different geography universe** from the BLS LAUS units used for `pct20_above_natl`. A unit
   can qualify under one and not the other. (VERIFIED via 20 CFR 654 + paper fn. 3.)
7. **OBBB grouping ban.** Whether OBBB imposes a *distinct* statutory grouping ban, or grouping
   simply disappears because its "insufficient jobs" hook was repealed, is **UNVERIFIED at the
   statutory-text level** (§5.3).
8. **FNS→FNA rename (Topic 9) — RESOLVED, VERIFIED.** It is a **genuine agency rename and
   reorganization**, not merely a domain change. As of **June 1, 2026**, the **Food and
   Nutrition Service (FNS)** became the **Food and Nutrition Administration (FNA)** (VERIFIED
   against `fna.usda.gov/about/reorganization`: "As of June 1, 2026 the Food and Nutrition
   Service (FNS) is now the Food and Nutrition Administration (FNA)"). Under the USDA
   reorganization, "the Food and Nutrition Service and the Food, Nutrition, and Consumer
   Services mission area are now the Food and Nutrition Administration." Announced via USDA press
   release **0062.26 (Apr 30, 2026)**; 30-day congressional notification ended May 30, 2026;
   effective June 1, 2026. New primary domain **fna.usda.gov**; legacy **www.fns.usda.gov URLs
   now HTTP-redirect host-for-host to www.fna.usda.gov**. **Implication for this KB:** all
   events described here (1996–2025) occurred under the name **FNS**; the operative statute and
   the (pre-2026) regulation/guidance text say "FNS"/"Service." Post-June-2026 the agency is
   "FNA." (Caution: the exact first-live date of the fna.usda.gov host was not independently
   pinned; the June 1 2026 effective date is the anchor.)
9. **Guidance-memo PDFs — RESOLVED (1996/2016/2021 retrieved).** The 1996, 2016, and 2021 guides
   were downloaded in full (Internet Archive `id_` snapshots) and read; their criteria + the
   window rule are VERIFIED-primary. The **Aug-2006** guide was **not located** — its
   criteria/data-standard specifics (e.g., the "non-seasonally-adjusted" mandate, standardized
   rounding, no-double-counting, contiguity) remain **UNVERIFIED-primary** and are attributed to
   the paper's characterization; the 2016/2021 guides confirm the *substance* of these but a
   verbatim 2006 read would close the loop.

---

## 10. Canonical criterion codes — evaluation & refinement

The project proposed: `pct10_statutory`, `pct20_above_natl`, `lsa`, `eb_trigger`,
`federal_suspension`, `statewide_eb`, `other`. Assessment:

| Code | Verdict | Precise definition / threshold | Valid window | Primary citation |
|---|---|---|---|---|
| `pct10_statutory` | **Keep** | Area unemployment **> 10%** (evidence: recent 12-mo avg, recent 3-mo avg, or historical seasonal). Self-certifiable. | 1996-08-22 → present | 7 U.S.C. 2015(o)(4)(A)(i); 7 CFR 273.24(f)(1)(i),(f)(2)(i) |
| `pct20_above_natl` | **Keep** (origin = 2001) | Area **24-mo avg ≥ 20% above** national avg over same 24 mos; **no floor/ceiling**; window may begin no earlier than Jan 1 of (waiver-FY − 3). | 2001 → 2025-07-04 | 7 CFR 273.24(f)(2)(ii),(f)(3)(iii) |
| `lsa` | **Keep** | DOL/ETA **Labor Surplus Area** designation: 24-mo avg ≥ **120% of national** (=20% above), **6% floor**, **10% ceiling**; over DOL "civil jurisdictions." | 1996 → 2025-07-04 | 7 CFR 273.24(f)(2)(ii); 20 CFR 654.5 |
| `eb_trigger` | **Keep** | State/area qualifies for **Extended Benefits** (IUR/TUR trigger "ON") or **EUC** in-window → automatic statewide waiver, ≤12 mo. | 1996 → 2025-07-04 | 7 CFR 273.24(f)(2)(ii); P.L. 91-373 |
| `federal_suspension` | **Keep** | ABAWD time limit **suspended nationwide** (no application). | 2009-04-01→2010-09-30; 2020-04-01→2023-06-30 | ARRA §101(e); FFCRA §2301 |
| `statewide_eb` | **Drop as a criterion** | Not a distinct *criterion* — it is `eb_trigger` at **statewide scope**. Represent as a scope flag (`scope ∈ {area, statewide}`), not a separate code. | (n/a) | see `eb_trigger` |
| `other` | **Keep** | Softer "insufficient jobs" evidence: low/declining **emp-to-pop ratio**; **declining occupations/industries**; **academic study**/publication. | 1996 → 2025-07-04 | 7 CFR 273.24(f)(2)(ii) |
| `noncontig_1p5x` | **ADD** | Noncontiguous state (**AK/HI**) statewide rate **≥ 1.5× national**. | 2025-07-04 → present | OBBB §10102(b); 7 U.S.C. 2015(o)(4)(A)(ii) as amended |

**Recommended canonical set:** `pct10_statutory`, `pct20_above_natl`, `lsa`, `eb_trigger`,
`federal_suspension`, `noncontig_1p5x`, `other` — with a separate **scope** attribute to mark
statewide-blanket EB/suspension coverage. This maps 1:1 onto the working paper's labels:
`[10% Rule]`→`pct10_statutory`, `[20% Rule]`→`pct20_above_natl`, `[LSA]`→`lsa`, `[EB]`→
`eb_trigger`, federal suspensions→`federal_suspension`, softer criteria→`other`, plus the new
`noncontig_1p5x` for the post-OBBB regime. `[Insufficient Jobs]` is the statutory *umbrella*
for `pct20_above_natl`+`lsa`+`eb_trigger`+`other`, not a code.

Notes/flags: no criterion in the rules is left uncaptured by this set. The only ambiguity is
whether the project wants to (a) distinguish EB area-evidence from statewide-blanket EB
(handle via scope flag), and (b) treat the OBBB AK/HI rule as its own code (recommended) or a
variant of `pct10_statutory` (both are "level vs. multiple-of-national" tests but with
different thresholds and geographies).

---

## 11. Download manifest (PDFs in this folder + source URLs)

All downloaded politely with a browser User-Agent and ~2s spacing. All govinfo/DOL URLs
returned HTTP 200 and were content-verified via `pdftotext`.

| Local file | Source URL |
|---|---|
| `src_prwora_1996_sec824_110stat2323.pdf` | `https://www.govinfo.gov/content/pkg/STATUTE-110/pdf/STATUTE-110-Pg2105.pdf` (pp. 219–221 = §824, 110 Stat. 2323–2325) |
| `src_7usc_2015_workreq_2023ed.pdf` | `https://www.govinfo.gov/content/pkg/USCODE-2023-title7/pdf/USCODE-2023-title7-chap51-sec2015.pdf` |
| `src_7usc_2015_workreq_2024ed.pdf` | `https://www.govinfo.gov/content/pkg/USCODE-2024-title7/pdf/USCODE-2024-title7-chap51-sec2015.pdf` |
| `src_7cfr_273-24_cfr2024ed.pdf` | `https://www.govinfo.gov/content/pkg/CFR-2024-title7-vol4/pdf/CFR-2024-title7-vol4-sec273-24.pdf` |
| `src_7cfr_273-24_cfr2025ed.pdf` | `https://www.govinfo.gov/content/pkg/CFR-2025-title7-vol4/pdf/CFR-2025-title7-vol4-sec273-24.pdf` |
| `src_7cfr_part273_ecfr_current.xml` | `https://www.ecfr.gov/api/versioner/v1/full/2025-01-01/title-7.xml?part=273` (eCFR API; §273.24 current text) |
| `src_fns_2001_final_rule_66fr4437.pdf` | `https://www.govinfo.gov/content/pkg/FR-2001-01-17/pdf/01-1025.pdf` (66 FR 4437) |
| `src_fns_final_rule_2019-12-05_84fr66782.pdf` | `https://www.govinfo.gov/content/pkg/FR-2019-12-05/pdf/2019-26044.pdf` (84 FR 66782; vacated) |
| `src_fns_notice_of_vacatur_2021-06-30_86fr.pdf` | `https://www.govinfo.gov/content/pkg/FR-2021-06-30/pdf/2021-14045.pdf` (86 FR 34605) |
| `src_fns_fra2023_final_rule_2024-12-17_89fr102362.pdf` | `https://www.govinfo.gov/content/pkg/FR-2024-12-17/pdf/2024-29072.pdf` (89 FR 102362) |
| `src_20cfr_654_lsa_cfr2025ed.pdf` | `https://www.govinfo.gov/content/pkg/CFR-2025-title20-vol3/pdf/CFR-2025-title20-vol3-part654.pdf` |
| `src_dol_lsa_fy2026_90fr47340.pdf` | `https://www.govinfo.gov/content/pkg/FR-2025-10-01/pdf/2025-19136.pdf` (90 FR 47340; FY2026 LSA list) |
| `src_dol_eb_law_fedstate_euc_act_1970.pdf` | `https://oui.doleta.gov/unemploy/EB_law_for_web.pdf` |
| `src_dol_eb_extensions_thresholds.html` | `https://oui.doleta.gov/unemploy/pdf/extensions.html` (IUR/TUR trigger thresholds) |
| `src_arra_2009_publ111-5.pdf` | `https://www.govinfo.gov/content/pkg/PLAW-111publ5/pdf/PLAW-111publ5.pdf` (§101(e)) |
| `src_ffcra_2020_publ116-127.pdf` | `https://www.govinfo.gov/content/pkg/PLAW-116publ127/pdf/PLAW-116publ127.pdf` (§2301) |
| `src_obbb_2025_publ119-21_sec10102.pdf` | `https://www.govinfo.gov/content/pkg/PLAW-119publ21/pdf/PLAW-119publ21.pdf` (pp. 11–13 = §10102) |
| `src_fns_guidance_1996-12_seeking_waivers.pdf` | `http://web.archive.org/web/20210323083700id_/https://fns-prod.azureedge.net/sites/default/files/media/file/HistoricalPolicyDocument_GuidanceforStatesSeekingWaiversforFoodStampLimits_December1996.pdf` (Dec 3 1996 guidance; canonical live copy 404s) |
| `src_fns_guide_2016-12_waive_timelimit_abawd.pdf` | `http://web.archive.org/web/20180302014920id_/https://fns-prod.azureedge.net/sites/default/files/snap/SNAP-Guide-to-Supporting-Requests-to-Waive-the-Time-Limit-for-ABAWDs.pdf` (Dec 2 2016 guide, 21 pp.) |
| `src_fns_guide_2021-09_waive_timelimit_abawd.pdf` | `http://web.archive.org/web/20230513141226id_/https://fns-prod.azureedge.us/sites/default/files/resource-files/snap-2021-guide-supporting-abawd-time-limit-waiver-requests.pdf` (Sep 2021 guide, 20 pp.; currently-in-force; live canonical at `https://www.usda.gov/sites/default/files/guidance-documents/fns.snap-guide-supporting-requests-waive-time-limit-abawd.pdf`) |

**Sources referenced but NOT downloaded:**
- **Aug-2006 FNS guidance** ("Guidance on Requesting ABAWD Waivers") — PDF not located; existence
  confirmed via the 2016 guide. **Retrieve if 2006-specific wording is load-bearing.**
- 7 CFR 273.24 & 20 CFR 654.5 live text: `https://www.ecfr.gov/...` (eCFR blocks bots; content
  captured via the eCFR API XML above and govinfo CFR PDFs).
- FNS OBBB ABAWD-waivers implementation memo: `https://www.fns.usda.gov/snap/obbb-ABAWD-Waivers-Implementation-Memo` (JS SPA; curl returns shell only; now redirects to fna.usda.gov).
- FNS statewide-EB waiver guidance (Jan 2009): `https://www.fns.usda.gov/snap/abawd/statewide-waivers-unemployment-insurance-extended` (fetch timed out).
- FNS→FNA reorganization notice: `https://www.fna.usda.gov/about/reorganization`; USDA press release 0062.26 (Apr 30 2026).
- FNS statewide-EB waiver guidance: `https://www.fns.usda.gov/snap/abawd/statewide-waivers-unemployment-insurance-extended` (fetch timed out).
- D.C. OAG vacatur opinion: `https://oag.dc.gov/sites/default/files/2020-10/SNAP-ABAWD-Opinion.pdf`.
- Post-OBBB codified 7 U.S.C. 2015(o): `https://uscode.house.gov/view.xhtml?req=(title:7+section:2015+edition:prelim)`.
