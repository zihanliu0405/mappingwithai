# California PCOS care access: public mapping data

## Tract extension: October 4, 2026

`california_tracts_women_insurance.csv` extends the insurance measure to California tracts. `TRACT_DATA_DICTIONARY.md` defines fields, formulas, universes, missing values and analyses. `tract_validation.json` and `tract_county_reconciliation.csv` provide checks; actual results are below and in the page.

Verified official sources:

- ACS bulk directory: https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/ (files `acsdt5y2024-b27001.dat`, `acsdt5y2024-b17001.dat`, `acsdt5y2024-c27007.dat`, `acsdt5y2024-b19013.dat`). California state/county/tract rows and all published cells/MOEs are retained in `tract_sources/`.
- Metadata: https://api.census.gov/data/2024/acs/acs5/groups.html ; table-specific JSON files are retained locally.
- 2020 boundaries: https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_06_tract_500k.zip
- USDA RUCA: https://www.ers.usda.gov/data-products/rural-urban-commuting-area-codes ; exact CSV URL and hashes in `tract_sources/manifest.json`.
- RUCA documentation: https://www.ers.usda.gov/data-products/rural-urban-commuting-area-codes/documentation

RUCA has explicit `TractFIPS20` keys, directly joined to 11-character ACS GEOIDs; no 2010 crosswalk is needed or guessed. RUCA combines 2020 population/urban delineations with **2017–2021 commuting flows**, a different period from 2020–2024 insurance. Do not substitute ZIP RUCA. Primary codes 1–3 / 4–6 / 7–9 / 10 become urban / large rural / small rural / isolated; code 99 stays unknown.

Geometry uses already-generalized, land-clipped Census 1:500,000 cartographic boundaries, simplified with Shapely shared-boundary coverage simplification at 0.0005 degrees. Source coverage and resulting polygons are validated. All source features/GEOIDs are retained. Twenty zero-population ACS tracts lack polygons in this product and remain in the CSV. GeoJSON works directly with MapLibre, requiring no extra browser dependency. Tract geometry measures 2.47 MB gzipped and loads on demand, after the initial county map. Measured gzip size is not a guarantee about a host's transfer encoding.

Poverty is B17001_002E / _001E, all people with determined poverty status. Medicaid/means-tested coverage is C27007_004E + _007E + _010E + _014E + _017E + _020E divided by _001E, all ages and both sexes in the civilian noninstitutionalized population. These universes differ from women 19–44. Medicaid is not all public insurance. Household median income is B19013_001E. Missing/sentinel ACS values are not zero-filled.

Counts are survey-estimated women, not patients. Insurance is an access proxy, not care received. PCOS prevalence, diagnoses and delays are unavailable at this scale and are not inferred. Tract associations describe places, not individuals. ACS five-year estimates are not a current snapshot. Wide MOEs favor reading groups of tracts, not individual rankings. CV filtering favors higher uninsured estimates; reliable-only results are not representative of all tracts, and rural subgroup sizes are especially small. Survey error, spatial dependence, omitted variables and covariate universe differences limit interpretation.

Run the Python download/build/publish scripts in `/scripts`; see root README for commands. Build is offline after download and checks keys, counts, geometry and size. Publish refreshes static HTML, README findings and bundle. The bundle includes California raw extracts, metadata and original tract boundary ZIP. County files remain unchanged; the two historical raw/metadata files were recovered from the existing bundle.

This dataset measures an insurance-related barrier to potential PCOS care: the percentage of civilian noninstitutionalized females ages 19-44 without health insurance. It does NOT measure PCOS prevalence, diagnoses, treatment, unmet need among PCOS patients, or confirmed provider access. Research question: Where in California are women ages 19-44 most likely to lack insurance, potentially complicating access to PCOS evaluation and care?

## Files for mapping
- california_women_insurance.csv: 58 county records, estimates and approximate 90% margins of error.
- california_counties.geojson: 58 county Polygon/MultiPolygon features with GEOID and county properties.
- california_pcos_access.geojson: the same boundaries with the insurance data already joined.
- acs_b27001_california_counties_raw.csv: original Census fields for all 58 counties, including published margins of error.
- acs_b27001_metadata.json: Census variable definitions (API naming places E/M after the number; bulk-file naming puts E/M before the number).
- prepare_data.ps1: reproducible processing script; requires downloading the national bulk source alongside the county boundary source. Download URLs below.
- validation.json: join and basic range validation results.

## Health/access source and calculations
U.S. Census Bureau, 2020-2024 American Community Survey five-year estimates, table B27001, Health Insurance Coverage Status by Sex by Age. These are period estimates, not a September 2026 snapshot.
Bulk source: https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b27001.dat
Table: https://data.census.gov/table/ACSDT5Y2024.B27001
Metadata: https://api.census.gov/data/2024/acs/acs5/groups/B27001.json
Format documentation: https://www.census.gov/programs-surveys/acs/data/summary-file.Getting_Started.html
Downloaded during this session on September 5, 2026 (America/Los_Angeles).

County rows selected by GEO_ID prefix 0500000US06, followed by three county digits.
Denominator = B27001_E037 + E040 + E043 (female ages 19-25, 26-34, 35-44).
Numerator = B27001_E039 + E042 + E045 (uninsured females in the same age bands).
uninsured_pct = 100 * numerator / denominator.
The 19-44 age window uses complete published categories; it does not cover every person affected by PCOS. Sex categories follow the ACS source and do not identify gender identity or PCOS status.

