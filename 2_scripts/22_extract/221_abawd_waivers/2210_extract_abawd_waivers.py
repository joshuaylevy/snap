"""
Extract structured data from USDA ABAWD waiver PDFs using the OpenAI Responses API.

Run from project root with:
  conda activate snap && python 2_scripts/22_extract/221_abawd_waivers/2210_extract_abawd_waivers.py [--fys 2019 2020] [--model gpt-5.4-mini]

Requires OPENAI_API_KEY in your environment (.env).
Requires 10001_abawd_waiver_pdf_document_inventory.csv from make_abawd_waiver_db.R.
"""
import argparse
import json
import sys
import time
import base64
import hashlib
from typing import Optional

import pandas as pd
import pathlib as pl
from tqdm import tqdm
from openai import OpenAI
from datetime import datetime
from dotenv import dotenv_values

_SCRIPT_DIR = pl.Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from abawd_extraction_results import (  # noqa: E402
    INVENTORY_CSV,
    document_id_from_path,
    load_inventory,
    run_short_from_run_id,
    upsert_extraction_result,
)


RAW_DATA_DIR = pl.Path("1_data/10_raw/100_usda")
SCRIPT_DIR = pl.Path("2_scripts/22_extract/221_abawd_waivers")
OUTPUT_DIR = RAW_DATA_DIR / "1001_abawd_openai_responses"
MANIFEST_FILENAME = "current_run_manifest.json"

OPENAI_API_KEY = dotenv_values(".env").get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in .env file. Script will not run without it."
    )
client = OpenAI(api_key=OPENAI_API_KEY)

DEFAULT_MODEL = "gpt-5.4-mini"
PROMPT_CACHE_RETENTION = "24h"


