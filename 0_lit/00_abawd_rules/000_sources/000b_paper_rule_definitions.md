# ABAWD Waiver Rule Definitions — as stated in the working paper

**Source:** Duggan, Julian and Josh Levy. "Inferring State Technical Capacity and
Preferences from ABAWD Waiver Allocations." Draft dated June 3, 2026.
File: `5_write/weighted_set_packingv2.pdf` (28 pp.).

**Status flag from the paper itself:** the title page is stamped **"PRELIMINARY AND
INCOMPLETE; DO NOT SHARE."** The rule-definition sections (§§1.1–1.4) are carried by
numerous author "TO DO" footnotes flagging figures still to be confirmed. Treat the
*definitions* as the authors' considered statements, but treat the *empirical
assertions about them* (e.g., how often each rule is invoked, how often the 10% Rule
is dominated) as conjectures the authors have not yet verified.

Extracted for the rules knowledge base. Direct quotes are in blockquotes and marked
**[VERBATIM]**; everything else marked **[PARAPHRASE]** is my restatement.

---

## 1. The paper's canonical qualifying criteria

The paper uses a **bracketed-label convention** throughout — e.g. `[10% Rule]`,
`[Insufficient Jobs]`, `[LSA]`, `[EB]`, `[20% Rule]` — to name each distinct route to
qualification. This is a real, consistent convention in the paper, not my invention.
The labels sit at two nested levels:

- **Statutory level (PRWORA 1996):** an area qualifies under **either** `[10% Rule]`
  **or** `[Insufficient Jobs]`.
- **Operationalization level (FNS guidance):** `[Insufficient Jobs]` is made concrete
  by FNS via `[LSA]`, `[EB]`, the later `[20% Rule]` (added 2006), and a set of
  "softer" criteria.

### 1.1 `[10% Rule]` — the statutory >10% unemployment criterion

The paper introduces this as one of the two original PRWORA criteria (p. 2).

> **[VERBATIM]** (p. 2)
> "They added a provision to the bill that permitted state governments to apply for
> exemptions from these requirements for ABAWDs living in areas of their state that
> met either of two criteria:
> **[10% Rule]** Has an unemployment rate of over 10 percent
> **[Insufficient Jobs]** Does not have a sufficient number of jobs to provide
> employment for the individuals."

**[PARAPHRASE]** `[10% Rule]` = the area's unemployment rate exceeds 10 percent. It is
**statutory** (written into PRWORA), as distinct from the FNS-operationalized routes
below. The statutory text as quoted gives **no reference-period, data-source, or
averaging specification** — it is simply "an unemployment rate of over 10 percent."
(Contrast the very precise 24-month-window definition of `[20% Rule]` below. This
imprecision is inherent to the paper's institutional description; see §6 on how the
model later pins it down.)

**Author's note on self-certification and dominance (footnote 1, p. 2):**

> **[VERBATIM]** (fn. 1)
> "TO DO: Check how many applications are approved under this rule rather than the
> insufficient jobs criterion. On the one hand, states can self-certify waivers under
> this rule and begin issuing them at the time the application is submitted, rather
> than waiting until it is approved. So they have timing-based incentives to use this
> criterion. On the other hand, barring these timing issues, at almost all points in
> time, any area that can qualify under this rule may also qualify under the [20%
> Rule] stated below. And invoking the [20% Rule] expands the set of other areas that
> can be waived due to grouping. Therefore, we want to argue that invoking this rule
> is usually weakly dominated for most applications."

**[PARAPHRASE]** Two properties the paper attaches to `[10% Rule]`: (i) it is
**self-certifiable** — a state can begin issuing waivers at application-submission time
rather than waiting for approval; (ii) the paper *conjectures* it is "usually weakly
dominated" by `[20% Rule]`, because anything clearing 10% typically also clears the
20%-above-national threshold, and `[20% Rule]` additionally unlocks grouping benefits.
Both are flagged as unverified ("TO DO").

### 1.2 `[Insufficient Jobs]` — the statutory "not enough jobs" criterion (FNS-operationalized)

**[PARAPHRASE]** The second statutory criterion (verbatim text quoted above). FNS was
charged with operationalizing it. The paper (p. 3):

> **[VERBATIM]** (p. 3)
> "The US Department of Agriculture's Food and Nutrition Services (USDA FNS) was
> charged with operationalizing these criteria, especially [Insufficient Jobs]. Their
> initial guidance was published in 1996, with updates published in 2006, 2016, and
> 2021."

