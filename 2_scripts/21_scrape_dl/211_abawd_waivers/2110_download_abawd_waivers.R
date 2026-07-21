#!/usr/bin/env Rscript
# Download SNAP ABAWD waiver PDFs from USDA website
# For FY2017-FY2025 only

library(rvest)
library(xml2)
library(httr)
library(dplyr)
library(stringr)

# Assume script is run from project root
# Use absolute paths based on current working directory
project_root <- normalizePath(getwd())

# Create output directory with absolute path
output_dir <- file.path(project_root, "1_data", "10_raw", "100_usda", "1000_abawd_waivers")
output_dir <- normalizePath(output_dir, mustWork = FALSE)

if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
  print(paste("Created output directory:", output_dir))
} else {
  print(paste("Using output directory:", output_dir))
}

# Verify directory exists and is writable
if (!dir.exists(output_dir)) {
  stop(paste("Failed to create output directory:", output_dir))
}
print(paste("Output directory (absolute):", output_dir))
print(paste("Project root:", project_root))

# Base URL
base_url <- "https://www.fns.usda.gov"

# Pages to scrape for FY1997-FY2025
# Structure based on official USDA FNS ABAWD Waiver PDFs landing page and annual subpages:
#   https://www.fns.usda.gov/snap/abawd/waivers
# Documents are organized into fiscal year batches. The earliest ABAWD waivers go back to 1997.

pages <- list(
  "1997-1999" = list(
    url = "https://www.fns.usda.gov/snap/abawd/waivers/1997-1999",
    target_years = 1997:1999
  ),
  "2000-2004" = list(
    url = "https://www.fns.usda.gov/snap/abawd/waivers/2000-2004",
    target_years = 2000:2004
  ),
  "2005-2009" = list(
    url = "https://www.fns.usda.gov/snap/abawd/waivers/2005-2009",
    target_years = 2005:2009
  ),
  "2010-2014" = list(
    url = "https://www.fns.usda.gov/snap/abawd/waivers/2010-2014",
    target_years = 2010:2014
  ),
  "2015-2019" = list(
    url = "https://www.fns.usda.gov/snap/abawd/waivers/2015-2019",
    target_years = 2015:2019
  ),
  "2020-2024" = list(
    url = "https://www.fns.usda.gov/snap/abawd/waivers/2020-2024",
    target_years = 2020:2024
  ),
  "2025-2029" = list(
    url = "https://www.fns.usda.gov/snap/abawd/waivers/2025-2029",
    target_years = 2025
  )
)

# All years we want to download (FY1997-FY2025)
all_target_years <- 1997:2025

print("Starting download of ABAWD waiver PDFs for FY1997-FY2025...")

all_pdfs <- list()

# Function to extract PDF links from a page
extract_pdf_links <- function(url) {
  print(paste("Scraping:", url))
  
  # Read the page with retries
  page <- NULL
  attempts <- 0
  while (is.null(page) && attempts < 3) {
    attempts <- attempts + 1
    tryCatch({
      page <- read_html(url)
    }, error = function(e) {
      print(paste("Attempt", attempts, "failed:", e$message))
      if (attempts < 3) {
        Sys.sleep(2)
      }
    })
  }
  
  if (is.null(page)) {
    warning(paste("Failed to read page:", url))
    return(data.frame())
  }
  
  # Find all links
  links <- page %>%
    html_nodes("a") %>%
    html_attr("href")
  
  # Find all text that might indicate PDFs
  link_texts <- page %>%
    html_nodes("a") %>%
    html_text()
  
  # Filter for PDF links
  pdf_links <- data.frame(
    href = links,
    text = link_texts,
    stringsAsFactors = FALSE
  ) %>%
    filter(
      !is.na(href),
      str_detect(tolower(href), "\\.pdf$") |
        str_detect(tolower(href), "pdf")
    )
  
  # Make absolute URLs
  pdf_links <- pdf_links %>%
    mutate(
      url = if_else(
        str_detect(href, "^http"),
        href,
        paste0(base_url, if_else(str_detect(href, "^/"), "", "/"), href)
      )
    )
  
  return(pdf_links)
}

