.PHONY: conda_activate_snap_env openai_abawd_waivers_subset
SHELL := /bin/bash
CONDA_ACTIVATE := source $(shell conda info --base)/etc/profile.d/conda.sh; conda activate snap

# FOLDER VARIABLES
DATA := 1_data
100_RAW_USDA := $(DATA)/10_raw/100_usda


SCRIPTS := 2_scripts
21_SCRAPE_DL := $(SCRIPTS)/21_scrape_dl
211_ABAWD_WAIVERS := $(SCRIPTS)/21_scrape_dl/211_abawd_waivers
22_EXTRACT := $(SCRIPTS)/22_extract
221_EXTRACT_ABAWD_WAIVERS := $(SCRIPTS)/22_extract/221_abawd_waivers


# COMMANDS

full_project:
	@echo "------------- MAKING FULL PROJECT -------------"
	openai_abawd_waivers
	@echo "--------------- DONE -----------------"

openai_abawd_waivers: \
	$(100_RAW_USDA)/1000_abawd_waivers/10001_abawd_waiver_pdf_document_inventory.csv \
	$(100_RAW_USDA)/1001_abawd_openai_responses/10010_abawd_waiver_interpretations.csv
	
	@echo "------------- MAKING ALL -------------"
	@echo "--------------- DONE -----------------"




# Document inventory (10001): one row per PDF path + document_id for extraction joins
$(100_RAW_USDA)/1000_abawd_waivers/10001_abawd_waiver_pdf_document_inventory.csv:
	@echo "======================= MAKING ABAWD PDF DOCUMENT INVENTORY ======================="
	@echo "Assumes that all relevant ABAWD waivers have been downloaded/scraped"
	@echo "These can be scraped by using  2110_download_abawd_waivers.R"
	@echo "-------------------------------------------------------------------------"

	@echo "Generating document inventory CSV"
	Rscript --quiet $(211_ABAWD_WAIVERS)/2111_make_abawd_waiver_db.R
	@echo "Generated document inventory"
	@echo ========================================================================="

# Parse OpenAI Responses of ABAWD Waivers
$(100_RAW_USDA)/1001_abawd_openai_responses/10010_abawd_waiver_interpretations.csv: \
	$(100_RAW_USDA)/1000_abawd_waivers/10001_abawd_waiver_pdf_document_inventory.csv
	@echo "================== OPEN AI ABAWD WAIVER INTERPRETATIONS =================="
	@echo "Takes downloaded waivers and parses them using GPT via OpenAI Responses API"
	@echo "API responses are stored locally as JSONs to be further processed and"
	@echo "checked by hand before being used for analysis" 
	@echo "-------------------------------------------------------------------------"
	
	@echo "Submitting PDFs to OpenAI Responses API for parsing"
	$(CONDA_ACTIVATE) && python $(221_EXTRACT_ABAWD_WAIVERS)/2210_extract_abawd_waivers.py
	@echo "Extracted PDF contents saved as JSONs and organized into csvs"
	$(CONDA_ACTIVATE) && python $(221_EXTRACT_ABAWD_WAIVERS)/2211_interpret_abawd_waiver_json.py
	@echo "=========================================================================="

# Subset of fiscal years only, e.g.: make openai_abawd_waivers_subset FYS="2019 2020"
openai_abawd_waivers_subset:
	$(CONDA_ACTIVATE) && python $(221_EXTRACT_ABAWD_WAIVERS)/2210_extract_abawd_waivers.py --fys $(FYS)
	$(CONDA_ACTIVATE) && python $(221_EXTRACT_ABAWD_WAIVERS)/2211_interpret_abawd_waiver_json.py


# =====================================================================
# FNA REBUILD PIPELINE (v2) -- see .claude/plans/abawd-fna-rebuild.plan.md
# Rebuild against the FNA time-limit waiver archive (applications + responses).
# Targets below are STUBS until each phase's scripts are implemented; the legacy
# openai_abawd_waivers pipeline above remains the working path in the meantime.
# =====================================================================

.PHONY: fna_recon fna_download fna_app_zips fna_inventory fna_worklist fna_collate fna_status \
        fna_extract fna_panel fna_validate

# FNA folder variables (numbered tree mirrors the target architecture)
LIT := 0_lit
00_ABAWD_RULES := $(LIT)/00_abawd_rules
102_RAW_FNA := $(DATA)/10_raw/102_fna
11_CLEAN := $(DATA)/11_clean
110_WAIVER_PANEL := $(11_CLEAN)/110_waiver_panel
212_FNA_TIMELIMIT := $(21_SCRAPE_DL)/212_fna_timelimit
222_FNA_WAIVERS := $(22_EXTRACT)/222_fna_waivers

# Phase 2 -- recon the FNA site: discover FY-batch pages and map document links
fna_recon:
	$(CONDA_ACTIVATE) && python $(212_FNA_TIMELIMIT)/2120_recon_fna_site.py

# Phase 2 -- deterministic, resumable, rate-limited download into per-FY folders.
# Optional subsetting: make fna_download FNA_ARGS="--batches 2015-2019"
fna_download:
	$(CONDA_ACTIVATE) && python $(212_FNA_TIMELIMIT)/2121_download_fna_waiver_docs.py $(FNA_ARGS)

# Phase 2 -- the "State Requests and Data" zips: the STATE APPLICATIONS (requests),
# unemployment spreadsheets, LSA lists and maps that sit alongside the FNS responses.
# Deterministic, resumable, sha256-verified; extracts into a per-FY tree.
# Optional subsetting: make fna_app_zips FNA_ARGS="--batches 2015-2019"
fna_app_zips:
	$(CONDA_ACTIVATE) && python $(212_FNA_TIMELIMIT)/2123_download_fna_application_zips.py $(FNA_ARGS)