FNS operationalized `[Insufficient Jobs]` through the binary designations `[LSA]` and
`[EB]`, later `[20% Rule]`, plus softer criteria (§§1.3 below).

### 1.3 `[LSA]` — Labor Surplus Area designation (DOL ETA)

From §1.3 (p. 4), the original FNS route:

> **[VERBATIM]** (p. 4)
> "In the original FNS guidance, an area qualifies for a waiver under the Insufficient
> Jobs Criterion if it:
> **[LSA]** Is designated as a Labor Surplus Area (LSA) by the Department of Labor's
> Employment and Training Administration (DOL ETA);
> **[EB]** Is determined by the DOL ETA's Office of Unemployment Insurance (OUI)
> Service as qualifying for extended unemployment benefits;"

> **[VERBATIM]** (p. 4)
> "The ETA gives LSA designations to civil jurisdictions with unemployment rates at
> least 20% higher than the national unemployment rate."

**LSA floor/ceiling overrides (footnote 2, p. 4):**

> **[VERBATIM]** (fn. 2)
> "The designation rule also has ceiling and floor provisions that override the 20%
> rule. No jurisdiction unemployment rates below 6% can be designated LSAs, while
> jurisdictions with unemployment rates above 10% are automatically designated LSAs."

**"Civil jurisdiction" definition (footnote 3, p. 4–5):**

> **[VERBATIM]** (fn. 3)
> "Civil jurisdiction include the following kinds of areas:
> - A city of at least 25,000 population on the basis of the most recently available
>   estimates from the Bureau of the Census; or
> - A town or township in the States of Michigan, New Jersey, New York, or
>   Pennsylvania of 25,000 or more population and which possess powers and functions
>   similar to those of cities; or
> - A county, except those counties which contain any type of civil jurisdictions
>   defined in A or B above; or
> - A "balance of county" consisting of a county less any component cities and
>   townships identified in paragraphs A or B above; or
> - A county equivalent which is a town in the States of Connecticut, Massachusetts,
>   and Rhode Island, or a municipio in the Commonwealth of Puerto Rico."

**[PARAPHRASE]** `[LSA]` is a **DOL-ETA-administered binary designation**, not a
state-computed threshold. Its underlying rule is "≥20% above national unemployment,"
but with a **6% floor** (never LSA below 6% unemployment) and a **10% ceiling**
(automatic LSA above 10% unemployment). It applies to "civil jurisdictions" (a
specific DOL geography list, quoted above), which is a *different* geography universe
from the BLS LAUS units used by `[20% Rule]`.

### 1.4 `[EB]` — Extended Benefits trigger (DOL ETA OUI)

> **[VERBATIM]** (p. 4–5)
> "Similarly, the OUI issues an [EB] trigger for any state that reaches threshold
> levels for its 13-Week Insured Unemployment Rate (IUR) or 3-Month Total Unemployment
> Rate (TUR). The methods used to calculate these figures are nuanced; see
> [Corson and Rangarajan, 1993] for a more detailed discussion. For our purposes, the
> essential point is that FNS effectively chose numerical thresholds and binary DOL
> designations to operationalize the Insufficient Jobs Criterion."

