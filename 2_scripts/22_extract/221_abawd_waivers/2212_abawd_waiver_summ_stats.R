library(tidyverse)
library(maps)
library(gt)

print(getwd())

openai_responses_folder_path <- file.path(
    "1_data/10_raw/100_usda/1001_abawd_openai_responses"
)

openai_responses_filepath <- file.path(
    openai_responses_folder_path, "10010_abawd_waiver_interpretations.csv"
)

data_in <- read_csv(openai_responses_filepath, show_col_types = FALSE)

# Map state_code to map region (lowercase state name for map_data("state"))
state_abb_to_region <- c(
    setNames(tolower(state.name), tolower(state.abb)),
    "dc" = "district of columbia"
)

# ------------------------------------------------------------------------------
# State-level summaries: unique counties (areas) ever approved/denied per state
# ------------------------------------------------------------------------------
approvals_by_state <- data_in %>%
    filter(status == "approved") %>%
    distinct(state_code, name) %>%
    count(state_code, name = "n_counties") %>%
    mutate(region = state_abb_to_region[tolower(state_code)])

denials_by_state <- data_in %>%
    filter(status == "denied") %>%
    distinct(state_code, name) %>%
    count(state_code, name = "n_counties") %>%
    mutate(region = state_abb_to_region[tolower(state_code)])

# ------------------------------------------------------------------------------
# 1. Choropleth: total approvals by state (unique counties)
# ------------------------------------------------------------------------------
states_map <- map_data("state")
states_approvals <- states_map %>%
    left_join(approvals_by_state, by = "region")

p1 <- ggplot(states_approvals, aes(long, lat, group = group)) +
    geom_polygon(aes(fill = n_counties), color = "white", linewidth = 0.2) +
    scale_fill_viridis_c(option = "plasma", na.value = "grey90") +
    labs(
        title = "ABAWD Waiver Approvals by State",
        subtitle = "Total number of unique counties (or equivalent areas) that have ever received a waiver",
        fill = "Count"
    ) +
    theme_personal() +
    theme(
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank(),
        panel.grid = element_blank()
    ) +
    coord_fixed(1.3)

print(p1)

# ------------------------------------------------------------------------------
# 2. Choropleth: total denials by state
# ------------------------------------------------------------------------------
states_denials <- states_map %>%
    left_join(denials_by_state, by = "region")

p2 <- ggplot(states_denials, aes(long, lat, group = group)) +
    geom_polygon(aes(fill = n_counties), color = "white", linewidth = 0.2) +
    scale_fill_viridis_c(option = "cividis", na.value = "grey90") +
    labs(
        title = "ABAWD Waiver Denials by State",
        subtitle = "Total number of unique counties (or equivalent areas) that have ever been denied",
        fill = "Count"
    ) +
    theme_personal() +
    theme(
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank(),
        panel.grid = element_blank()
    ) +
    coord_fixed(1.3)

print(p2)

# ------------------------------------------------------------------------------
# 3. Bar chart: counts by approval reason + total denials
# ------------------------------------------------------------------------------
approval_reason_counts <- data_in %>%
    filter(status == "approved") %>%
    mutate(reason = coalesce(exemption_type, "unknown")) %>%
    count(reason, name = "n")

denial_count <- tibble(
    reason = "Denials (no reason)",
    n = sum(data_in$status == "denied", na.rm = TRUE)
)

bar_data <- bind_rows(approval_reason_counts, denial_count) %>%
    mutate(
        reason = fct_reorder(reason, n, .desc = TRUE),
        category = if_else(reason == "Denials (no reason)", "Denials", "Approval reason")
    )

p3 <- ggplot(bar_data, aes(x = fct_rev(reason), y = n, fill = category)) +
    geom_col() +
    scale_fill_manual(values = c("Approval reason" = "steelblue", "Denials" = "coral2"), guide = "none") +
    labs(
        title = "ABAWD Waivers by Approval Reason and Denials",
        x = "Reason for approval / Denials",
        y = "Count"
    ) +
    theme_personal() +
    coord_flip()

print(p3)

# ------------------------------------------------------------------------------
# 4. Line chart: counties with waiver by FY, geom_step, total + by reason
# ------------------------------------------------------------------------------
county_fy_reason <- data_in %>%
    filter(status == "approved") %>%
    mutate(reason = coalesce(exemption_type, "unknown")) %>%
    distinct(fy, state_code, name, reason)

total_by_fy <- county_fy_reason %>%
    distinct(fy, state_code, name) %>%
    count(fy, name = "n_counties") %>%
    mutate(series = "Total")

by_reason_fy <- county_fy_reason %>%
    count(fy, reason, name = "n_counties") %>%
    mutate(series = reason)

all_fy <- min(county_fy_reason$fy, na.rm = TRUE):max(county_fy_reason$fy, na.rm = TRUE)
line_data <- bind_rows(total_by_fy, by_reason_fy) %>%
    complete(fy = all_fy, series, fill = list(n_counties = 0)) %>%
    arrange(series, fy)

p4 <- ggplot(line_data, aes(x = fy, y = n_counties, color = series, group = series)) +
    geom_step(linewidth = 0.8) +
    scale_color_viridis_d(option = "turbo", end = 0.9) +
    labs(
        title = "Counties Receiving ABAWD Waivers by Fiscal Year",
        subtitle = "Step plot: total and by approval reason",
        x = "Fiscal year",
        y = "Number of counties",
        color = "Series"
    ) +
    theme_personal()

print(p4)

# ------------------------------------------------------------------------------
# 5. Table: annual FY summary stats on approvals
# ------------------------------------------------------------------------------
annual_approvals <- data_in %>%
    filter(status == "approved") %>%
    distinct(fy, state_code, name) %>%
    count(fy, state_code, name = "counties_in_state")

annual_summary <- annual_approvals %>%
    group_by(fy) %>%
    summarise(
        n_states = n(),
        n_counties = sum(counties_in_state),
        mean_counties_per_state = mean(counties_in_state),
        median_counties_per_state = median(counties_in_state),
        min_counties = min(counties_in_state),
        max_counties = max(counties_in_state),
        .groups = "drop"
    )

tbl <- annual_summary %>%
    gt() %>%
    fmt_number(
        columns = c(mean_counties_per_state, median_counties_per_state),
        decimals = 3
    ) %>%
    cols_label(
        fy = "Fiscal year",
        n_states = "Unique states",
        n_counties = "Counties",
        mean_counties_per_state = "Mean counties/state",
        median_counties_per_state = "Median counties/state",
        min_counties = "Min counties",
        max_counties = "Max counties"
    )

print(tbl)
