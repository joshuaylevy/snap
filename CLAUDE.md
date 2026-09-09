# Project conventions

Working agreements for this repo — for Claude sessions and for humans. Where a
convention exists because something went wrong, the incident is named; those are the
ones not to quietly relax.

## Environment

Python runs in the **`snap` conda env**, always **from the project root**:

```bash
source $(conda info --base)/etc/profile.d/conda.sh && conda activate snap
```

`make` handles this itself (`CONDA_ACTIVATE`). R uses `renv` (`renv.lock`).

## The numbered tree

Top level is pipeline order, and a child's number extends its parent's:

```
0_lit/       literature, statutes, the rules knowledge base
1_data/      10_raw → 11_clean
2_scripts/   21_scrape_dl → 22_extract → … → 26_present
3_tabs/  4_figs/  5_write/  6_present/
99_misc/
```

So `2_scripts/22_extract/222_fna_waivers/2220b_extraction_prompt.txt` reads as
`2 scripts / 22 extract / 222 fna_waivers / 2220b prompt`. Trailing letters mark
files belonging to one step (`2220a`/`2220b`/`2220c` are one spec).

**Script numbers and output numbers mirror each other.** `2_scripts/26_present/261_waiver_map`
writes to `6_present/61_waiver_map`; `2_scripts/22_extract/222_fna_waivers` writes to
`1_data/10_raw/102_fna/1022_extractions`. Given one, you can derive the other — that
correspondence is the convention, not a coincidence, and there is no source/output
ambiguity to resolve.

## Explicit paths

Declare path globals at the top of every script, composed from the project root down:

```python
DATA_DIR   = pathlib.Path("1_data")
EXTRACT_DIR = DATA_DIR / "10_raw" / "102_fna" / "1022_extractions"
OUT_DIR    = pathlib.Path("6_present") / "61_waiver_map"
```

**Never** locate a script implicitly — no `Path(__file__).resolve().parent`, no walking
up with `.parent`. Every read and write is declared from the root, so a script's inputs
and outputs are readable off the first screen without running it.

Every builder calls `mkdir(parents=True, exist_ok=True)` on its own output root, so a
clean checkout rebuilds whether or not the directory exists.

## Make is the entry point

Every runnable step has a target. If a script can only be run by knowing its path, it
is not finished — wire it up. Targets share their overrides (`STATES`, `JSON_ROOT`,
`MODEL_TAG`, `STATE`, `FYS`) so one set of variables runs a step and then scores it.

## What goes in git

The rule is **provenance, not size**: version what cannot be regenerated, ignore what
can.

| | |
|---|---|
| **Tracked** | code, specs, prompts, schemas, the rules KB, the geography reference, hand-curated registries and judgment files, docs |
| **Ignored** | scraped corpora, extraction outputs, derived CSVs, built pages, raw reference pulls, aux files |

Hand-curated inputs that happen to be `.csv` are un-ignored explicitly and say why —
`2226a_state_tier_registry.csv`, `010_county_changes_1997_present.csv`. Tier
assignments and prose warts are judgments, not derived counts.

Two consequences to hold in mind:

- **Extraction arms live only in the working tree.** They are gitignored, deliberately:
  a tracked JSON stays reachable through `git show` and re-opens the exact channel the
  blinding rule closes. A deleted arm does not come back, and re-running the same spec
  does not reproduce it. Treat an arm directory as a lab notebook.
- **Gold sheets are not version controlled** — they are hand-edited `.xlsx`. A score is
  only interpretable against a stated sheet version, which is why `2225` prints the
  path, sha256 and row count before every report.

## Provenance hashing

Anything whose identity matters is hashed, so a result can be traced to what produced it:

| id | definition |
|---|---|
| `document_id` | `sha256(PDF content)` — not the path; files move and get renamed |
| `run_id` | `sha256(2220a ‖ 2220b ‖ 2220c ‖ model_tag)` — the (spec, model) pair |
| `geo_context_hash` | sha256 of the state geography reference at collate time |
| gold sha256 | printed in the validator header; the sheets are not in git |

`run_id` is computed from the spec files **as they are on disk now**, so editing a spec
silently redefines "the current run". Spec change and new `--json-root` move together.

## Working with the extraction pipeline

Full detail in `2_scripts/22_extract/222_fna_waivers/222_README.md` and
`2220_spec_history.md`. The three rules that are easy to break:

1. **Blinding.** Every extraction fan-out prompt must forbid the subagent from reading
   gold sheets, comparison CSVs, the ledger, `2225`, or any other extraction JSON —
   including other documents in its own arm. Not hypothetical: in the v1_3 WI run 2 of
   20 agents reconciled against outside material, one rewriting its answer to match
   gold; re-run blinded, FY2009's answer changed. The rule is in `2220b`, but agents
   follow the task prompt they are handed, so restating it per fan-out is what enforces
   it. Ask for a compliance line in the report.
2. **An example in the spec must be a pattern, not a document.** v1_5 found eleven
   examples lifted verbatim from corpus documents, one of them a gold-scored document's
   exact composition. Before adding an example to `2220b`/`2220c`, grep the extraction
   JSONs for its distinctive numbers and names.
3. **A score belongs to an arm.** `98.5%` under v1_4 and under v1_5 are different
   claims. Name the arm whenever a number is quoted.

## Decisions and open questions

`222_open_decisions.md` is the register: every decision awaiting a ruling, with
evidence, options and a recommendation; the deferred ones; and an index of what has
been settled. Read it before changing `2220b`/`2220c`. Interpretation questions that
arise mid-run go there rather than being resolved silently in one document's extraction.

## Commit messages

Conventional-commit subject (`feat(abawd):`, `fix(abawd):`, `chore(gitignore):`, …),
`!` for a breaking change, and a body that carries the reasoning. The body is the
research record — these commits get read months later to reconstruct why a number
means what it means. Include:

- **Why**, not just what — the problem the change solves, and the alternatives rejected.
- **Verification**: what was actually checked, with figures.
- **What was NOT verified or NOT done.** This is the load-bearing half. A commit that
  changes a prompt but has not re-run extraction should say so outright.
- A spec bump is marked in the subject: `feat(abawd)!: … (SPEC BUMP -> <run_short>)`.

## Session records

Run `/worklog` before `/clear`. It writes a narrative entry to `.worklog/entries/` and
appends a row to `.worklog/worklog.csv` keyed by session id, so any past session can be
reopened with `claude --resume <session_id>`. The mechanism is global (`~/.claude/`);
only the data lives here.

## Vendoring for artifacts

The waiver map publishes under a strict CSP and must reference nothing over the
network. Third-party assets are vendored into `2_scripts/26_present/261_waiver_map/`
(topojson-client, OFL font subsets) and inlined at assembly; `2612` asserts no fetching
construct survives into the page. Downloads are version-pinned and sha256-verified, so
a silent upstream revision fails loudly.

## Scraping etiquette

`.gov` sites are scraped slowly and politely: browser UA, request delay, exponential
backoff, resumable via content hash, everything recorded in a manifest. A document
already on disk whose sha256 matches is never re-fetched.
