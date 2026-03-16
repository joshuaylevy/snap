import json
import hashlib
import pandas as pd
import pathlib as pl
from tqdm import tqdm

RAW_DATA_DIR = pl.Path("1_data/10_raw/100_usda")
OUTPUT_DIR = RAW_DATA_DIR / "1001_abawd_openai_responses"
WAIVERS_DIR = RAW_DATA_DIR / "1000_abawd_waivers"
JSONS_DIR = OUTPUT_DIR / "1001_abawd_openai_responses"


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


def flatten_for_dataframe(d: dict) -> dict:
    """Convert nested dicts/lists to JSON strings so pd.DataFrame.from_dict works."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = json.dumps(v)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            # Keep lists of dicts as-is (geographic_areas); handled later
            out[k] = v
        else:
            out[k] = v
    return out


def intelligent_response_to_df(intelligent_response: dict) -> pd.DataFrame:
    """Convert intelligent response to dataframe."""
    
    if type(intelligent_response.get('waiver_serial_number')) == list:
        intelligent_response['waiver_serial_number'] = "||".join(intelligent_response['waiver_serial_number'])
    if type(intelligent_response.get('waiver_end_date')) == list:
        intelligent_response['waiver_end_date'] = "||".join(intelligent_response['waiver_end_date'])

    try:
        temp_df = pd.DataFrame.from_dict(intelligent_response)
    except ValueError as e:
        print(f"Error parsing JSON for {ai_response_path}")
        print(e)
        print("Trying with the flatten")
        temp_df = pd.DataFrame.from_dict(flatten_for_dataframe(intelligent_response))

    return temp_df

def assign_waiver_metadata(temp_df: pd.DataFrame, interpret_df_row: pd.Series) -> pd.DataFrame:

    temp_df['state_name'] = interpret_df_row['state_name']
    temp_df['state_code'] = interpret_df_row['state_code']
    temp_df['fy'] = interpret_df_row['fy']
    temp_df['abawd_response_path'] = interpret_df_row['abawd_response_path']
    return temp_df

tracker_df = load_tracker()

if not tracker_cols_check(tracker_df):
    raise Exception("Tracker columns are not correct. Please check the tracker file.")


interpret_df = tracker_df[tracker_df["ai_parsed"] == True]

out_df = pd.DataFrame()

for idx, row in interpret_df.iterrows():
    ai_response_path = row["ai_parsed_response_path"]
    print(ai_response_path)
    with open(ai_response_path, "r") as f:
        ai_response_dict = json.load(f)
    intelligent_response = json.loads(
        ai_response_dict.get("output")[1].get("content")[0].get("text")
    )

    if type(intelligent_response) == list:
        for item_dict in intelligent_response:
            temp_df = intelligent_response_to_df(item_dict)
            temp_df = assign_waiver_metadata(temp_df, row)
            out_df = pd.concat([out_df, temp_df], ignore_index=True)
    else:
        temp_df = intelligent_response_to_df(intelligent_response)
        temp_df = assign_waiver_metadata(temp_df, row)
        out_df = pd.concat([out_df, temp_df], ignore_index=True)





# Expand geographic_areas: each dict key becomes a column, each value the cell entry
# Handle list-of-dicts (take first) or single dict per row
geo_series = out_df["geographic_areas"].apply(
    lambda x: x[0] if isinstance(x, list) and len(x) else (x if isinstance(x, dict) else {})
)
geo_expanded = geo_series.apply(pd.Series)
out_df = pd.concat([out_df.drop(columns=["geographic_areas"]), geo_expanded], axis=1)


out_df.to_csv(OUTPUT_DIR / "10010_abawd_waiver_interpretations.csv", index=False)
