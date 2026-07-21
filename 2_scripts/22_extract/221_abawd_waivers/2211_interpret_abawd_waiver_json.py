import json
import sys
from pathlib import Path

import pandas as pd
import pathlib as pl

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from abawd_extraction_results import (  # noqa: E402
    INVENTORY_CSV,
    RESULTS_CSV,
    load_inventory,
    load_results_for_run,
)

RAW_DATA_DIR = pl.Path("1_data/10_raw/100_usda")
OUTPUT_DIR = RAW_DATA_DIR / "1001_abawd_openai_responses"
MANIFEST_FILENAME = "current_run_manifest.json"

DOC_LEVEL_KEY_ALIASES = {
    "document_type": ["document_type"],
    "waiver_serial_number": ["waiver_serial_number"],
    "type_of_request": ["type_of_request"],
    "primary_regulation_citation": ["primary_regulation_citation"],
    "state": ["state"],
    "fns_region": ["fns_region", "region"],
    "alt_procedures_desc": ["alt_procedures_desc", "description_of_proposed_alternative_procedures"],
    "action_reason_approval_denial": ["action_reason_approval_denial", "action_and_reason_for_approval_or_denial"],
    "reg_leg_action_basis": ["reg_leg_action_basis", "regulatory_or_legislative_basis_for_action"],
    "conditions_and_reasons": ["conditions_and_reasons"],
    "info_required_for_extension": ["info_required_for_extension", "information_required_for_extension"],
    "expiration_date": ["expiration_date", "expiration_date_text"],
    "limits_on_regional_office_approvals": [
        "limits_on_regional_office_approvals",
        "limitation_on_regional_office_approval_of_like_requests",
    ],
    "quality_control_procedures": ["quality_control_procedures"],
    "date_national_office_action": ["date_national_office_action", "date_of_national_office_action", "response_date"],
    "date_state_request": ["date_state_request", "date_of_state_agency_request", "application_date"],
    "date_ro_transmittal_request": [
        "date_ro_transmittal_request",
        "date_of_regional_office_transmittal_of_request",
    ],
    "date_ro_transmittal_response": [
        "date_ro_transmittal_response",
        "date_ro_transmittal_resposne",
        "date_of_regional_office_transmittal_of_response_to_state_agency",
    ],
    "implementation_date_actual": [
        "implementation_date_actual",
        "implementation_date_actiona",
        "actual_implementation_date",
    ],
    "state_official_name": ["state_official_name"],
    "fns_official_name": ["fns_official_name"],
    "fns_official_title": ["fns_official_title"],
    "response_date": ["response_date", "date_of_national_office_action"],
    "number_of_groups": ["number_of_groups"],
    "non_conforming_document": ["non_conforming_document"],
    "non_conforming_reason": ["non_conforming_reason"],
}

GROUP_LEVEL_KEY_ALIASES = {
    "criterion_code_normalized": ["criterion_code_normalized", "rule_cited"],
    "criterion_other_explanation": ["criterion_other_explanation", "rule_other_explanation"],
    "criteria_summary_text": ["criteria_summary_text"],
    "national_unemployment_rate_cited": ["national_unemployment_rate_cited"],
    "data_collection_date": ["data_collection_date"],
    "local_unemployment_time_window": ["local_unemployment_time_window"],
    "group_action": ["group_action", "status"],
    "status": ["status", "group_action"],
    "waiver_effective_date": ["waiver_effective_date"],
    "waiver_expiry_date": ["waiver_expiry_date"],
    "waiver_duration_text": ["waiver_duration_text", "waiver_duration"],
    "waiver_duration": ["waiver_duration", "waiver_duration_text"],
    "applied_waiver_start_date": ["applied_waiver_start_date"],
    "applied_waiver_end_date": ["applied_waiver_end_date"],
    "applied_waiver_duration_text": ["applied_waiver_duration_text", "applied_waiver_duration"],
    "applied_waiver_duration": ["applied_waiver_duration", "applied_waiver_duration_text"],
}