**[PARAPHRASE]** `[EB]` is a **state-level** trigger (based on the state's IUR or TUR),
issued by DOL ETA's OUI. Critically, in the paper's model a state-year that qualifies
under `[EB]` gets an **automatic, year-long, statewide** waiver (see §3 below,
"degrees of freedom" item a), so it bypasses the whole allocation problem.

### 1.5 The "softer" criteria

> **[VERBATIM]** (p. 5)
> "FNS also included a handful of softer criteria. They indicated that waivers may be
> available to areas experiencing a "lack of jobs due to lagging job growth" or a
> "lack of jobs in declining occupations or industries." These criteria were softer in
> the sense that they were not accompanied by necessary or sufficient quantitative
> thresholds and administrative categorizations. Later versions of the guidance
> substantially reduced the discussion of these softer criteria, and in practice, few
> waivers were ever approved on their basis alone."

**[PARAPHRASE]** Two named soft criteria — "lagging job growth" and "declining
occupations or industries" — with no quantitative thresholds; de-emphasized over time;
rarely if ever the sole basis for approval (flagged "TO DO" to confirm the count).

### 1.6 `[20% Rule]` — the 24-month-average criterion (added 2006)

> **[VERBATIM]** (p. 6)
> "In 2006, the guidance included a third sufficient criteria:
> **[20% Rule]** Has a 24-month average unemployment rate 20% above the national
> unemployment rate for the same 24-month period."

> **[VERBATIM]** (p. 6)
> "This new criteria amounted to an extension of the LSA designation criterion to the
> geographic units found in the BLS LAUS dataset, especially counties that contain
> cities."

**[PARAPHRASE]** `[20% Rule]` = an area's **24-month average** unemployment rate is
≥20% above the national rate over the **same 24-month period**. The paper is explicit
that this is an **extension of the LSA idea to BLS LAUS geographies** (self-computed by
the state from BLS series), which is *why* it is a distinct label from `[LSA]` even
though both rest on a "20% above national" threshold. See the terminology table (§2).

---

## 2. The critical terminology distinction (confirmation from the paper)

The project flagged that the paper reserves `[10% Rule]` for the **statutory >10%
unemployment** criterion and treats **LSA as a separate criterion**, whereas an
external source conflated them. **The paper confirms this distinction.** There are, in
fact, *three* distinct numeric thresholds in the paper that an outside reader could
easily muddle:

| Label | What it is | Who administers / computes | The number(s) | Geography universe |
|---|---|---|---|---|
| **`[10% Rule]`** | **Statutory** PRWORA criterion; self-certifiable | State self-certifies; statutory | Area unemployment **> 10%** (level; no window/data source specified in statute) | "areas" (unspecified in statute) |
| **`[Insufficient Jobs]`** | Statutory "not enough jobs" criterion; umbrella for the FNS routes below | FNS operationalizes | (qualitative) | — |
| **`[LSA]`** | DOL binary **designation** under `[Insufficient Jobs]` | **DOL ETA** designates | ≥ **20% above national**, with **6% floor** and **10% auto-designation ceiling** | DOL "civil jurisdictions" (cities ≥25k, certain towns, counties, balance-of-county, some county-equivalents) |
| **`[EB]`** | Extended-benefits trigger; grants automatic statewide year waiver | **DOL ETA OUI** | State IUR or TUR reaches trigger thresholds | State-level |
| **`[20% Rule]`** | State-computed criterion added 2006; "extension of LSA to LAUS" | **State** computes from BLS series | **24-month avg** ≥ **20% above national** over same 24-mo. period | BLS **LAUS** units (states, counties, cities ≥25k, New England towns, select metro/labor-market areas) |
| **Federal suspensions** | Time limits suspended nationwide; no application needed | Congress (ARRA, FFCRA) | n/a | Nationwide |

**Where the external conflation likely comes from — and why the paper rejects it:**
The `[LSA]` designation formula contains its own **10% ceiling** ("jurisdictions with
unemployment rates above 10% are automatically designated LSAs," fn. 2). This internal
LSA parameter is a *different* 10% from the statutory `[10% Rule]`. The paper keeps them
strictly separate:
- The statutory **`[10% Rule]`** is a **PRWORA rate threshold** on "areas," is
  **self-certifiable**, and stands independent of any DOL designation.
- The **LSA 10% ceiling** is one internal parameter of the DOL ETA's LSA-designation
  algorithm (which otherwise keys on 20%-above-national with a 6% floor).

So the two "10%"s coincide numerically but are institutionally distinct rules;
conflating "the 10% rule" with "LSA" collapses (a) a self-certified statutory route and
(b) a DOL-administered designation with a 20%-above-national core. The paper's labels
are precisely designed to avoid this.

**`[20% Rule]` vs. `[LSA]`:** both rest on "20% above national," but `[LSA]` is a
**DOL designation over civil jurisdictions** (with 6%/10% overrides), whereas
`[20% Rule]` is **state-computed over BLS LAUS units** using a **24-month average**.
The paper explicitly frames `[20% Rule]` as an *extension* of the LSA logic to LAUS
geographies — i.e., deliberately a separate, later, broader route, not a synonym.

---

## 3. Effective dates / regime changes the paper relies on

| Date / period | Event | Paper location |
|---|---|---|
| **1996** | PRWORA establishes ABAWD work requirements (3 months of benefits in any 36-month period) and the two waiver criteria (`[10% Rule]`, `[Insufficient Jobs]`). First FNS guidance published. | p. 2–3 |
| **2006** | FNS guidance update adds `[20% Rule]`; mandates BLS **non-seasonally-adjusted** series; standardizes aggregation/rounding; bars **double-counting**; sets the **window-selection rule**; clarifies **no limit** on number of applications per year. | p. 6–7 |
| **Apr 1, 2009 – Sep 30, 2010** | **ARRA** (American Recovery and Reinvestment Act) suspends ABAWD time limits nationwide; no applications needed. | p. 7 (item b) |
| **2016** | FNS guidance update; clarifies groups must be **geographically contiguous** or part of an **"economic region"**; sharpens that states may discontinue/amend existing waivers at will (fn. 9). Core features of 1996/2006 maintained. | p. 6–7 |
| **Apr 1, 2020 – Jun 30, 2023** | **FFCRA** (Families First Coronavirus Response Act, 2020) suspends ABAWD time limits nationwide; no applications needed. | p. 7 (item b) |
| **2021** | FNS guidance update; core features of 1996/2006 maintained. | p. 7 |
| **2025** | **One Big Beautiful Bill (OBBB)** "erased the Insufficient Jobs Criterion and banned area grouping." Regulation now requires an individual geographic unit to qualify **on its own under the `[10% Rule]`.** (Paper flags "TO DO: Include reference to latest FNS guidance when it is issued.") | p. 7 |

> **[VERBATIM]** (p. 7)
> "In 2025, the One Big Beautiful Bill erased the Insufficient Jobs Criterion and
> banned area grouping. Today, the regulation requires an individual geographic unit to
> qualify on its own under the [10% Rule]."

> **[VERBATIM]** (p. 7, item b)
> "From April 1, 2009 to September 30, 2010, the American Recovery and Reinvestment Act
> (ARRA) suspended the ABAWD time limits. The Families First Coronovirus Response Act
> (FFCRA) of 2020 did the same from April 1, 2020, to June 30, 2023. States did not
> need to apply for waivers during either of these periods."

**Note on the FFCRA end date:** the paper gives **June 30, 2023** as the end of the
FFCRA-era suspension. (This is the paper's stated date; cross-check against independent
research, since the statutory unwinding of the ABAWD suspension is sometimes dated to
the 2023 Fiscal Responsibility Act / mid-2023 — worth confirming the paper's exact
basis.)

---

## 4. Operational details the paper uses

### 4.1 Data source and geography
- **[PARAPHRASE]** (p. 5) The 1996 guidance recommended states cite official **BLS
  Local Area Unemployment Statistics (LAUS)** figures to justify a waiver in terms of
  area unemployment. Because LAUS covers a pre-specified set of geographies, a norm
  formed that waivers go to **LAUS geographic units**: states, counties, cities with
  population ≥ 25,000, cities and towns in New England, and select metropolitan and
  small labor-market areas.
- **[PARAPHRASE]** (p. 6) The 2006 guidance mandated calculations use BLS
  **non-seasonally-adjusted** unemployment and labor-force series.
- **[PARAPHRASE]** (p. 9, §2.1) Data used are **county-month** unadjusted labor-force
  and unemployment counts; the word "county" is used to mean **county-equivalent**
  throughout (encompassing CT planning regions, AK boroughs, LA parishes, etc.,
  fn. 15). **National** rate for the `[20% Rule]` threshold comes from BLS "LN" series
  (fn. on p. 10).
- **[PARAPHRASE / data limitation]** (p. 9–10) The authors currently only have
  **post-January-2011 vintages** of LAUS county-month data; BLS appears not to have
  archived pre-2011 vintages. This vintage limitation drives their "main sample"
  restriction and is implicated in the anomalous 2023 North Dakota result (§5.1).

### 4.2 Reference-period / window-selection rule (`[20% Rule]`)
> **[VERBATIM]** (p. 6)
> "It specified that the 24-month window used to justify a [20% rule] exception could
> begin no earlier than the January of two fiscal years prior to the fiscal year when
> the requested waiver would take effect. This window selection rule was taken directly
> from LSA designation rules."

- **[PARAPHRASE]** The qualifying statistic is a **24-month average**. The window may
  begin **no earlier than January of two fiscal years before the start FY** of the
  waiver, and states may use **any consecutive 24-month window** after that January
  (p. 8, item I). This creates the applicant "degree of freedom" of **window choice**.
- **[PARAPHRASE]** (p. 8, item II) A state can also expand the menu of available
  windows by ~12 by **timing the application/start date**: applying for a start date in
  or before September (current FY) rather than October (next FY), and applying closer
  to the start date as BLS publishes more recent data.

### 4.3 Grouping / contiguity / aggregation
- **[PARAPHRASE]** (p. 5) The 1996 guidance **explicitly allowed states to combine
  geographic units** (e.g., counties) into groups when computing unemployment rates.
  Quoted guidance language:
  > **[VERBATIM]** "USDA will give States broad discretion in defining areas that best
  > reflect the labor market prospects of program participants and State administrative
  > needs..." and "Accordingly, states should consider areas within, or combinations
  > of, counties, cities, and towns..."
- **[PARAPHRASE]** (p. 6) The **2016 guidance** clarified groups must be either
  **geographically contiguous** or part of an **"economic region"**; the authors
  believe contiguity was already respected in "(nearly?) every approved application
  since the beginning" (fn. 6, flagged as a conjecture / de facto rule).
- **[PARAPHRASE]** (p. 6) **No double-counting**: the 2006 guidance clarified that no
  geographic unit may be included in more than one waived group within an application.
- **[PARAPHRASE]** (p. 6) The 2006 guidance gave a **standardized aggregation and
  rounding procedure** removing ambiguity in how states compute area rates and national
  thresholds from BLS series. (Paper does not reproduce the exact rounding rule.)

### 4.4 Duration and application frequency
- **[PARAPHRASE]** (p. 6) 1996 guidance: waivers typically granted **one year at a
  time** (fn. 7 notes some other durations, e.g. three-month seasonal, exist).
- **[PARAPHRASE]** (p. 7) 2006 guidance: **no limit** on the number of times a state may
  apply within a year; in practice most states filed on a **regular annual cycle**.

### 4.5 How the criteria enter the formal model (important operationalization nuance)
- **[PARAPHRASE]** (p. 13, §3.1) In the model, the county-group qualifying condition is
  an **unemployment-threshold** condition: for national rate α̃ during a window, the
  operative threshold is **min{1.2 × α̃, .1}** — i.e., the required area rate is the
  **lower of** "20% above national" (1.2·α̃) and **0.10**. The paper states the **min
  operator "incorporates the [10% Rule] encoded in PRWORA."**
- **[FLAG — subtle definitional shift]** In the institutional description (§1.1),
  `[10% Rule]` is a **standalone statutory level test** (raw area unemployment > 10%,
  self-certifiable, no window specified). In the **model/empirics** (§3.1, and
  `V_i^{10%} = 1{unemp_iw ≥ .1 for some w ∈ W(t^app, t^start)}` on p. 20), `[10% Rule]`
  is instead folded into the **same 24-month-window machinery** as `[20% Rule]`, as a
  **cap** on the threshold. So the paper's *formal* `[10% Rule]` is "clears 10% in some
  permissible window," which is not identical to the statute's unspecified-window level
  test. Note this when reconciling the paper against source law. The model also
  **assumes away** cities/metros and treats **counties as the only geography**, and
  handles `[LSA]` and `[EB]` as *bypass* conditions rather than inside the optimization.

### 4.6 Conditions that bypass the state decision problem
> **[VERBATIM]** (p. 7, §1.4 "degrees of freedom")
> "a. State-years that qualified under [EB] were automatically granted a year-long,
> statewide waiver."
> "c. State-years where 0 BLS geographic units or LSA civil jurisdictions individually
> qualify in any 24-month window leave no remaining decisions for the state to make."

**[PARAPHRASE]** The three bypass conditions (no real allocation choice) are: (a) `[EB]`
qualification → automatic statewide waiver; (b) a **federal suspension** in force (ARRA
or FFCRA); (c) zero individually-qualifying units. State-years *not* covered by these
are where the combinatorial allocation problem (window choice, geography choice,
grouping) is non-trivial — the paper's "main sample."

---

## 5. Extracted reference list (verbatim, p. 28)

The paper's reference section gives **titles and dates but no URLs or document/notice
numbers** for the FNS guidance memos (a gap to fill from independent research). Full
list as printed:

1. **Bauer, Lauren and Chloe N. East.** "A primer on snap work requirements," 2026.
   *(cited p. 2 for the "ABAWD requirements cover just 9%" figure)*

2. **Corson, Walter and Anu Rangarajan.** "Extended UI benefit triggers," 1993.
   — Paper notes: *"Local PDF in literature folder: 'Corson and Rangarajan (1993).pdf'."*
   *(cited p. 5 for how IUR/TUR extended-benefit triggers are calculated)*

3. **Han, Jeehoon.** "The impact of snap work requirements on labor supply."
   *Labour Economics*, 74:102089, 2022.
   *(cited pp. 3, 21 as prior work using ABAWD-waiver variation)*

4. **Lippold, Kye and Remy Levin.** "The effects of transfer programs on childless
   adults: Evidence from food stamps," 2021. — **SSRN working paper 3655794.**
   *(cited pp. 3, 21 as prior work using ABAWD-waiver variation)*

5. **U.S. Department of Agriculture, Food and Nutrition Service.** "Guidance for states
   seeking waivers for food stamp limits," **December 1996.** *(the original guidance)*

6. **U.S. Department of Agriculture, Food and Nutrition Service.** "Guidance on
   requesting abawd waivers," **August 2006.** *(adds `[20% Rule]`, window rule, etc.)*

7. **U.S. Department of Agriculture, Food and Nutrition Service.** "Supplemental
   nutrition assistance program: Guide to supporting requests to waive the time limit
   for able-bodied adults without dependents (abawd)," **December 2016.**
   *(adds contiguity/economic-region clarification)*

8. **U.S. Department of Agriculture, Food and Nutrition Service.** "Supporting requests
   to waive the time limit for able-bodied adults without dependents," **September
   2021.**

**Statutes/acts named in text but NOT given formal citations in the reference list**
(to source independently): PRWORA (Personal Responsibility and Work Opportunity
Reconciliation Act of 1996); ARRA (American Recovery and Reinvestment Act, 2009); FFCRA
(Families First Coronavirus Response Act, 2020); the One Big Beautiful Bill (2025).
Institutions named: DOL ETA (Employment and Training Administration), DOL ETA OUI
(Office of Unemployment Insurance); BLS LAUS; BLS "LN" national series.

---

## 6. Places where the paper is vague, incomplete, or internally inconsistent

1. **`[10% Rule]` reference period unspecified in the institutional text.** §1.1 gives
   only "unemployment rate of over 10 percent" with no window or data source, whereas
   `[20% Rule]` gets a precise 24-month/window definition. The model (§3.1, §4.2) later
   *silently* recasts `[10% Rule]` as a 24-month-window cap (`min{1.2α̃, .1}`), a
   stronger/different object than the statute's plain level test. **Flag for
   reconciliation with statutory text.** (§4.5 above.)

2. **"Weakly dominated" claim is a conjecture.** The assertion that `[10% Rule]` is
   "usually weakly dominated" by `[20% Rule]` (fn. 1) rests on the empirical premise
   that anything clearing 10% also clears 20%-above-national — flagged "TO DO,"
   unverified, and *not* obviously true when the national rate is high (e.g., 2009–2010,
   2020–2021), when 1.2·α̃ could exceed 10%. This is exactly the case the `min` operator
   handles, so the dominance claim and the model are consistent but the *empirical
   frequency* is unestablished.

3. **Contiguity as de facto vs. de jure.** The paper says the 2016 guidance "clarified"
   contiguity but suspects it "was already a de facto rule" respected in "(nearly?)
   every" prior application (fn. 6) — an explicit hedge ("nearly?").

4. **Softer criteria under-specified by design.** "Lagging job growth" and "declining
   occupations/industries" have no thresholds; the claim that "few waivers were ever
   approved on their basis alone" is flagged "TO DO: Confirm."

5. **FFCRA suspension end date.** Paper states June 30, 2023 (see §3 note); confirm the
   statutory basis independently.

6. **Aggregation/rounding rule not reproduced.** The paper asserts the 2006 guidance
   gave a "standardized aggregation and rounding procedure" but does not state the
   procedure; retrieve it from the 2006 FNS memo (reference #6) if the KB needs it.

7. **LSA floor/ceiling numbers (6%/10%) sourced only to the paper.** Footnote 2's
   6%-floor / 10%-ceiling override of the LSA 20% rule should be cross-checked against
   DOL ETA LSA regulations (20 CFR Part 654, Subpart A) — the paper gives no citation
   for it.

8. **Draft-wide caveat.** Many quantitative claims sit behind author "TO DO" footnotes;
   the paper is explicitly preliminary. Definitions are stable; magnitudes are not.
