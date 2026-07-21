# ABAWD Time-Limit Waiver Rules — Semantic Knowledge Base

**Purpose.** The canonical, cited reference for *how an area or state qualifies for a waiver of
the SNAP ABAWD time limit* — the qualifying criteria, their legal authority, effective windows,
operational mechanics, and the canonical criterion-code set used to label the project's waiver
panel. This document is the human-readable source of truth; `002_rules_machine.yaml` is its
machine-readable companion (a stub interface for a future programmatic rule-checker).

**Status:** DRAFT for Josh's verification (Phase 1 checkpoint). Do not encode into extraction
prompts until confirmed. Items still needing Josh's adjudication are marked **⟨PENDING JOSH⟩**.

**Sources (triangulated).** This KB is synthesized from three independent passes, all in
`000_sources/`:
- `000a_deep_research_rules_history.md` — **primary-source spine**: every criterion verified
  against statute (govinfo), regulation (7 CFR / 20 CFR), Federal Register rules, and FNS guidance
  PDFs (18 source PDFs downloaded into `000_sources/`). This is the authoritative anchor.
- `000b_paper_rule_definitions.md` — the working paper's (Duggan & Levy, draft 2026-06-03) own
  bracketed-label taxonomy and operationalization. Defines the label convention the panel maps to.
- `000c_cursor_disclosure_recovered.md` — the recovered Cursor-chat disclosure. **Superseded**:
  it conflates LSA with "the 10% rule" and is retained only as provenance. Do not use it to define
  criteria; the paper + primary sources govern.

---

## 1. The two-level structure of the rules

Since **PRWORA (1996)** an area qualifies under **one of two statutory prongs** (7 U.S.C.
2015(o)(4)(A)):

1. **`[10% Rule]`** — the area "has an unemployment rate of over 10 percent." *Statutory,
   self-certifiable.*
2. **`[Insufficient Jobs]`** — the area "does not have a sufficient number of jobs to provide
   employment for the individuals." *An umbrella that FNS operationalizes* into concrete routes:
   **LSA**, **Extended Benefits (EB)**, the state-computed **20%-above-national** test, and a set
   of **softer** criteria (declining employment-to-population, declining occupations/industries,
   academic study).

Two things sit outside this per-area structure:
- **Federal suspensions** (ARRA, FFCRA): the time limit is suspended *nationwide*; no application
  is needed.
- **OBBB 2025**: strikes the `[Insufficient Jobs]` prong entirely. From 2025-07-04, the only
  surviving routes are `[10% Rule]` (48 states + DC) and a new noncontiguous-state (AK/HI)
  "≥1.5× national" test.

`[Insufficient Jobs]` is the statutory *parent*, not itself a code. The canonical codes below are
its operational children plus `[10% Rule]` and the two structural additions.

---

## 2. Canonical criterion codes

Refined from the plan's proposed set. **Two changes** from the plan: (a) `statewide_eb` is
**dropped** as a code — statewide EB coverage is `eb_trigger` at statewide *scope*, captured by a
separate `scope` attribute, not a distinct criterion; (b) `noncontig_1p5x` is **added** for the
post-OBBB AK/HI rule.

| Code | Criterion | Statutory prong | Maps to paper label |
|---|---|---|---|
| `pct10_statutory` | Area unemployment **> 10%** (recent 12-mo avg, recent 3-mo avg, or historical seasonal) | `[10% Rule]` | `[10% Rule]` |
| `pct20_above_natl` | Area **24-mo avg ≥ 20% above** national avg (state-computed, BLS LAUS, **no floor/ceiling**) | `[Insufficient Jobs]` | `[20% Rule]` |
| `lsa` | Area **designated a Labor Surplus Area** by DOL/ETA (20%-above-national core, **6% floor / 10% ceiling**, "civil jurisdictions") | `[Insufficient Jobs]` | `[LSA]` |
| `eb_trigger` | Area/state **qualifies for Extended Benefits** (IUR/TUR trigger "ON"; EUC in-window) → automatic statewide waiver | `[Insufficient Jobs]` | `[EB]` |
| `federal_suspension` | Time limit **suspended nationwide** (no application) | — (overrides all) | federal suspensions |
| `noncontig_1p5x` | Noncontiguous state (**AK/HI**) statewide rate **≥ 1.5× national** | new post-OBBB prong | (post-dates paper) |
| `other` | Softer `[Insufficient Jobs]` evidence: low/declining **emp-to-pop ratio**; **declining occupations/industries**; **academic study**/publication | `[Insufficient Jobs]` | softer criteria |