def load_prompts() -> tuple[str, str]:
    with open(SCRIPT_DIR / "2210a_extraction_instruction.txt", "r", encoding="utf-8") as f:
        instruction = f.read().strip()
    with open(SCRIPT_DIR / "2210b_extraction_prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read().strip()
    return instruction, prompt


def compute_run_id(instruction: str, prompt: str, model: str) -> str:
    payload = (instruction + "\n" + prompt + "\n" + model).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def instruction_prompt_hashes(instruction: str, prompt: str) -> tuple[str, str]:
    ih = hashlib.sha256(instruction.encode("utf-8")).hexdigest()
    ph = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return ih, ph


def resolve_ai_response_path(
    fy: int,
    state_code: str,
    abawd_response_path: str,
    run_id: str,
) -> tuple[pl.Path, pl.Path]:
    FYyy = "FY{}".format(str(fy)[-2:])
    abawd_response_path_hash = hashlib.sha256(
        abawd_response_path.encode()
    ).hexdigest()
    abawd_response_path_hash_short = abawd_response_path_hash[-8:]
    rs = run_short_from_run_id(run_id)
    ai_response_folder = OUTPUT_DIR / FYyy
    ai_response_json = (
        OUTPUT_DIR
        / FYyy
        / f"{state_code}-fy{fy}-{abawd_response_path_hash_short}-{rs}.json"
    )
    return (ai_response_folder, ai_response_json)


def read_response_provenance(json_path: pl.Path) -> tuple[Optional[str], Optional[str]]:
    """Return (response_id, model) from saved OpenAI response JSON."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("id"), data.get("model")
    except (OSError, json.JSONDecodeError):
        return None, None


def ensure_run_manifest(
    run_id: str,
    model: str,
    instruction_hash: str,
    prompt_hash: str,
) -> None:
    manifest = {
        "run_id": run_id,
        "model": model,
        "instruction_hash": instruction_hash,
        "prompt_hash": prompt_hash,
        "prompt_cache_retention": PROMPT_CACHE_RETENTION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUTPUT_DIR / MANIFEST_FILENAME
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def reconcile_run_with_existing_manifest(
    run_id: str,
    model: str,
    instruction_hash: str,
    prompt_hash: str,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_run_manifest(run_id, model, instruction_hash, prompt_hash)


def build_work_queue(args: argparse.Namespace) -> pd.DataFrame:
    """Load rows from 10001 document inventory only."""
    if not INVENTORY_CSV.exists():
        raise FileNotFoundError(
            f"Missing {INVENTORY_CSV}. Run:\n"
            "  Rscript 2_scripts/21_scrape_dl/211_abawd_waivers/make_abawd_waiver_db.R"
        )
    inv = load_inventory()
    if inv is None or len(inv) == 0:
        raise RuntimeError(f"Document inventory is empty: {INVENTORY_CSV}")
    w = inv.copy()
    w = w[w["abawd_response_path"].notna()]
    if "document_id" not in w.columns:
        w["document_id"] = w["abawd_response_path"].map(
            lambda p: document_id_from_path(p) if pd.notna(p) else pd.NA
        )

    if args.fys is not None:
        fys_set = set(args.fys)
        w = w[w["fy"].isin(fys_set)]
        print(f"Filtering to fiscal years: {sorted(fys_set)}")

    return w


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract ABAWD waiver data via OpenAI Responses API."
    )
    p.add_argument(
        "--fys",
        nargs="*",
        type=int,
        default=None,
        metavar="FY",
        help="Optional fiscal years to process (e.g. 2019 2020). Omit to process all.",
    )
    p.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model (default: {DEFAULT_MODEL})",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.fys is not None and len(args.fys) == 0:
        print("Error: --fys was passed with no years.", file=sys.stderr)
        sys.exit(1)

    instruction, extraction_prompt = load_prompts()
    model = args.model
    run_id = compute_run_id(instruction, extraction_prompt, model)
    instruction_hash, prompt_hash = instruction_prompt_hashes(instruction, extraction_prompt)

    reconcile_run_with_existing_manifest(
        run_id, model, instruction_hash, prompt_hash
    )

    work_df = build_work_queue(args)

    pbar = tqdm(
        work_df.iterrows(),
        total=len(work_df),
        desc="OpenAI parse progress",
    )
    for _, row in pbar:
        abawd_response_path = row["abawd_response_path"]
        state_code = row["state_code"]
        fy = row["fy"]
        doc_id = str(row["document_id"])

        pbar.set_description(
            "OpenAI parse progress (current req: {state} - FY{fy})".format(
                state=str(state_code).upper(), fy=fy
            )
        )

        ai_response_folder, ai_response_json = resolve_ai_response_path(
            fy, state_code, abawd_response_path, run_id
        )

        if not ai_response_folder.exists():
            ai_response_folder.mkdir(parents=True, exist_ok=True)

        if ai_response_json.exists():
            pbar.set_description(
                "Skipping (already parsed): {pdf}".format(pdf=abawd_response_path)
            )
            rid, rmodel = read_response_provenance(ai_response_json)
            upsert_extraction_result(
                doc_id,
                run_id,
                rid,
                rmodel,
                str(ai_response_json),
                status="ok",
            )
            time.sleep(0.1)
            continue

        with open(abawd_response_path, "rb") as f:
            abawd_response_data = f.read()

        b64_abawd_response_data = base64.b64encode(abawd_response_data).decode("utf-8")

        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": extraction_prompt,
                        },
                        {
                            "type": "input_file",
                            "filename": abawd_response_path,
                            "file_data": f"data:application/pdf;base64,{b64_abawd_response_data}",
                        },
                    ],
                }
            ],
            instructions=instruction,
            prompt_cache_key=run_id,
            prompt_cache_retention=PROMPT_CACHE_RETENTION,
        )

        with open(ai_response_json, "w", encoding="utf-8") as f:
            f.write(response.model_dump_json())

        rid = response.id
        rmodel = getattr(response, "model", None) or model

        upsert_extraction_result(
            doc_id,
            run_id,
            rid,
            rmodel,
            str(ai_response_json),
            status="ok",
        )

        time.sleep(0.1)


if __name__ == "__main__":
    main()