# Function to extract fiscal year from text or URL
extract_fiscal_year <- function(text, url) {
  # Try to extract 4-digit year from various patterns
  # Valid range: 1997-2025
  text_lower <- tolower(text)
  url_lower <- tolower(url)
  
  # Look for FY followed by 4 digits (e.g., "fy2025", "fy 2025", "fy-2025")
  year_match <- str_extract(text_lower, "fy[\\s_-]*\\d{4}")
  if (!is.na(year_match)) {
    year_str <- str_extract(year_match, "\\d{4}")
    if (!is.na(year_str)) {
      year <- as.numeric(year_str)
      if (year >= 1997 && year <= 2025) {
        return(year)
      }
    }
  }
  
  # Look for 4-digit year in text (1997-2025 range)
  year_match <- str_extract(text_lower, "19[89][0-9]|20[0-2][0-9]")
  if (!is.na(year_match)) {
    year <- as.numeric(year_match)
    if (year >= 1997 && year <= 2025) {
      return(year)
    }
  }
  
  # Look for FY followed by 4 digits in URL
  year_match <- str_extract(url_lower, "fy[\\s_-]*\\d{4}")
  if (!is.na(year_match)) {
    year_str <- str_extract(year_match, "\\d{4}")
    if (!is.na(year_str)) {
      year <- as.numeric(year_str)
      if (year >= 1997 && year <= 2025) {
        return(year)
      }
    }
  }
  
  # Look for 4-digit year in URL
  year_match <- str_extract(url_lower, "19[89][0-9]|20[0-2][0-9]")
  if (!is.na(year_match)) {
    year <- as.numeric(year_match)
    if (year >= 1997 && year <= 2025) {
      return(year)
    }
  }
  
  # Look in filename if URL has one
  url_parts <- strsplit(url, "/")[[1]]
  if (length(url_parts) > 0) {
    filename <- url_parts[length(url_parts)]
    filename_lower <- tolower(filename)
    
    # Try FY pattern first
    year_match <- str_extract(filename_lower, "fy[\\s_-]*\\d{4}")
    if (!is.na(year_match)) {
      year_str <- str_extract(year_match, "\\d{4}")
      if (!is.na(year_str)) {
        year <- as.numeric(year_str)
        if (year >= 1997 && year <= 2025) {
          return(year)
        }
      }
    }
    
    # Try 4-digit year
    year_match <- str_extract(filename_lower, "19[89][0-9]|20[0-2][0-9]")
    if (!is.na(year_match)) {
      year <- as.numeric(year_match)
      if (year >= 1997 && year <= 2025) {
        return(year)
      }
    }
  }
  
  return(NA)
}

# Function to get FY folder name (FYXX format)
get_fy_folder <- function(year) {
  if (is.na(year)) {
    return(NA)
  }
  # Extract last two digits
  last_two <- substr(as.character(year), 3, 4)
  return(paste0("FY", last_two))
}

# Function to check if PDF is for target years
is_target_year <- function(text, url, page_target_years) {
  # Check for fiscal year mentions in text or URL
  text_lower <- tolower(text)
  url_lower <- tolower(url)
  
  # Look for patterns matching the target years for this page
  for (year in page_target_years) {
    # Various patterns to match fiscal years
    patterns <- c(
      paste0("fy", year),
      paste0("fiscal year ", year),
      paste0("fy ", year),
      paste0("fy-", year),
      paste0("fy_", year),
      paste0("20", substr(year, 3, 4)),  # e.g., "17" for 2017
      paste0("/", year, "/"),
      paste0("_", year, "_"),
      paste0("-", year, "-"),
      paste0("_", year, "\\."),
      paste0("-", year, "\\.")
    )
    
    for (pattern in patterns) {
      if (str_detect(text_lower, pattern) || str_detect(url_lower, pattern)) {
        return(TRUE)
      }
    }
  }
  
  # If no explicit year match, but we're on a page with limited years,
  # we might want to include it (but be conservative)
  # For now, return FALSE if no year match
  return(FALSE)
}

# Scrape each page
for (page_name in names(pages)) {
  page_info <- pages[[page_name]]
  url <- page_info$url
  page_target_years <- page_info$target_years
  
  print(paste("Processing page:", page_name, "- Target years:", paste(page_target_years, collapse = ", ")))
  
  pdf_links <- extract_pdf_links(url)
  
  if (nrow(pdf_links) > 0) {
    print(paste("Found", nrow(pdf_links), "potential PDF links on", page_name, "page"))
    
    # Filter for target years for this specific page
    pdf_links_filtered <- pdf_links %>%
      rowwise() %>%
      mutate(is_target = is_target_year(text, url, page_target_years)) %>%
      ungroup() %>%
      filter(is_target)
    
    if (nrow(pdf_links_filtered) > 0) {
      pdf_links_filtered$page <- page_name
      pdf_links_filtered$page_target_years <- paste(page_target_years, collapse = "-")
      all_pdfs[[page_name]] <- pdf_links_filtered
      print(paste("  → Filtered to", nrow(pdf_links_filtered), "PDFs for target years"))
    } else {
      print(paste("  → No PDFs matched target years for", page_name, "page"))
      # Show a few examples of what we found
      sample_links <- pdf_links %>% head(3)
      if (nrow(sample_links) > 0) {
        print("  Sample links found (not matching target years):")
        for (j in 1:nrow(sample_links)) {
          print(paste("    -", sample_links$text[j], ":", sample_links$href[j]))
        }
      }
    }
  } else {
    print(paste("No PDFs found on", page_name, "page"))
  }
  
  # Be polite - wait between requests
  Sys.sleep(2)
}

