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
SCRIPT_DIR = pl.Path("2_scripts/22_extract/221_abawd_waivers")
OUTPUT_DIR = RAW_DATA_DIR / "1001_abawd_openai_responses"
WAIVERS_DIR = RAW_DATA_DIR / "1000_abawd_waivers"
RESPONSES_API_URL = "https://api.openai.com/v1/responses"
OPENAI_API_KEY = dotenv_values(".env")["OPENAI_API_KEY"]
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file. Script will not run without it. Exiting in 10 seconds.")
client = OpenAI(api_key=OPENAI_API_KEY)

# Load prompts from .txt files next to this script
with open(SCRIPT_DIR / "2210a_extraction_instruction.txt", "r", encoding="utf-8") as f:
    EXTRACTION_INSTRUCTION = f.read().strip()
with open(SCRIPT_DIR / "2210b_extraction_prompt.txt", "r", encoding="utf-8") as f:
    EXTRACTION_PROMPT = f.read().strip()


def load_tracker() -> pd.DataFrame:
    """Load tracker and return rows with valid PDF paths."""
    df = pd.read_csv(WAIVERS_DIR / "10000_pdf_tracker.csv")
    return df


def tracker_cols_check(df: pd.DataFrame) -> bool:
    existing_cols = df.columns.tolist()
    required_cols = ["ai_parsed", "ai_parsed_response_path", "ai_parse_timestamp"]
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

iter_df = tracker_df[tracker_df["abawd_response_path"].notna()]
pbar = tqdm(
    iter_df.iterrows(),
    total=len(iter_df),
    # initial=initial_done,
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
        # pandas may store this column as the "string" dtype; store paths as plain strings
        tracker_df.loc[idx, "ai_parsed_response_path"] = str(ai_response_json)
        tracker_df.loc[idx, "ai_parse_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tracker_df.to_csv(WAIVERS_DIR / "10000_pdf_tracker.csv", index=False)
        time.sleep(0.1)
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
    # pandas may store this column as the "string" dtype; store paths as plain strings
    tracker_df.loc[idx, "ai_parsed_response_path"] = str(ai_response_json)
    tracker_df.loc[idx, "ai_parse_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tracker_df.to_csv(WAIVERS_DIR / "10000_pdf_tracker.csv", index=False)


    time.sleep(0.1)