**Companion attributes** (see `002_rules_machine.yaml`): `scope ∈ {area, statewide}` (marks
statewide-blanket EB / suspension coverage); optionally `statutory_prong` to preserve the
`[10% Rule]` / `[Insufficient Jobs]` roll-up. ⟨PENDING JOSH⟩ Confirm whether the panel should
carry `statutory_prong` as an explicit field or leave it derivable from the code.

**Terminology guard-rail (do not conflate).** Three distinct "numeric-threshold" objects that
outside readers routinely muddle — the recovered Cursor disclosure muddled exactly these:
1. the **statutory ">10%" test** (`pct10_statutory`) — a level test on "areas," self-certifiable;
2. the **DOL LSA designation** (`lsa`) — 20%-above-national core **with a 6% floor and a 10%
   auto-qualify ceiling**, over DOL "civil jurisdictions";
3. FNS's **state-computed "20% above national" 24-month test** (`pct20_above_natl`) — **no floor,
   no ceiling**, over BLS LAUS units.
The LSA formula's internal *10% ceiling* is a **different** 10% from the statutory `[10% Rule]`.
Keep `lsa` and `pct10_statutory` strictly separate.

---

## 3. Effective-timeline table

"Valid window" = dates during which the criterion was a legally available basis for a waiver.

| Code | Valid-date window | Governing authority |
|---|---|---|
| `pct10_statutory` | **1996-08-22 → present** (survives OBBB) | PRWORA §824 → 7 U.S.C. 2015(o)(4)(A)(i); 7 CFR 273.24(f)(1)(i),(f)(2)(i),(f)(3)(i) |
| `pct20_above_natl` | **2001 → 2025-07-04** (standalone criterion) | 7 CFR 273.24(f)(2)(ii),(f)(3)(iii); codified by 2001 final rule (66 FR 4437) |
| `lsa` | **1996 → 2025-07-04** | 7 CFR 273.24(f)(2)(ii),(f)(3)(ii),(f)(4); DOL 20 CFR 654.5 |
| `eb_trigger` | **1996 → 2025-07-04** (2019 rule tried to remove → vacated 2020, restored) | 7 CFR 273.24(f)(2)(ii); Fed-State EUC Act 1970 (P.L. 91-373) |
| `federal_suspension` | **2009-04-01 → 2010-09-30** (ARRA); **2020-04-01 → 2023-06-30** (FFCRA) | ARRA §101(e), P.L. 111-5; FFCRA §2301, P.L. 116-127 |
| `noncontig_1p5x` | **2025-07-04 → present** | OBBB §10102(b), P.L. 119-21 |
| `other` | **1996 → 2025-07-04** | 7 CFR 273.24(f)(2)(ii) |

All `[Insufficient Jobs]`-family codes (`pct20_above_natl`, `lsa`, `eb_trigger`, `other`) share a
single sunset: **OBBB struck the "insufficient jobs" prong on 2025-07-04**; operational wind-down
of pending waivers ran to ~November 2025 per FNS/FNA implementation guidance.

---

## 4. Per-criterion detail

### 4.1 `pct10_statutory` — the statutory ">10%" test
- **Definition.** Area unemployment rate over 10%. Evidence forms (7 CFR 273.24(f)(2)(i)): a
  recent **12-month average** >10%, a recent **3-month average** >10%, or an **historical
  seasonal** rate >10%. It is **not** a single fixed-window statistic.
- **Self-certification.** For a 12-month-average >10% area (or a current-FY LSA area), the state
  may begin operating the waiver **at submission** (f)(4) — the key timing advantage.
- **Recency constraint** (2021 guide): the 12-mo (or 3-mo) average must be recent; e.g., for a
  Jan-1-2018 start the furthest look-back is the 12-month period Feb 2016–Jan 2017.
