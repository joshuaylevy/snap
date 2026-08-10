# County-change log (waiver era, FY1997–present)

`010_county_changes_1997_present.csv` is the hand-curated log of changes to U.S.
counties and county-equivalent entities relevant to the ABAWD waiver period
(FY1997–present). It is a **committed source input** to
`2_scripts/21_scrape_dl/213_geo/2131_build_geo_context.py`, which uses it to (a) set
validity intervals and predecessor/successor notes in the per-state geography context
files at `1_data/11_clean/111_geo_context/`, and (b) assert that every GEOID difference
between the 2010 and current Census county-adjacency vintages is explained by a curated
event (unexplained differences are fatal at build time).

## Source

Census Bureau, "Substantial Changes to Counties and County Equivalent Entities:
1970–Present" — decade tabs saved beside this file as
`src_census_county_changes_{1990,2000,2010,January_2020}.html` (fetched 2026-08-10).
The CT event is additionally documented in the Federal Register notice "Change to
County-Equivalents in the State of Connecticut," 87 FR 34235 (June 6, 2022).

## Inclusion rule

Only **identity events** are curated: creations, dissolutions, splits, merges, renames,
FIPS-code changes, and status changes of county-equivalent units, with effective dates
on or after October 1, 1996 (FY1997). **Boundary-only events are excluded** — e.g. the
1997 Takoma Park shift between Montgomery/Prince George's MD, Virginia part-annexations
by independent cities, the 2007 York/Newport News exchange, and the 1998 Puerto Rico
municipio territory transfers. Those change county lines, not which units exist, and the
geography context files carry names/adjacency, not boundaries.

Pre-FY1997 events (e.g. South Boston VA reverting to town status June 30, 1995; the 1990
Denali Borough creation; the 1992 Skagway-Yakutat-Angoon split) are excluded: both
adjacency vintages already reflect them and no waiver-era document uses the older units.

## Columns

| column | meaning |
|---|---|
| `event_id` | `ST_YYYY_slug`, unique |
| `state` | USPS code |
| `change_type` | `rename_fips_change` \| `new_county` \| `dissolved` \| `split` \| `rename_boundary` \| `status_boundary` \| `county_equiv_redefinition` |
| `effective_date` | legal effective date (Census page) |
| `first_affected_fy` | federal fiscal year containing the effective date. NOTE: Census data products adopt changes the *following* reference year (changes effective after Jan 1 appear in the next year's products), so documents may lag a year or more |
| `old_fips` / `old_name` | unit(s) before the event; `;`-separated when several |
| `new_fips` / `new_name` | unit(s) after; empty for dissolutions |
| `predecessor_fips` / `successor_fips` | full lineage, `;`-separated (successors of a dissolution are the absorbing counties) |
| `note` | prose detail, incl. adjacency-reconstruction rules for splits |
| `source` | decade page (+ FR citation for CT) |

The CT redefinition is one summary row (8 counties → 9 planning regions, non-nesting);
the build script treats any `09*` GEOID difference between vintages as explained by it.
