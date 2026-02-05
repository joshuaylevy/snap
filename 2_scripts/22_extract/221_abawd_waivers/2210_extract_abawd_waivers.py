"""
Extract structured data from USDA ABAWD waiver PDFs using the OpenAI Responses API.

Run from project root with: conda activate snap && python 2_scripts/22_extract/221_abawd_waivers/extract_abawd_waivers.py

Requires OPENAI_API_KEY in your environment.
"""
import os
import re
import sys
import time
import json
import base64
import hashlib
import pandas as pd
import pathlib as pl
from pydantic_core.core_schema import bool_schema
from tqdm import tqdm
from openai import OpenAI
from datetime import datetime
from pydantic import BaseModel
from dotenv import dotenv_values
from typing import List, Dict, Any, Optional


RAW_DATA_DIR = pl.Path("1_data/10_raw/100_usda")
OUTPUT_DIR = RAW_DATA_DIR / "1001_abawd_openai_responses"
WAIVERS_DIR = RAW_DATA_DIR / "1000_abawd_waivers"
RESPONSES_API_URL = "https://api.openai.com/v1/responses"
OPENAI_API_KEY = dotenv_values(".env")["OPENAI_API_KEY"]
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file. Script will not run without it. Exiting in 10 seconds.")
client = OpenAI(api_key=OPENAI_API_KEY)



EXTRACTION_PROMPT = """You are extracting structured data from USDA FNS ABAWD (Able-Bodied Adults Without Dependents) waiver response letters. Each letter is a response from USDA to a state agency about SNAP work-requirement waivers.

Extract and return a JSON object with this exact structure:

1. geographic_areas: List of objects, each with:
   - name: The geographic area name (e.g., "Anchorage Borough", "Los Angeles County")
   - status: Either "approved" or "denied"
   - area_type: The type of geographic unit for this area (e.g., "borough", "census area", "county", "parish", "statewide", "Labor Market Area")
   - exemption_type: If the geographic_area has status "approved", then this section should explain why. Options include "LSA" (if the area has been deemed a "Labor Surplus Area" by the Department of Labor); "percent_20" (if the area had an unemployment rate 20percent higher than the national average over the previous 24 months); "percent_10" (if the area had an unemployment rate above 10 percent for 12 consecutive months); "other" (if some other reason is provided in the document); or "none" (if the document does not provide any information about the exemption type.
   - exemption_none_reason: If the geographic_area has a status of "approved" and an exemption_type of "other", an short explanation (<30 words) why you think the area is approved/what reasoning was provided.

2. waiver_serial_number: The serial number associated with the waiver. These are usually a sequence of numbers.

3. waiver_start_date: Start date of the waiver period (YYYY-MM-DD if determinable, else null)

4. waiver_end_date: End date of the waiver period (YYYY-MM-DD if determinable, else null)

5. author_name: Full name of the USDA/FNS official who signed or wrote the letter

6. author_title: Their title or role if given (e.g., "Director, Certification Policy Branch")

7. non_conforming_document: If you think that the document is not a valid waiver response letter, or does not contain sufficient information to be parsed, set this to True. Otherwise, set it to False. 

8. non_conforming_reason: If you set non_conforming_document to True, provide a brief explanation (<50 words) for why you think this document is not a valid waiver response letter or does not contain sufficient information to be parsed. One way that a document might be "non-conforming" is that it does not have a section titled "Waiver Response" with approximately 20 sections that follow it. Note that the relevant sections for many of the above questions include but are not limited to: 1. Waiver serial number; 2. Type of request; 8: Description of proposed alternative procedures; 9. Action and reason for approval or denial; 13. Expiration date etc. Another reason why a document might be non-conforming is that the document is a modification to an existing waiver, and so is only partially complete (may not have all of the above fields). Please succinctly explain why you think the document is non-conforming.

If information is not found, use null. For geographic_areas, use an empty list [] if none found.
Return ONLY valid JSON, no markdown code fences or extra text."""