- **⟨PENDING JOSH⟩ Model-vs-statute nuance.** The paper's *model* (§3.1) recasts `[10% Rule]` as a
  cap inside the 24-month-window machinery: required area rate = **min{1.2·α̃, 0.10}** over a
  permissible window (`V_i^{10%} = 1{unemp ≥ .1 for some w ∈ W}`). That is a modeling choice, not
  the institutional definition (which specifies no fixed window). For *extraction/labeling* the KB
  uses the legal definition; flag documents accordingly. Confirm you want the panel's rule-code to
  reflect the **legal** criterion (not the model's windowed recasting).

### 4.2 `pct20_above_natl` — state-computed "20% above national," 24-month
- **Definition** (7 CFR 273.24(f)(2)(ii),(f)(3)(iii)): area **24-month average** unemployment rate
  **≥ 20% above** the national average over the same 24 months. **No 6% floor, no 10% ceiling** in
  current (reverted-2001) law. State-computed from BLS LAUS (non-seasonally-adjusted); national
  comparison from the BLS national series.
- **⟨PENDING JOSH — correction #1⟩ Origin is 2001, not 2006.** The paper attributes `[20% Rule]`
  to the **Aug-2006** guidance. Primary sources show the freestanding 24-month 20%-above criterion
  (with the ETA-tied window rule) was **codified in the 2001 final rule** (66 FR 4437/4469,
  verified); the 1996 memo had no standalone 20% test (only LSA-embedded). The 2006 guide restated
  it. The KB dates this criterion to **2001**. Please confirm this correction lands in the paper.
- **Window rule.** See §5.2 — this is **correction #2** and the most empirically load-bearing item.

### 4.3 `lsa` — Labor Surplus Area designation (DOL/ETA)
- **Definition** (DOL 20 CFR 654.5): an area is an LSA where the 24-month-average unemployment
  rate is **≥ 120% of the national average** (= "20% above"), **subject to a 6.0% floor** (never
  LSA below 6%) **and a 10% ceiling** (automatic LSA at/above 10%). Reference period (654.4(d)):
  the two calendar years ending Dec 31 of the year before the Oct 1 effective date. Published
  annually (FY basis).
- **Geography.** DOL **"civil jurisdictions"** (cities ≥25k; certain MI/NJ/NY/PA towns; counties;
  "balance of county"; CT/MA/RI towns and PR *municipios*) — a **different universe** from BLS LAUS
  units. A unit can qualify under `lsa` but not `pct20_above_natl`, or vice versa.
- **ABAWD linkage.** LSA designation is enumerated evidence (f)(2)(ii), a "readily approvable"
  basis (f)(3)(ii), and a self-certification basis (f)(4). A **two-year** LSA-based waiver requires
  LSA designation for ≥2 consecutive FYs (2021 guide §IX).

### 4.4 `eb_trigger` — Extended Benefits trigger (DOL/ETA OUI)
- **Definition** (7 CFR 273.24(f)(2)(ii)): the area/state is determined by DOL to qualify for
  extended unemployment benefits. Triggers: **IUR** (13-week insured unemployment rate ≥5% and
  ≥120% of the prior-2-years average; or optional flat ≥6%) or **TUR** (3-month seasonally-adjusted
  total unemployment rate ≥6.5% and ≥110% of either prior 2 years; high tier ≥8.0%). EUC08
  eligibility (2008–2013) served as a qualifying basis in-window.
- **Statewide & automatic.** Per FNS statewide-EB guidance (Jan 2009), a state listed "ON" EB gets
  an automatic **statewide** ABAWD waiver (≤12 months), regardless of whether the state elected to
  offer EB and regardless of the qualifying route. → In the panel this is `eb_trigger` with
  `scope = statewide`; in the paper's model it is a **bypass** (no allocation problem).
- **Underlying data:** DOL ETA **Trigger Notice** archive (built on the weekly **ETA-539** report);
  note the FNS guides cite the Trigger Notice, not "ETA-539" by name.

### 4.5 `federal_suspension` — nationwide suspensions
- **ARRA §101(e)** (P.L. 111-5): **Apr 1 2009 → Sep 30 2010**; post-9/30/2010 pre-count months were
  disregarded.
- **FFCRA §2301** (P.L. 116-127): **Apr 1 2020 → Jun 30 2023** (PHE-tied; COVID PHE ended May 11
  2023 → suspension ended Jun 30 2023). ✅ The paper's Jun-30-2023 date is **confirmed**.
  - **Correction to the plan's brief:** CAA-2023 (P.L. 117-328) ended SNAP *Emergency Allotments*
    (FFCRA §2302) after Feb 2023 — a **different** provision. Do not cite CAA-2023 as the end of the
    ABAWD suspension.

### 4.6 `noncontig_1p5x` — post-OBBB noncontiguous-state test
- **Definition** (OBBB §10102(b), P.L. 119-21, eff. **Jul 4 2025**): strikes old (o)(4)(A)(ii) and
  inserts a waiver for an area "in a noncontiguous State" (defined as not one of the 48 contiguous
  states or DC; excludes Guam/USVI) with an unemployment rate **≥ 1.5× the national rate** →
  effectively **Alaska and Hawaii**. Age ceiling also raised to 64 (over-65 exempt);
  dependent-child exemption tightened to under-14.

### 4.7 `other` — softer `[Insufficient Jobs]` evidence
- Low/declining **employment-to-population ratio** (2021 guide: ETP ≥1 pp below national and
  declining over ≥4-year window, plus a 24-mo rate ≥10% above national); **declining occupations/
  industries**; **academic study or other publication**. Rarely the sole basis for approval
  (paper flags this "TO DO: confirm count").

---

## 5. Operationalization

### 5.1 Data & geography
- Waiver data must rely on **standard BLS data or methods** (f)(2). In practice: **BLS LAUS**,
  **not seasonally adjusted** (2021 guide §IV, verified), at LAUS units (states, counties, cities
  ≥25k, New England towns, select metro/labor-market areas). National rate for the 20% test from
  the BLS national ("LN") series. The paper uses **county-month** unadjusted data, "county" =
  county-equivalent (CT planning regions, AK boroughs, LA parishes, independent cities).
- **Data-vintage caveat** (paper §2.1): the authors hold only **post-Jan-2011** LAUS vintages
  (BLS did not archive earlier vintages), which drives their main-sample restriction and the
  anomalous 2023 ND result. (Vintage ingestion is out of scope for this KB per the plan.)

### 5.2 ⟨PENDING JOSH — correction #2⟩ The 24-month window-selection rule (load-bearing)
This defines the legal window set `W(t)` at the heart of the paper's optimality analysis, so the
exact rule matters.

- **Primary-source rule (verified verbatim** from the FNS 2016 & 2021 guides + 7 CFR
  273.24(f)(2)(ii)): the qualifying 24-month window "**can begin no earlier than the period the
  Department of Labor uses to calculate LSAs for the Federal fiscal year in which the waiver is
  implemented.**" The guides give an explicit table:

  | Waiver FY | 24-mo window may begin no earlier than |
  |---|---|
  | 2021 | **01-01-2018** |
  | 2022 | **01-01-2019** |
  | 2023 | **01-01-2020** |
  | 2024 | **01-01-2021** |

  Equivalently: **Jan 1 of the calendar year two years before the calendar year in which the
  waiver-start FY begins** = **Jan 1 of (FY_label − 3)** (FY2021 starts Oct 1 2020 → Jan 1 2018).
  The state may then use any consecutive 24-month window on/after that January.

- **Discrepancy with the paper.** The paper (§4.2) states the window "could begin no earlier than
  the **January of two fiscal years prior to** the fiscal year when the requested waiver would take
  effect." Read literally that yields **Jan 2019** for an FY2021 waiver — **~one year later
  (more restrictive)** than the primary-source **Jan 2018**. The FNS-guide table is verbatim
  primary source. **This changes the legal window menu `W(t)` and therefore the feasible set in
  your optimization.** Please verify against your own reading before I encode it — if the paper's
  phrasing is a loose gloss for the correct Jan-1-(FY−3) rule, the KB and the paper should both say
  Jan-1-(FY−3); if you intend something different, tell me.

### 5.3 Application-timing degree of freedom
By choosing a start date in/before September (current FY) vs. October (next FY), and applying
closer to the start date as newer BLS data post, a state expands its menu of usable 24-month
windows (paper §4.2, items I–II).

### 5.4 Grouping / contiguity / no-double-counting / rounding
- **Grouping.** 1996 guidance gave "broad discretion in defining areas" and allowed **combining**
  units; **2016** guidance clarified groups must be **geographically contiguous or part of an
  "economic region."** A group can qualify even if not every constituent unit qualifies
  individually — the core combinatorial lever in the paper.
- **No double-counting** (2006 guidance): no geographic unit may appear in more than one waived
  group within an application; groups within an application are disjoint.
- **Aggregation/rounding** (2006 guidance): a standardized procedure exists but the exact rule is
  **not** reproduced in the paper and the **Aug-2006 memo was not located** in research — retrieve
  it if the rounding convention becomes load-bearing. ⟨PENDING JOSH — do you have the 2006 memo?⟩
- **Self-certification** (f)(4): >10% 12-mo-avg or current-FY-LSA areas may operate at submission.
- **Duration** (f)(5): generally one year; seasonal (3-mo) and 2-year variants exist with support.

---

## 6. Regulatory history (for citation)
- **1996** — PRWORA §824 creates the ABAWD 3-in-36 time limit and the two-prong waiver authority;
  first FNS guidance (Dec 3 1996): LSA, EB, >10%, softer criteria; **no standalone 20% test**.
- **2001** — Final rule (66 FR 4437) codifies **7 CFR 273.24(f)**, including the freestanding
  **20%-above-national** criterion and the ETA-tied window rule.
- **2006** — FNS guidance restates the 20% test; mandates non-seasonally-adjusted BLS; standardizes
  rounding; bars double-counting; states the window rule.
- **2016** — FNS guide adds contiguity/economic-region clarification and the academic-study
  criterion.
- **2019 → vacated** — Dec-2019 final rule (84 FR 66782) added a 6% floor to the 20% test, dropped
  LSA/EB as automatic bases, restricted grouping. **Vacated** *Bread for the City / D.C. v. USDA*
  (Oct 18 2020); formally rescinded (86 FR 34605, Jun 30 2021) → **§273.24 reverted to 2001 text**
  (the current law).
- **2021** — Sep-2021 FNS guide restates reverted criteria; **currently in force** (pre-OBBB).
- **2024** — FRA-2023 implementation (89 FR 102362) changes age/exemptions, **not** waiver criteria.
- **2025** — **OBBB** (P.L. 119-21, Jul 4 2025) §10102 strikes the `[Insufficient Jobs]` prong;
  only `pct10_statutory` (48+DC) + `noncontig_1p5x` (AK/HI) survive; age ceiling → 64.

## 7. FNS → FNA rename
As of **June 1, 2026**, the Food and Nutrition **Service (FNS)** became the Food and Nutrition
**Administration (FNA)** — a genuine agency rename/reorganization (USDA press release 0062.26,
Apr 30 2026). New domain **fna.usda.gov**; legacy **www.fns.usda.gov** URLs redirect host-for-host.
All rules/events here (1996–2025) were issued under **FNS**; only post-June-2026 materials say FNA.

---

## 8. Open reconciliation points (⟨PENDING JOSH⟩ — decide before prompt-building)
1. **`pct20_above_natl` origin = 2001, not 2006** (§4.2). Primary-source verified. Affects the
   effective-date table.
2. **24-month window rule = Jan 1 of (FY−3)**, ~one year earlier than the paper's "two fiscal years
   prior" gloss (§5.2). Load-bearing for `W(t)`. Verify against your reading.
3. **`[10% Rule]` legal-vs-model definition** (§4.1): KB uses the legal (unspecified-window level)
   test for labeling; the paper's model uses a windowed `min{1.2α̃,0.10}` cap. Confirm.
4. **`statutory_prong` field** (§2): explicit panel field, or derive from code?
5. **Aug-2006 memo** (§5.4): not located in research; do you have a copy for the rounding/
   no-double-count exact text?
6. **Code set sign-off** (§2): confirm `{pct10_statutory, pct20_above_natl, lsa, eb_trigger,
   federal_suspension, noncontig_1p5x, other}` + `scope` flag as canonical (drops `statewide_eb`,
   adds `noncontig_1p5x` vs. the plan).

## 9. Source index
- Narrative provenance: `000_sources/000a_deep_research_rules_history.md` (primary-source spine,
  18 downloaded PDFs listed in its §11), `000b_paper_rule_definitions.md`, `000c_cursor_disclosure_recovered.md`.
- Machine-readable codes/windows/thresholds: `002_rules_machine.yaml`.
- EB trigger context data: `1_data/10_raw/101_dol/10110_eta539_state_eb_triggerlist_panel.csv`.