def load_current_run_id() -> str:
    manifest_path = OUTPUT_DIR / MANIFEST_FILENAME
    if not manifest_path.exists():
        print(
            f"Missing {manifest_path}. Run 2210_extract_abawd_waivers.py first.",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    run_id = manifest.get("run_id")
    if not run_id:
        print("Manifest has no run_id.", file=sys.stderr)
        sys.exit(1)
    return run_id


def normalize_serial_number(val):
    """Convert waiver_serial_number list to string for CSV."""
    if isinstance(val, list):
        return "||".join(str(x) for x in val) if val else None
    return val


def first_non_null(source: dict, keys: list[str]):
    """Return first non-null value from an ordered list of keys."""
    for key in keys:
        if key in source and source.get(key) is not None:
            return source.get(key)
    return None


def extract_aliased_fields(source: dict, aliases: dict[str, list[str]]) -> dict:
    """Build a flat dict using alias lists for backward-compatible parsing."""
    out = {}
    for out_key, in_keys in aliases.items():
        out[out_key] = first_non_null(source, in_keys)
    return out


def flatten_time_window(obj):
    """Turn local_unemployment_time_window object into flat keys for one row."""
    if obj is None or not isinstance(obj, dict):
        return {
            "local_unemployment_window_type": None,
            "local_unemployment_start_date": None,
            "local_unemployment_end_date": None,
            "local_unemployment_description": None,
        }
    return {
        "local_unemployment_window_type": obj.get("window_type"),
        "local_unemployment_start_date": obj.get("start_date"),
        "local_unemployment_end_date": obj.get("end_date"),
        "local_unemployment_description": obj.get("description"),
    }


def groups_to_area_rows(intelligent_response: dict) -> list[dict]:
    """
    Convert one extraction response (document-level + groups) into a list of
    area-level rows (one row per geographic unit).
    """
    groups = intelligent_response.get("groups") or []
    request_level = intelligent_response.get("request_level")
    doc_source = request_level if isinstance(request_level, dict) else intelligent_response
    doc = extract_aliased_fields(doc_source, DOC_LEVEL_KEY_ALIASES)

    if "waiver_serial_number" in doc and doc["waiver_serial_number"] is not None:
        doc["waiver_serial_number"] = normalize_serial_number(doc["waiver_serial_number"])

    rows = []
    for grp in groups:
        geographic_units = grp.get("geographic_units") or []
        group_flat = extract_aliased_fields(grp, GROUP_LEVEL_KEY_ALIASES)
        time_window_flat = flatten_time_window(group_flat.pop("local_unemployment_time_window", None))
        for unit in geographic_units:
            row = {
                **doc,
                "geographic_unit_name": unit.get("name"),
                "geographic_unit_area_type": unit.get("area_type"),
                **group_flat,
                **time_window_flat,
            }
            rows.append(row)
    return rows


def assign_waiver_metadata(rows: list[dict], interpret_df_row: pd.Series) -> list[dict]:
    """Add tracker metadata and OpenAI provenance to each row."""
    meta = {
        "state_name": interpret_df_row["state_name"],
        "state_code": interpret_df_row["state_code"],
        "fy": interpret_df_row["fy"],
        "abawd_response_path": interpret_df_row["abawd_response_path"],
        "ai_extraction_run_id": interpret_df_row.get("ai_extraction_run_id"),
        "ai_openai_response_id": interpret_df_row.get("ai_openai_response_id"),
        "ai_openai_model": interpret_df_row.get("ai_openai_model"),
        "ai_parsed_response_path": interpret_df_row.get("ai_parsed_response_path"),
    }
    for r in rows:
        r.update(meta)
    return rows


def interpret_from_results_and_inventory(run_id: str) -> list[dict]:
    """Primary path: 10011 + 10001 join."""
    results_df = load_results_for_run(run_id)
    inv_df = load_inventory()
    if results_df.empty or inv_df is None or len(inv_df) == 0:
        return []

    merged = results_df.merge(
        inv_df,
        on="document_id",
        how="left",
        suffixes=("", "_inv"),
    )
    all_rows: list[dict] = []

    for _, row in merged.iterrows():
        ai_response_path = row["response_json_path"]
        print(ai_response_path)
        row = row.copy()
        row["ai_parsed_response_path"] = row["response_json_path"]
        row["ai_extraction_run_id"] = run_id
        row["ai_openai_response_id"] = row.get("openai_response_id")
        row["ai_openai_model"] = row.get("openai_model")

        try:
            with open(ai_response_path, "r") as f:
                ai_response_dict = json.load(f)
        except OSError as e:
            print(f"  Skip: cannot read {ai_response_path}: {e}")
            continue

        output = ai_response_dict.get("output") or []
        if len(output) < 1:
            print(f"  Skip: output has {len(output)} element(s)")
            continue
        # Responses JSON shape can vary; our saved artifacts sometimes store the
        # content at output[0] (single element) rather than output[1].
        output_elem = output[1] if len(output) > 1 else output[0]
        content = output_elem.get("content") or []
        if not content:
            print(f"  Skip: no content")
            continue
        text = content[0].get("text")
        if not text:
            continue
        intelligent_response = json.loads(text)

        if isinstance(intelligent_response, list):
            for item in intelligent_response:
                area_rows = groups_to_area_rows(item)
                area_rows = assign_waiver_metadata(area_rows, row)
                all_rows.extend(area_rows)
        else:
            area_rows = groups_to_area_rows(intelligent_response)
            area_rows = assign_waiver_metadata(area_rows, row)
            all_rows.extend(area_rows)

    return all_rows


def main():
    run_id = load_current_run_id()

    if not INVENTORY_CSV.exists():
        print(
            f"Missing {INVENTORY_CSV}. Run:\n"
            "  Rscript 2_scripts/21_scrape_dl/211_abawd_waivers/make_abawd_waiver_db.R",
            file=sys.stderr,
        )
        sys.exit(1)
    if not RESULTS_CSV.exists():
        print(
            f"Missing {RESULTS_CSV}. Run 2210_extract_abawd_waivers.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    results_for_run = load_results_for_run(run_id)
    inv = load_inventory()
    if inv is None or len(inv) == 0:
        print(f"Document inventory is empty: {INVENTORY_CSV}", file=sys.stderr)
        sys.exit(1)
    if len(results_for_run) == 0:
        print(
            f"No rows in {RESULTS_CSV} for current run_id from manifest. "
            "Run 2210_extract_abawd_waivers.py for this prompt/model.",
            file=sys.stderr,
        )
        sys.exit(1)

    all_rows = interpret_from_results_and_inventory(run_id)

    out_df = pd.DataFrame(all_rows)
    out_df.to_csv(OUTPUT_DIR / "10010_abawd_waiver_interpretations.csv", index=False)


if __name__ == "__main__":
    main()
