library(tidyverse)
library(lubridate)
library(digest)

print(getwd())

waivers_folder_path <- file.path(
    "1_data/10_raw/100_usda/1000_abawd_waivers"
)
waiver_document_inventory_filepath <- file.path(
    waivers_folder_path, "10001_abawd_waiver_pdf_document_inventory.csv"
)

years <- 1997:2025

waiver_grid_df <- tibble(
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
) %>%
    group_by(state_code, state_name) %>%
    complete(fy = years) %>%
    ungroup() %>%
    drop_na()

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

waiver_tracker_updated_df <- waiver_grid_df %>%
    mutate(
        n_responses_found = mapply(find_n_responses, state_code, state_name, fy),
        abawd_response_path = mapply(get_response_path, state_code, state_name, fy)
    ) %>%
    unnest(abawd_response_path)

waiver_tracker_updated_df <- waiver_tracker_updated_df %>%
    mutate(
        document_id = map_chr(abawd_response_path, function(p) {
            if (is.na(p)) {
                return(NA_character_)
            }
            digest::digest(p, algo = "sha256", serialize = FALSE)
        })
    )

waiver_document_inventory_df <- waiver_tracker_updated_df %>%
    select(
        document_id,
        state_code,
        state_name,
        fy,
        abawd_response_path,
        n_responses_found
    )

write_csv(waiver_document_inventory_df, waiver_document_inventory_filepath)
