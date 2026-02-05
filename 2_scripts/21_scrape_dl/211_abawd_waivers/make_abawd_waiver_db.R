library(tidyverse)
library(lubridate)

print(getwd())

waivers_folder_path <- file.path(
    "1_data/10_raw/100_usda/1000_abawd_waivers"
)
# 1_data/10_raw/100_usda/1000_abawd_waivers/10000_pdf_tracker.csv

waiver_tracker_db_filepath <- file.path(
    waivers_folder_path, "10000_pdf_tracker.csv"
)

if (!file.exists(waiver_tracker_db_filepath)) {
    print("No existing PDF tracker sheet found. Creating a new one")
    years <- 1997:2025

    waiver_tracker_df <- tibble(
        state_code = c(
            "al", "ak", "az", "ar", "ca", "co", "ct", "dc", "de", "fl", "ga",
            "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma",
            "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny",
            "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx",
            "ut", "vt", "va", "wa", "wv", "wi", "wy"
        ),
        state_name = c(
            "alabama", "alaska", "arizona", "arkansas", "california",
            "colorado", "connecticut", "district of columbia", "delaware",
            "florida", "georgia", "hawaii", "idaho", "illinois", "indiana",
            "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
            "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
            "montana", "nebraska", "nevada", "new hampshire", "new jersey",
            "new mexico", "new york", "north carolina", "north dakota", "ohio",
            "oklahoma", "oregon", "pennsylvania", "rhode island",
            "south carolina", "south dakota", "tennessee", "texas", "utah",
            "vermont", "virginia", "washington", "west virginia", "wisconsin",
            "wyoming"
        ),
        fy = NA
    )
    waiver_tracker_df <- waiver_tracker_df %>%
        group_by(state_code, state_name) %>%
        complete(fy = years) %>%
        ungroup() %>%
        drop_na()
} else {
    print(c(
        "Loading existing PDF tracker sheet from file:\n",
        as.character(waiver_tracker_db_filepath)
    ))
    waiver_tracker_df <- read_csv(as.character(waiver_tracker_db_filepath))
}



find_n_responses <- function(state_code, state_name, fy) {
    FYyy <- paste0("FY", substr(fy, 3, 4))
    fy_folder_path <- file.path(waivers_folder_path, FYyy)
    FYyy_files <- list.files(fy_folder_path)

    state_code_pattern <- paste0("^", state_code)
    state_matches <- str_count(FYyy_files, state_code_pattern)
    return(sum(state_matches))
}

get_response_path <- function(state_code, state_name, fy) {
    FYyy <- paste0("FY", substr(fy, 3, 4))
    fy_folder_path <- file.path(waivers_folder_path, FYyy)
    if (!dir.exists(fy_folder_path)) {
        return(NA_character_)
    }
    # Build regex pattern: start with state_code, end with '.pdf'
    pattern <- paste0("^", state_code, ".*\\.pdf$")
    FYyy_files <- list.files(fy_folder_path)
    matched_files <- FYyy_files[grepl(pattern, FYyy_files, ignore.case = TRUE)]
    if (length(matched_files) > 0) {
        rel_paths_to_return <- paste0(
            "1_data/10_raw/100_usda/1000_abawd_waivers/",
            FYyy, "/", matched_files
        )
        return(rel_paths_to_return)
    } else {
        return(NA_character_)
    }
}

waiver_tracker_updated_df <- waiver_tracker_df %>%
    mutate(
        n_responses_found = mapply(find_n_responses, state_code, state_name, fy),
        abawd_response_path = mapply(get_response_path, state_code, state_name, fy)
    ) %>%
    unnest(abawd_response_path)

write_csv(waiver_tracker_updated_df, waiver_tracker_db_filepath)