EXTRACTION_INSTRUCTION = """You are an expert policy analysis that is particularly good at extracting information from government documents. Your job is to extract the requested information according to the provided format."""




def load_tracker() -> pd.DataFrame:
    """Load tracker and return rows with valid PDF paths."""
    df = pd.read_csv(WAIVERS_DIR / "10000_pdf_tracker.csv")
    return df


def tracker_cols_check(df: pd.DataFrame) -> bool:
    existing_cols = df.columns.tolist()
    required_cols = ["ai_parsed", "ai_parsed_response_path", "ai_parse_timestamp", ]
    if all(col in existing_cols for col in required_cols):
        return True
    else:
        print("Could not find all required columns in the tracker file. Adding them now.")
        for col in required_cols:
            if col not in existing_cols:
                df[col] = pd.NA  # create column with empty (None) values
        return tracker_cols_check(df)

def resolve_ai_response_path(fy: int, state_code: str, abawd_response_path: str) -> tuple[pl.Path, pl.Path]:

    FYyy = "FY{}".format(str(fy)[-2:])

    abawd_response_path_hash = hashlib.sha256(abawd_response_path.encode()).hexdigest()
    abawd_response_path_hash_short = abawd_response_path_hash[-8:]
    ai_response_folder = OUTPUT_DIR / FYyy
    ai_response_json = OUTPUT_DIR / FYyy / f"{state_code}-fy{fy}-{abawd_response_path_hash_short}.json"
    return (ai_response_folder, ai_response_json)




OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


tracker_df = load_tracker()

if not tracker_cols_check(tracker_df):
    raise Exception("Tracker columns are not correct. Please check the tracker file.")


# Count how many rows in "ai_parsed" are not null/false (progress already made)
initial_done = len(tracker_df[tracker_df["ai_parsed"] == True])

iter_df = tracker_df[tracker_df["abawd_response_path"].notna()].sample(10)
pbar = tqdm(
    iter_df.iterrows(),
    total=len(iter_df),
    initial=initial_done,
    desc="OpenAI parse progress",
)
for idx, row in pbar:
    abawd_response_path = row["abawd_response_path"]
    state_code = row["state_code"]
    fy = row["fy"]
    pbar.set_description(
        "OpenAI parse progress (current req: {state} - FY{fy})".format(
            state=state_code.upper(), fy=fy
        )
    )

    ai_response_folder, ai_response_json = resolve_ai_response_path(fy, state_code, abawd_response_path)

    if not ai_response_folder.exists():
        ai_response_folder.mkdir(parents=True, exist_ok=True)

    if ai_response_json.exists():
        pbar.set_description("Skipping (already parsed): {pdf}".format(pdf=abawd_response_path))
        tracker_df.loc[idx, "ai_parsed"] = True
        tracker_df.loc[idx, "ai_parsed_response_path"] = ai_response_json
        tracker_df.loc[idx, "ai_parse_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tracker_df.to_csv(WAIVERS_DIR / "10000_pdf_tracker.csv", index=False)
        time.sleep(10)
        continue

    with open(abawd_response_path, "rb") as f:
        abawd_response_data = f.read()

    b64_abawd_response_data = base64.b64encode(abawd_response_data).decode("utf-8")

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "role" : "user",
                "content" : [
                    {
                        "type" : "input_file",
                        "filename" : abawd_response_path,
                        "file_data" : f"data:application/pdf;base64,{b64_abawd_response_data}"
                    },
                    {
                        "type" : "input_text",
                        "text" : EXTRACTION_PROMPT
                    }
                ]
            }
        ],
        instructions=EXTRACTION_INSTRUCTION,
    )
    with open(ai_response_json, "w") as f:
        f.write(response.model_dump_json())

    tracker_df.loc[idx, "ai_parsed"] = True
    tracker_df.loc[idx, "ai_parsed_response_path"] = ai_response_json
    tracker_df.loc[idx, "ai_parse_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tracker_df.to_csv(WAIVERS_DIR / "10000_pdf_tracker.csv", index=False)


    time.sleep(0.1)

