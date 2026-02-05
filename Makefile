.PHONY: conda_activate_snap_env
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
	$(100_RAW_USDA)/1000_abawd_waivers/10000_pdf_tracker.csv \
	$(100_RAW_USDA)/1001_abawd_openai_responses/10010_abawd_waiver_interpretations.csv
	
	@echo "------------- MAKING ALL -------------"
	@echo "--------------- DONE -----------------"




# Create a PDF tracker sheet for ABAWD Waivers
$(100_RAW_USDA)/1000_abawd_waivers/10000_pdf_tracker.csv:
	@echo "======================= MAKING A PDF TRACKER SHEET ======================="
	@echo "Assumes that all relevant ABAWD waivers have been downloaded/scraped"
	@echo "These can be scraped by using  download_abawd_waivers.R"
	@echo "-------------------------------------------------------------------------"

	@echo "Generating PDF tracker sheet"
	Rscript --quiet $(211_ABAWD_WAIVERS)/make_abawd_waiver_db.R
	@echo "Generated PDF tracker sheet"
	@echo =========================================================================="

# Parse OpenAI Responses of ABAWD Waivers
$(100_RAW_USDA)/1001_abawd_openai_responses/10010_abawd_waiver_interpretations.csv: \
	$(100_RAW_USDA)/1000_abawd_waivers/10000_pdf_tracker.csv
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