# Phase 2 -- content-hash document inventory (document_id = sha256(file content))
fna_inventory:
	@echo "[stub] fna_inventory: $(212_FNA_TIMELIMIT)/2122_make_document_inventory.py not yet implemented"

# Phase 3 -- Claude in-harness extraction. fna_worklist prints the per-document agent
# assignments (each with its state geography reference); the fan-out itself is driven
# by a Claude session, see 2222_extract_claude_protocol.md. fna_collate validates the
# written JSONs into the ledger.
#
# A run arm = (spec, model, json root). ALWAYS pass the same JSON_ROOT/MODEL_TAG to
# worklist and collate, and point a new spec at a NEW root -- the output path is just
# <root>/<batch>/<stub>.json, so re-running in place silently overwrites the older arm.
#   make fna_worklist STATES="WI ND" JSON_ROOT=$(1022_EXTRACTIONS)/claude_v1_3_geo
#   make fna_collate  STATES="WI ND" JSON_ROOT=$(1022_EXTRACTIONS)/claude_v1_3_geo
# JSON_ROOT is shared with fna_validate, so the same override scores what you just ran.
1022_EXTRACTIONS := $(102_RAW_FNA)/1022_extractions
STATES ?= WI ND
MODEL_TAG ?= claude-sonnet-5
JSON_ROOT ?= $(1022_EXTRACTIONS)/claude
FNA_EXTRACT_ARGS = --states $(STATES) --json-root $(JSON_ROOT) --model-tag $(MODEL_TAG) $(FNA_ARGS)

fna_worklist:
	$(CONDA_ACTIVATE) && python $(222_FNA_WAIVERS)/2222_extract_claude.py worklist $(FNA_EXTRACT_ARGS)

fna_collate:
	$(CONDA_ACTIVATE) && python $(222_FNA_WAIVERS)/2222_extract_claude.py collate $(FNA_EXTRACT_ARGS)

fna_status:
	$(CONDA_ACTIVATE) && python $(222_FNA_WAIVERS)/2222_extract_claude.py status --states $(STATES)

fna_extract: fna_worklist
	@echo ""
	@echo "Fan out one Claude subagent per not-[done] document above, then:"
	@echo "  make fna_collate STATES=\"$(STATES)\" JSON_ROOT=$(JSON_ROOT) MODEL_TAG=$(MODEL_TAG)"

# Phase 4 -- build waiver-unit and state-year application panels
fna_panel:
	@echo "[stub] fna_panel: $(222_FNA_WAIVERS)/2224_build_waiver_panel.py not yet implemented"

# Phase 5 -- validate extractions vs the hand-collected gold standards. A state is
# scoreable iff 1_data/<CODE>-hand-collected.xlsx exists (WI, ND, DE, IA so far);
# states without a sheet (e.g. NC) can be compared run-to-run but never scored.
# FYS defaults to empty, which scores every fiscal year the sheet carries.
#   make fna_validate STATE=WI
#   make fna_validate STATE=ND FYS="2020 2021" JSON_ROOT=$(1022_EXTRACTIONS)/claude_v1_3_geo
STATE ?= WI
FYS ?=
fna_validate:
	$(CONDA_ACTIVATE) && python $(222_FNA_WAIVERS)/2225_validate_vs_hand_collected.py \
		--state $(STATE) $(if $(strip $(FYS)),--fys $(FYS),) --json-root $(JSON_ROOT)
# =====================================================================
# GEO REFERENCE -- state geography context for extraction sub-agents
# =====================================================================

.PHONY: geo_fetch geo_context

213_GEO := $(21_SCRAPE_DL)/213_geo
103_RAW_GEO := $(DATA)/10_raw/103_geo
111_GEO_CONTEXT := $(11_CLEAN)/111_geo_context

# Polite, idempotent download of Census/BLS geographic reference files.
# Optional subsetting: make geo_fetch GEO_ARGS="--only bls_laus_area"
geo_fetch:
	$(CONDA_ACTIVATE) && python $(213_GEO)/2130_download_geo_reference.py $(GEO_ARGS)

# Build per-state agent-facing geography context files (offline; needs geo_fetch once).
# Optional subsetting: make geo_context GEO_ARGS="--states WI NC"
geo_context:
	$(CONDA_ACTIVATE) && python $(213_GEO)/2131_build_geo_context.py $(GEO_ARGS)

# =====================================================================
# WAIVER MAP -- interactive county choropleth of extracted applications
# =====================================================================

.PHONY: viz_fetch viz_data viz_html viz

261_WAIVER_MAP := $(SCRIPTS)/26_present/261_waiver_map
61_WAIVER_MAP := 6_present/61_waiver_map

# Pinned us-atlas county topology (sha256-verified, idempotent).
viz_fetch:
	$(CONDA_ACTIVATE) && python $(261_WAIVER_MAP)/2610_download_us_atlas.py $(VIZ_ARGS)

# Extraction arm + geography reference -> 610_waiver_map_data.json.
# Optional: make viz_data VIZ_ARGS="--arm claude_run2"
viz_data:
	$(CONDA_ACTIVATE) && python $(261_WAIVER_MAP)/2611_build_viz_data.py $(VIZ_ARGS)

# Inline data + topology + app into the one-file page (file:// ready, artifact ready).
viz_html:
	$(CONDA_ACTIVATE) && python $(261_WAIVER_MAP)/2612_assemble_artifact.py

viz: viz_fetch viz_data viz_html
