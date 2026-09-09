# SNAP ABAWD time-limit waivers

Research code for *"Inferring State Technical Capacity and Preferences from ABAWD
Waiver Allocations"* (Duggan & Levy).

SNAP's able-bodied-adults-without-dependents (ABAWD) time limit can be waived for areas
with weak labor markets. States choose **which** areas to request and **how to bundle**
them — a county alone, or inside a contiguous group whose combined unemployment rate
clears a threshold — and FNS approves or denies each request. Those choices are
observable, and they are the observed-choice side of the paper's weighted-set-packing
optimality analysis.

This repo builds the panel behind that analysis: for every geographic unit a state
applied for, whether FNS approved or denied it, under which qualifying rule the state
applied, and the data cited.

## What's here

The source is the USDA FNS/FNA time-limit waiver archive — roughly **1,135 documents
across 55 states and territories, FY1997–FY2026**, a mix of application packets and FNS
response letters, many of them scanned with no text layer. The pipeline scrapes it,
extracts structured records from each document, and validates them against
hand-collected gold-standard panels.

Extraction is **agentic**: Claude subagents read each PDF (as images where there is no
text layer) and emit one JSON record per document against a fixed schema, with
deterministic Python scaffolding around them for work lists, schema validation,
provenance and scoring. As of the current run, **649 documents across 34 states** are
extracted under the v1_5 spec.

## Layout

```
0_lit/          the ABAWD rules knowledge base — statutes, guidance, effective dates
1_data/         10_raw (scraped) → 11_clean (derived)
2_scripts/      21_scrape_dl → 22_extract → 26_present
5_write/        papers and summaries
6_present/      built pages and slides
Makefile        every runnable step
```

Numbers mirror between scripts and their outputs: `2_scripts/26_present/261_waiver_map`
builds `6_present/61_waiver_map`. See [`CLAUDE.md`](CLAUDE.md) for the full conventions.

## Documentation

| | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | project conventions — numbering, paths, what goes in git, provenance, commit style |
| [`2_scripts/22_extract/222_fna_waivers/222_README.md`](2_scripts/22_extract/222_fna_waivers/222_README.md) | **the extraction pipeline** — data it needs, how to run it, how to read a score |
| [`.../2220_spec_history.md`](2_scripts/22_extract/222_fna_waivers/2220_spec_history.md) | every extraction-spec change, its reasoning, and its `run_id` |
| [`.../2222_extract_claude_protocol.md`](2_scripts/22_extract/222_fna_waivers/2222_extract_claude_protocol.md) | the agentic fan-out protocol + the per-state run log |
| [`.../222_open_decisions.md`](2_scripts/22_extract/222_fna_waivers/222_open_decisions.md) | open coding decisions awaiting a ruling, with evidence and recommendations |
| [`2_scripts/26_present/261_waiver_map/261_README.md`](2_scripts/26_present/261_waiver_map/261_README.md) | the interactive county-choropleth artifact |

## Running it

Python is in the `snap` conda env; every script runs from the project root. `make`
activates the env itself.

```bash
make fna_recon                 # discover the FNA archive
make fna_download              # fetch the corpus (polite, resumable, hashed)
make geo_fetch && make geo_context   # per-state geography reference
make fna_worklist STATES="WI ND" JSON_ROOT=...   # then fan out; see 222_README.md
make fna_collate  STATES="WI ND" JSON_ROOT=...
make fna_validate STATE=WI
make viz                       # rebuild the waiver map
```

## A note on what a clone gets

Scraped corpora, extraction outputs and built pages are gitignored — they are
regenerable, or (for extraction arms) deliberately kept out of history so extraction
agents cannot read a prior run's answers. A fresh clone has the code, the specs, the
rules knowledge base and the geography reference; `make fna_recon` + `make fna_download`
rebuild the corpus. The hand-collected gold sheets are not distributed.

Extraction is not deterministic — independent runs of the same spec differ on
transcription and on judgment calls — so re-running does not reproduce a prior arm
byte-for-byte. Runs are identified instead by
`run_id = sha256(instruction ‖ prompt ‖ schema ‖ model_tag)` over files that *are*
versioned. `2220_spec_history.md` maps every `run_id` back to the commit that produced
it.
