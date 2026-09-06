# California PCOS care access: public mapping data

This dataset measures an insurance-related barrier to potential PCOS care: the percentage of civilian noninstitutionalized females ages 19-44 without health insurance. It does NOT measure PCOS prevalence, diagnoses, treatment, unmet need among PCOS patients, or confirmed provider access. Research question: Where in California are women ages 19-44 most likely to lack insurance, potentially complicating access to PCOS evaluation and care?

## Files for mapping
- california_women_insurance.csv: 58 county records, estimates and approximate 90% margins of error.
- california_counties.geojson: 58 county Polygon/MultiPolygon features with GEOID and county properties.
- california_pcos_access.geojson: the same boundaries with the insurance data already joined.
- acs_b27001_california_counties_raw.csv: original Census fields for all 58 counties, including published margins of error.
- acs_b27001_metadata.json: Census variable definitions (API naming places E/M after the number; bulk-file naming puts E/M before the number).
- prepare_data.ps1: reproducible processing script; requires the two full source files retained alongside it in the workspace. Download URLs below.
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
Download the bulk source to acsdt5y2024-b27001.dat and the full boundary source to california_counties_source.geojson in this directory, then run prepare_data.ps1 in PowerShell. The workspace retains both source files. The ZIP omits the national bulk file to keep it compact; it includes the complete California county extract. No external PowerShell modules are required.