# Combine all PDFs
if (length(all_pdfs) > 0) {
  all_pdfs_df <- bind_rows(all_pdfs)
  
  # Remove duplicates
  all_pdfs_df <- all_pdfs_df %>%
    distinct(url, .keep_all = TRUE)
  
  print(paste("\nTotal unique PDFs to download:", nrow(all_pdfs_df)))
  
  # Download each PDF
  downloaded <- 0
  failed <- 0
  
  for (i in 1:nrow(all_pdfs_df)) {
    pdf_url <- all_pdfs_df$url[i]
    pdf_text <- all_pdfs_df$text[i]
    
    # Extract fiscal year from PDF
    fiscal_year <- extract_fiscal_year(pdf_text, pdf_url)
    if (is.na(fiscal_year)) {
      print(paste("Warning: Could not extract fiscal year for:", pdf_url))
      print(paste("  Text:", pdf_text))
      # Skip this file if we can't determine the year
      next
    }
    
    # Get FY folder name (e.g., FY25 for 2025)
    fy_folder <- get_fy_folder(fiscal_year)
    fy_dir <- file.path(output_dir, fy_folder)
    
    # Create FY folder if it doesn't exist
    if (!dir.exists(fy_dir)) {
      dir.create(fy_dir, recursive = TRUE)
      print(paste("Created FY folder:", fy_dir))
    }
    
    # Create a safe filename
    filename <- basename(URLdecode(pdf_url))
    # If no filename in URL, create one from text
    if (filename == "" || !str_detect(tolower(filename), "\\.pdf$")) {
      filename <- paste0("abawd_waiver_", fiscal_year, "_", i, ".pdf")
      filename <- str_replace_all(filename, "[^A-Za-z0-9._-]", "_")
    }
    
    filepath <- file.path(fy_dir, filename)
    
    # Skip if already downloaded
    if (file.exists(filepath)) {
      print(paste("Skipping (already exists):", fy_folder, "/", filename))
      next
    }
    
    print(paste("Downloading", i, "of", nrow(all_pdfs_df), ":", fy_folder, "/", filename))
    print(paste("  Fiscal Year:", fiscal_year))
    print(paste("  URL:", pdf_url))
    print(paste("  Filepath:", filepath))
    
    # Download with retries
    success <- FALSE
    attempts <- 0
    while (!success && attempts < 3) {
      attempts <- attempts + 1
      tryCatch({
        # download.file returns 0 on success, non-zero on failure
        # Try libcurl first, fall back to auto if needed
        download_method <- "auto"
        if (capabilities("libcurl")) {
          download_method <- "libcurl"
        }
        
        result <- download.file(
          url = pdf_url,
          destfile = filepath,
          mode = "wb",
          method = download_method,
          quiet = FALSE  # Set to FALSE to see download progress
        )
        
        # Check return code
        if (result != 0) {
          print(paste("  ✗ download.file returned error code:", result))
          if (file.exists(filepath)) file.remove(filepath)
        } else {
          # Check if file was actually downloaded and has content
          if (file.exists(filepath)) {
            file_size <- file.info(filepath)$size
            if (file_size > 0) {
              success <- TRUE
              downloaded <- downloaded + 1
              print(paste("  ✓ Downloaded:", filename, "(", file_size, "bytes )"))
            } else {
              print(paste("  ✗ File downloaded but is empty (0 bytes)"))
              file.remove(filepath)
            }
          } else {
            print(paste("  ✗ File was not created"))
          }
        }
      }, error = function(e) {
        print(paste("  ✗ Attempt", attempts, "failed:", e$message))
        if (file.exists(filepath)) {
          file.remove(filepath)
        }
      })
      
      if (!success && attempts < 3) {
        print(paste("  Retrying in 2 seconds..."))
        Sys.sleep(2)
      }
    }
    
    if (!success) {
      failed <- failed + 1
      print(paste("  ✗ Failed to download:", filename))
    }
    
    # Be polite - wait between downloads
    Sys.sleep(1)
  }
  
  print(paste("\n=== Download Summary ==="))
  print(paste("Successfully downloaded:", downloaded))
  print(paste("Failed:", failed))
  print(paste("Output directory:", output_dir))
  
} else {
  print("No PDFs found for FY1997-FY2025")
}

# Final verification: list downloaded files by FY folder
print("\n=== Verifying Downloads ===")
fy_folders <- list.dirs(output_dir, recursive = FALSE)
fy_folders <- fy_folders[grepl("^FY\\d{2}$", basename(fy_folders))]

if (length(fy_folders) > 0) {
  total_files <- 0
  for (fy_folder in sort(fy_folders)) {
    fy_name <- basename(fy_folder)
    downloaded_files <- list.files(fy_folder, pattern = "\\.pdf$", full.names = TRUE)
    file_count <- length(downloaded_files)
    total_files <- total_files + file_count
    
    if (file_count > 0) {
      print(paste(fy_name, ":", file_count, "files"))
      # Show sample files
      for (f in head(downloaded_files, 3)) {
        print(paste("  -", basename(f), "(", file.info(f)$size, "bytes )"))
      }
    }
  }
  print(paste("\nTotal files across all FY folders:", total_files))
} else {
  print("No FY folders found in output directory")
}

print("Done!")
