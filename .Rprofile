source("renv/activate.R")
### print current working directory of R instance
print("#############################################################################")
print(paste("Loading local custom .Rprofile:", getwd(), "/.Rprofile", sep = ""))
print(paste("CURRENT WORKING DIRECTORY:", getwd(), sep = " "))
print("#############################################################################")



### setting CRAN mirror default
local({
    r <- getOption("repos")
    r["CRAN"] <- "https://cran.rstudio.com/"
    options(repos = r)
})
Sys.setenv(RGL_USE_NULL = TRUE)

## Optional: print to confirm
print("renv external.libraries set to:")
print(renv::settings$external.libraries())

### httpgd plot viewer setup
options(vsc.plot = FALSE)
if (interactive() && Sys.getenv("TERM_PROGRAM") == "vscode") {
    if ("httpgd" %in% .packages(all.available = TRUE)) {
        options(vsc.plot = FALSE)
        options(device = function(...) {
            httpgd::hgd(silent = TRUE)
            .vsc.browser(httpgd::hgd_url(history = FALSE), viewer = "Beside")
        })
    }
}

## loading custom fonts
# NOTE: For replication packages, copy font files to project directory and update paths
# Font files should be copied from: /Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/fonts/
inter_font_load <- function() {
    tryCatch(
        {
            sysfonts::font_add(
                family = "Inter",
                regular = "/Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/fonts/Inter-Regular.ttf",
                bold = "/Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/fonts/Inter-Bold.ttf",
                italic = "/Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/fonts/Inter-Light.ttf"
            )
        },
        warning = function(w) {
            message("WARNING: Custom font ('Inter') failed to load properly. Custom themes may not load properly")
        }
    )
}
inter_font_load()

intel_font_load <- function() {
    tryCatch(
        {
            sysfonts::font_add(
                family = "Intel One",
                regular = "/Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/fonts/intelone-mono-font-family-regular.ttf",
                bold = "/Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/fonts/intelone-mono-font-family-bold.ttf",
                italic = "/Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/fonts/intelone-mono-font-family-italic.ttf"
            )
        },
        warning = function(w) {
            message("WARNING: Custom font ('Intel One') failed to load properly. Custom themes may not load properly")
        }
    )
}
intel_font_load()

### loading personal theme for dataviz
# NOTE: For replication packages, copy theme_personal.R to project directory and update path
# Copy from: /Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/r_materials/theme_personal.R
source("/Users/joshuaylevy/Documents/Work/General/projectTemplatesSnips/theme_personal/r_materials/theme_personal.R")
