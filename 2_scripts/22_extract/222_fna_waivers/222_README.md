# 222 — FNA ABAWD waiver extraction pipeline

Turns the USDA FNS/FNA time-limit waiver archive — ~1,135 letters and forms across 55
states and territories, FY1997–FY2026, many of them scanned with no text layer — into
one structured JSON record per document, conforming to `2220c_schema.json`.

## The one thing to understand first

**The extractor is a Claude agent, not a script.** `2222_extract_claude.py` builds a
work list and validates the results; between those two steps a human (or an
orchestrating Claude session) fans out one subagent per document, each of which *reads*
the PDF — as images where there is no text layer — and writes a JSON file. There is no
`make fna_extract` that runs end to end, and there cannot be.

Three properties follow, and every convention below exists because of them:

| property | consequence |
|---|---|
| **Not deterministic.** Independent runs of the same spec differ on transcription and on judgment calls. | A spec revision can only be evaluated against a *fixed* prior arm. Arms are never overwritten. |
| **Agents have full repo access.** | They will read gold sheets and other arms unless forbidden. Blinding is mandatory in every fan-out prompt. |
| **Outputs are gitignored.** | An arm's JSONs live only in the working tree. A deleted arm does not come back. |

## Data it needs

| what | where | tracked? | how to get it |
|---|---|---|---|
| Response PDFs (the corpus) | `1_data/10_raw/102_fna/1020_timelimit_waiver_docs/FY*/` | no | `make fna_recon` then `make fna_download` |
| State applications + data | `1_data/10_raw/102_fna/1023_application_docs/` | no | `make fna_app_zips` (`2123`) |
| State geography reference | `1_data/11_clean/111_geo_context/*.md` (53 files) | **yes** | `make geo_fetch` then `make geo_context` |
| ABAWD rules knowledge base | `0_lit/00_abawd_rules/002_rules_machine.yaml` | **yes** | in repo |
| Gold standards | `1_data/<CODE>-hand-collected.xlsx` | no — hand-maintained | Josh |

A fresh clone has the code, the geography reference and the rules KB, and none of the
corpus. `fna_recon` + `fna_download` rebuild the corpus from the FNA site; both are
polite, rate-limited, resumable and content-hashed.

**Gold is not version controlled.** The sheets are hand-edited `.xlsx`, so a score is
only interpretable against a stated sheet version — `2225` prints the path, sha256 and
row count in a provenance header for exactly this reason. Sheets exist for **WI, ND,
DE, IA, WV, WY, GA, KY**. NC deliberately has none: it is the run-to-run stability
state, comparable across arms but never scoreable.

## Files

| file | role |
|---|---|
| `2220a_extraction_instruction.txt` | system role for the extraction agent |
| `2220b_extraction_prompt.txt` | the task spec — splitting rule, criterion codes, geography, QC |
| `2220c_schema.json` | canonical draft-07 schema; **both** extractors emit this |
| `2220_spec_history.md` | **every spec change, its reasoning, and its `run_id`** |
| `fna_extraction_results.py` | the spine: path globals, `document_id`, `run_id`, work list, validation, `flatten_to_gold`, the ledger |
| `2222_extract_claude.py` | driver — `worklist` / `collate` / `status` |
| `2222_extract_claude_protocol.md` | the fan-out protocol + the per-state run log |
| `2223_flatten_to_gold.py` | nested JSON → gold-layout flat CSV |
| `2225_validate_vs_hand_collected.py` | agreement report vs a gold sheet |
| `2226_progress_table.py` | one row per state: tier, corpus, run status, gold agreement |
| `222_open_decisions.md` | **the open-decisions register — read before touching `2220b`/`2220c`** |

## Identity: `document_id`, `run_id`, arms

```
document_id = sha256(PDF content)                    # not the path — files move
run_id      = sha256(2220a ‖ 2220b ‖ 2220c ‖ model_tag)
arm         = (spec, model, --json-root)             # one directory per arm
ledger row  = (document_id, extractor, run_id)
```

`run_id` is computed from the spec files **as they are on disk right now**, not from
the run that produced a JSON. So:

> **Every spec change needs a new `--json-root`.** The output path is only
> `<root>/<batch>/<stub>.json`. Re-running in place overwrites the previous arm, and
> the JSONs are gitignored, so there is nothing to recover. Collating an old root under
> a new spec would relabel that arm's output as the new spec's — the driver refuses
> this (`--force` overrides), because it survives into every downstream comparison.

Name arms `claude_v<major>_<minor>_<slug>`; `2611` (the waiver map) discovers them by
that pattern and applies newest-spec-wins precedence. Arms on disk now:

