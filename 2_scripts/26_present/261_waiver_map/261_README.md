# 261 — ABAWD waiver map

An interactive county choropleth of the extracted waiver applications, built as a
single self-contained HTML page that opens from `file://` and publishes as a Claude
Artifact under a strict CSP (the assembled page must reference nothing over the
network; `2612` asserts this).

## Where things live

There is **one** canonical location for the map, and it is split by role, not by
accident — the same source/output split the rest of the tree uses:

| | path | tracked? |
|---|---|---|
| **source** (edit here) | `2_scripts/26_present/261_waiver_map/` | yes |
| **output** (never edit) | `6_present/61_waiver_map/` | no — gitignored |

`6_present/61_waiver_map/` holds only `make viz` output: `610_waiver_map_data.json`
(the payload) and `611_waiver_map.html` (the assembled page). Both are ~26MB per
rebuild and fully reproducible, so they are gitignored; the `.gitkeep` marks the drop
point. **Do not hand-edit anything under `6_present/` — the next `make viz` overwrites
it.** If a change needs to survive, it belongs in a `2612*` source file here.

## Files

| file | role |
|---|---|
| `2610_download_us_atlas.py` | pinned, sha256-verified us-atlas county TopoJSON (v3.0.1) |
| `2611_build_viz_data.py` | extraction arms + geography reference → `610_waiver_map_data.json` (schema `wmap_v2`) |
| `2612_assemble_artifact.py` | inlines everything below into `611_waiver_map.html` |
| `2612a_waiver_map_template.html` | page skeleton with substitution markers |
| `2612b_waiver_map_app.js` | map application |
| `2612c_waiver_map_styles.css` | stylesheet |
| `2612d_topojson-client.v3.1.0.min.js` | vendored, so the page fetches nothing |
| `2612e_fonts/` | vendored latin WOFF2 subsets (SIL OFL 1.1), base64-inlined |
| `2612f_rules_tab.html` | rules-history tab |
| `2612g_pack_tab.html` / `2612h_pack_demo_app.js` | weighted-set-packing demo tab |

## Building

From the project root, in the `snap` conda env:

```bash
make viz          # = viz_fetch + viz_data + viz_html
```

or a stage at a time:

```bash
make viz_fetch                              # once; idempotent, sha256-pinned
make viz_data  VIZ_ARGS="--arm claude_v1_5_adjud"
make viz_html
```

### Inputs it needs

1. **An extraction arm** under `1_data/10_raw/102_fna/1022_extractions/` — the JSONs
   are gitignored and live only in the working tree, so a fresh clone has none.
   See `2_scripts/22_extract/222_fna_waivers/222_README.md`.
2. **The state geography reference**, `1_data/11_clean/111_geo_context/*.md` (tracked)
   — used to resolve unit names to FIPS. Rebuild with `make geo_context`.
3. **The us-atlas topology** — `make viz_fetch`.

### Arm selection, and one hazard worth knowing

With no `--arm`, `2611` reads every `claude_v<major>_<minor>_*` directory on disk in
ascending version order, and a later arm supersedes an earlier one **document by
document** — so re-extracting a state under a new spec updates the map with no code
change, and the map never blends two specs for one PDF. Pre-spec arms (`claude`,
`claude_run2`) are opt-in via `--arm`.

Precedence is `sorted()` over `((major, minor), dirname)`, so **two arms at the same
`(major, minor)` are ordered alphabetically**. Today that means `claude_v1_5_haiku`
outranks `claude_v1_5_adjud` — which is harmless only because their document sets are
disjoint (haiku holds AZ + MA, adjud holds the other 34 states). If a document ever
lands in both, the map will silently prefer the Haiku extraction over the Sonnet one
on nothing but a letter of the alphabet. Pass `--arm` explicitly when it matters.

## Size budget

`2612` enforces a soft budget (currently 13MB) against the artifact's 16MB hard cap.
At 694 documents the page is ~11.7MB and grows ~0.017MB per document, so **the last
states will not fit.** The lever, named in `2612`'s docstring: subset the topology to
the states actually present in the payload (the national mesh is the largest fixed
cost and most of it is never drawn), then compress the per-unit records.
