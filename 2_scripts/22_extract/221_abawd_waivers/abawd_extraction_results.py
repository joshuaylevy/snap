"""
Shared helpers for ABAWD OpenAI extraction results (10011 CSV) and document_id hashing.

Used by 2210_extract_abawd_waivers.py and 2211_interpret_abawd_waiver_json.py.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

import pandas as pd
import pathlib as pl


RAW_DATA_DIR = pl.Path("1_data/10_raw/100_usda")
WAIVERS_DIR = RAW_DATA_DIR / "1000_abawd_waivers"
OUTPUT_DIR = RAW_DATA_DIR / "1001_abawd_openai_responses"

INVENTORY_CSV = WAIVERS_DIR / "10001_abawd_waiver_pdf_document_inventory.csv"
RESULTS_CSV = OUTPUT_DIR / "10011_abawd_openai_extraction_results.csv"


def document_id_from_path(abawd_response_path: str) -> str:
    """SHA256 hex of UTF-8 path string; must match R digest(..., algo='sha256', serialize=FALSE)."""
    return hashlib.sha256(str(abawd_response_path).encode("utf-8")).hexdigest()


def run_short_from_run_id(run_id: str) -> str:
    return run_id[:8]


RESULT_COLUMNS = [
    "document_id",
    "run_id",
    "run_short",
    "openai_response_id",
    "openai_model",
    "response_json_path",
    "extracted_at",
    "status",
]


def upsert_extraction_result(
    document_id: str,
    run_id: str,
    openai_response_id: Optional[str],
    openai_model: Optional[str],
    response_json_path: str,
    status: str = "ok",
) -> None:
    """One row per (document_id, run_id); replaces existing row for that key."""
    run_short = run_short_from_run_id(run_id)
    row = {
        "document_id": document_id,
        "run_id": run_id,
        "run_short": run_short,
        "openai_response_id": openai_response_id,
        "openai_model": openai_model,
        "response_json_path": response_json_path,
        "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if RESULTS_CSV.exists():
        df = pd.read_csv(RESULTS_CSV)
        for c in RESULT_COLUMNS:
            if c not in df.columns:
                df[c] = pd.NA
        mask = (df["document_id"].astype(str) == str(document_id)) & (
            df["run_id"].astype(str) == str(run_id)
        )
        df = df[~mask]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df = df[RESULT_COLUMNS]
    df.to_csv(RESULTS_CSV, index=False)


def load_inventory() -> Optional[pd.DataFrame]:
    if not INVENTORY_CSV.exists():
        return None
    df = pd.read_csv(INVENTORY_CSV)
    if "document_id" not in df.columns and "abawd_response_path" in df.columns:
        df["document_id"] = df["abawd_response_path"].map(
            lambda p: document_id_from_path(p) if pd.notna(p) else pd.NA
        )
    return df


def load_results_for_run(run_id: str) -> pd.DataFrame:
    if not RESULTS_CSV.exists():
        return pd.DataFrame(columns=RESULT_COLUMNS)
    df = pd.read_csv(RESULTS_CSV)
    if df.empty or "run_id" not in df.columns:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return df[df["run_id"].astype(str) == str(run_id)].copy()