Approximate aggregate count MOE = sqrt(sum of squared published component MOEs).
Approximate percentage MOE = 100 * sqrt(MOE_numerator^2 - proportion^2 * MOE_denominator^2) / denominator; use addition instead of subtraction if the radicand is negative. These are derived 90% MOEs, not directly published Census estimates. They ignore covariance between age-category estimates. Use the MOEs in tooltips and avoid interpreting small differences as meaningful. Very small counties can have wide uncertainty. Nominal intervals may be clipped to 0-100 for display.
Method guidance: https://www.census.gov/data/academy/webinars/2020/calculating-margins-of-error-acs.html

## Geography source and connection
Official California GIS service, CA Counties, credited to California Department of Finance:
https://services.gis.ca.gov/arcgis/rest/services/Boundaries/CA_Counties/MapServer
Exact GeoJSON download:
https://services.gis.ca.gov/arcgis/rest/services/Boundaries/CA_Counties/MapServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson

Requested WGS84 longitude/latitude coordinates (EPSG:4326). Geometry is retained from the source, with no simplification. Original attributes include an older 2014 population estimate; this population field is excluded from the prepared files and is NOT used as a denominator. The service does not establish a 2024 boundary vintage, so this is an administrative county match, not a claim of exact 2024 TIGER geometry. Suitable for county-level overview mapping, not parcel-level boundary analysis.

Join CSV GEOID to GeoJSON properties.GEOID. Keep GEOID as a five-character STRING, including California's leading zero. Example: Alameda = 06001. The boundary source has three-digit FIPS; preparation prefixes 06. County level provides statewide coverage and more stable survey estimates than small neighborhoods. All 58 names and codes must match; county averages can conceal within-county inequalities.

## Field dictionary
GEOID: five-character county FIPS identifier.
county: county name, without County suffix.
period: ACS estimate period, 2020-2024.
female_19_44_population: estimated civilian noninstitutionalized female population ages 19-44.
female_19_44_uninsured: estimated uninsured count in that population.
uninsured_pct: percentage uninsured; recommended choropleth field.
uninsured_pct_moe90_approx: approximate 90% MOE, in percentage points.
population_moe90_approx: approximate 90% MOE for denominator count.
uninsured_count_moe90_approx: approximate 90% MOE for uninsured count.

## Why this measure and not a PCOS prevalence map
CDC NSFG supplies national diagnosed-PCOS context, but not public California county estimates:
https://www.cdc.gov/nchs/data/hestat/hestat121.htm
https://www.cdc.gov/rdc/b1datatype/dt1226.htm
Do not multiply a national PCOS percentage by local population and describe the result as observed county prevalence. General insurance coverage is a contextual access indicator, not a PCOS-specific outcome. Having insurance also does not guarantee affordable or available care.

The Census API returned a Missing Key page, so the actual data were obtained from its official bulk summary file. No API key is required for that download.
HCAI physician supply data were also inspected, but they combine specialties into condition-specific groups rather than isolate PCOS-related providers. Those exploratory files are not included in the mapping bundle, and the prepared data make no claims about specialist counts or travel time.

## Reproduction
Download the bulk source to acsdt5y2024-b27001.dat and the full boundary source to california_counties_source.geojson in this directory, then run prepare_data.ps1 in PowerShell. The checkout retains the county boundary source; download the national bulk file separately, or use the new Python pipeline and its retained California extracts. The ZIP omits the national bulk file to keep it compact; it includes the complete California county extract. No external PowerShell modules are required.


<!-- tract-checks-start -->
## Computed tract checks

9,129 ACS tracts: 90 with zero women and 54 with 1–49 women; 144 suppressed, 8,636 low reliability, and 349 reliable. 8,985 have denominators of at least 50 (usable for descriptive concentration, not necessarily reliable). Reliable rate distribution: min 4.38%, Q1 18.25%, median 22.61%, Q3 27.65%, max 45.97%; moment skewness 0.359. Geometry: 9,109; ACS: 9,129; matched: 9,109; geometry-only: 0; ACS-only: 20 zero-population tracts omitted by the cartographic geometry. RUCA matches all 9,129 ACS tracts. Tract sums exactly match all 58 county numerator and denominator counts: 571,146 / 6,939,418 = 8.2305% statewide, rounding to 8.2%. The largest rate difference from the rounded county CSV is 0.000500 percentage points.

The top 899 of 8,985 non-suppressed tracts (top 10%, rounded up) contain 28.95% of statewide estimated uninsured women. Ties use GEOID order. The excluded small-denominator tracts contain 96 uninsured women, so the curve ends just below 100%.

County membership explains 8.35% of population-weighted variation in rates across 8,985 non-suppressed tracts; 91.65% is within counties. Among 349 reliable tracts, those shares are 23.08% between and 76.92% within counties.

Pearson correlations (reliable tracts only): poverty_rate: r = 0.202, n = 349; medicaid_share: r = 0.122, n = 349.

Reliable-only, unweighted OLS (n = 349, R² = 0.064): a 1 percentage-point increase in poverty is associated with 0.172 percentage points in uninsured rate, and a 1-point increase in Medicaid share with 0.006 points, adjusting for the other covariate and rurality. Relative to urban, coefficients are -4.394 points for large rural, -0.828 for small rural, and -5.702 for isolated; intercept 20.113. These are exploratory associations without causal or statistical-significance claims. Reliable group sizes: large rural 5, small rural 1, isolated 11, urban 332.
<!-- tract-checks-end -->