| arm | `run_id` | model | documents |
|---|---|---|---|
| `claude_v1_4_fedsusp` | `3c73108d` | sonnet-5 | 63 — DE, IA, NC, ND, WI |
| `claude_v1_5_adjud` | `fe5d1b3c` | sonnet-5 | 649 across 34 states *(25 schema-invalid)* |
| `claude_v1_5_haiku` | `9959aa25` | haiku-4.5 | 44 — AZ, MA *(only arm holding either)* |

`claude_v1_4_fedsusp` is retained on purpose: it is the last arm run **before** the
v1_5 answer-leak sweep, and the only fixed baseline against which the leak's effect on
the gold states can be measured. See `2220_spec_history.md` § v1_5.

## Running it

From the project root, in the `snap` conda env. `STATES`, `JSON_ROOT` and `MODEL_TAG`
are shared across the targets, so one set of overrides runs and then scores the same arm.

```bash
ARM=1_data/10_raw/102_fna/1022_extractions/claude_v1_5_adjud

# 1. Work list — prints each document, its run_id, and per-document READ/WRITE paths.
make fna_worklist STATES="WI ND" JSON_ROOT=$ARM MODEL_TAG=claude-sonnet-5

# 2. Fan out (see below) — one Claude subagent per not-[done] document.

# 3. Collate — schema-validate the written JSONs, upsert the ledger.
make fna_collate  STATES="WI ND" JSON_ROOT=$ARM MODEL_TAG=claude-sonnet-5

# 4. Score against gold, if the state has a sheet.
make fna_validate STATE=WI JSON_ROOT=$ARM

# Where things stand overall:
make fna_status STATES="WI ND"
python 2_scripts/22_extract/222_fna_waivers/2226_progress_table.py
```

`[done]` in the work list keys on **the file existing**, not on `run_id` — a fresh arm
shows every document as not-done only because its root is empty.

### Step 2, the fan-out

Full procedure in `2222_extract_claude_protocol.md`. Each subagent gets a
self-contained prompt (subagents inherit no conversation context) telling it to:

1. Read `2220a`, `2220b`, `2220c`.
2. Read the **state geography reference** *before* the PDF — canonical spelling into
   `name`, verbatim print into `orig_text`, adjacency lists for contiguity checks. It
   is a starting point, never an exclusive list: never discard an area for being absent.
3. Read the assigned PDF, **all pages** (`Read` caps at 20 pages per request; pass a
   `pages` range beyond that). Treat scanned PDFs as images and transcribe.
4. Emit one JSON object per the schema, applying the **splitting rule** — one group per
   distinct rule/action combination, even within a single serial.
5. Write it to the exact `WRITE` path, no markdown fences.
6. Report briefly (serial, counts, criterion mix, actions, ambiguities) — **not** the
   full JSON.

Run in batches of roughly 5–16.

> ### Blinding — required in every fan-out prompt
>
> State that the agent may read **only** `2220a`/`2220b`/`2220c`, the rules KB, its
> state geography reference, and its one assigned PDF. It must **not** read: any
> `*.xlsx` gold sheet or `*gold*` path, any comparison CSV (`*vs_gold*`, `*_flat.csv`),
> the ledger, `2225`, or **any** other extraction JSON — other arms or other documents
> in its own arm. Ask for a one-line compliance confirmation in the report.
>
> This is not hypothetical. In the v1_3 WI run, 2 of 20 agents reconciled against
> material outside their assignment; one rewrote its answer to match gold, suppressing
> a second group *because* "the gold sheet shows only one row." Re-run blinded, FY2009's
> answer changed. Without blinding the agreement statistics are circular and the arm is
> not evidence.
>
> The rule is in `2220b`, but agents follow the task prompt they are handed. Restating
> it per fan-out is what actually enforces it.

## Scoring, honestly

`2225` reports three matching bases, because the gold sheets carry their own
transcription typos and exact matching would score the geography reference *down* for
correcting them:

- **`exact`** — comparable with pre-geo-context runs.
- **`gold_repaired`** — gold typos fixed, extraction left as written.
- **`canonical`** — both fixed; substantive agreement only.

Every repair is printed. `exact` and `gold_repaired` are identical by construction as
long as the sheets stay clean, which makes divergence a standing regression check: it
means a typo re-entered a sheet.

Two limits worth stating whenever a number is quoted. The unit-level comparison
**flattens away `groups[]`**, so bundling — the channel the adjacency lists actually
drive — is not scored at all (gold does carry `group_id` and `number_of_groups` if that
metric is wanted). And a score belongs to an arm: `98.5%` under v1_4 and under v1_5 are
different claims.

## Not built yet

`2221` (Extractor A, the OpenAI Batch path) and the A-vs-B adjudicator do not exist.
`fna_inventory` (`2122`) and `fna_panel` (`2224`) are Makefile stubs. `2224` is where
the federal-suspension overlay lands as a derived `(state, month)` function — v1_5
deliberately removed it from `criterion_code`, which now records only what a given
document decided. `222_open_decisions.md` § "Pending work that is not a decision"
tracks the rest.
