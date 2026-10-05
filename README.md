# mappingwithai

## Tract extension

`tracts.js` adds the geography toggle, keyboard-accessible tract menu, uncertainty panel, within-county dots, concentration curve, and poverty/Medicaid scatterplots. The existing county design and rate/count charts remain. Static HTML includes computed findings and methods without JavaScript. All analysis data are local; no localStorage or front-end build step is used.

Counties load first. Tract geometry loads only when Tracts is selected and appears at zoom 7 or higher. Low-reliability/suppressed tracts are gray. The reliable-only subset is small and atypical; read the caveats alongside the charts.

### Reproduce

Python 3.13 was used. From the repository root on Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements.txt
.\.venv\Scripts\python.exe scripts/download_tract_sources.py
.\.venv\Scripts\python.exe scripts/build_tract_data.py
.\.venv\Scripts\python.exe scripts/publish_tract_outputs.py
.\.venv\Scripts\python.exe -m unittest discover -s scripts -p "test_*.py"
```

The downloader uses official bulk files because the Census data API requires a key. It caches national files in ignored `data/pcos_access/source_cache/`, retains California extracts/metadata in `tract_sources/`, and records URLs/checksums in a manifest. Cached files are reused; remove a specific cached file to refresh it, preserving the previous manifest for audit. The bundle contains California raw extracts, original tract boundary ZIP, derived files and scripts, allowing offline build/publish after extraction. No secret/API key is needed.

See [the dictionary](data/pcos_access/TRACT_DATA_DICTIONARY.md) and [full methods](data/pcos_access/README.md). The publish script regenerates the summaries below.

### Preview and deploy

Use VS Code Live Server, or `py -m http.server 8000` from the root, then open `http://localhost:8000`. Libraries/fonts/basemap require internet. Check both geography modes, menus, county charts, empty reliable-tract states and narrow screens.

Review the `tract-level-extension` branch, push that branch, and open a pull request against the GitHub Pages source branch. After review/merge, publish the static root with the existing Pages configuration. No new host, key or build workflow is required. These scripts do not push or deploy.

### Verification

Six data tests cover MOE formulas/fallback, suppression/CV edge cases, known variance decomposition, county totals, geometry joins/size and concentration. Optional browser checks use `pip install playwright` and installed Chrome, then `python scripts/check_dashboard.py`. They exercise desktop/mobile layouts, lazy geometry, map hover/click, mode switching, keyboard menus, county charts, empty reliable-tract states and no-JavaScript findings. Screenshots are saved in ignored `preview_checks/`.

The initial county/chart datasets total 2.79 MB with gzip; on-demand tract geometry adds 2.47 MB. This measures local data payloads, excluding existing third-party basemap/library/font traffic. Actual transfer size depends on server compression.

### Files added or changed

| Group | Files |
| --- | --- |
| Front end | Changed `index.html`, `app.js`, `styles.css`; added `tracts.js`. |
| Project docs/config | Changed `.gitignore`, `README.md`, `data/pcos_access/README.md`. |
| Scripts | Added `scripts/download_tract_sources.py`, `build_tract_data.py`, `publish_tract_outputs.py`, `test_tract_data.py`, `check_dashboard.py`, `requirements.txt`. |
| Derived data (under `data/pcos_access/`) | Added `california_tracts_women_insurance.csv`, `california_tracts_simplified.geojson`, `tract_county_reconciliation.csv`, `tract_validation.json`, `TRACT_DATA_DICTIONARY.md`; updated `california_pcos_access_bundle.zip`. |
| Tract sources (under `data/pcos_access/tract_sources/`) | Added `B27001_california.csv`, `B17001_california.csv`, `C27007_california.csv`, `B19013_california.csv`; corresponding `B27001_metadata.json`, `B17001_metadata.json`, `C27007_metadata.json`, `B19013_metadata.json`; `ruca2020_california.csv`, `manifest.json`. |
| Recovered county sources (under `data/pcos_access/`) | Added `acs_b27001_california_counties_raw.csv`, `acs_b27001_metadata.json`, recovered unchanged from the original ZIP. |
# California PCOS care-access research page

Open `index.html` with **Live Server** in VS Code (right-click → Open with Live Server). No build step or package installation is needed. Serve the project root so relative data paths resolve. Do not open via `file://`.

The single page includes a MapLibre GL JS county choropleth over a grayscale CARTO Positron vector-tile basemap, a county selector, and linked D3 uncertainty and uninsured-count charts. Libraries, web fonts, and basemap tiles require internet access. No API key is configured or required for the basemap. Attribution is retained on the map.

The map measures uninsured percentages among women ages 19–44 (ACS 2020–2024), as context for potential PCOS care access. It does not map PCOS prevalence. See `data/pcos_access/README.md` for source and calculation details. Map bands are fixed at 5, 8, 11 and 15 percent; derived 90% margins of error appear in the county panel and comparison chart.

Files: `index.html`, `styles.css`, `app.js`; existing CSV and joined GeoJSON in `data/pcos_access/`. There is no separate map page because the map and charts share county selection on the main page.


<!-- tract-checks-start -->
## Computed tract checks

9,129 ACS tracts: 90 with zero women and 54 with 1–49 women; 144 suppressed, 8,636 low reliability, and 349 reliable. 8,985 have denominators of at least 50 (usable for descriptive concentration, not necessarily reliable). Reliable rate distribution: min 4.38%, Q1 18.25%, median 22.61%, Q3 27.65%, max 45.97%; moment skewness 0.359. Geometry: 9,109; ACS: 9,129; matched: 9,109; geometry-only: 0; ACS-only: 20 zero-population tracts omitted by the cartographic geometry. RUCA matches all 9,129 ACS tracts. Tract sums exactly match all 58 county numerator and denominator counts: 571,146 / 6,939,418 = 8.2305% statewide, rounding to 8.2%. The largest rate difference from the rounded county CSV is 0.000500 percentage points.

The top 899 of 8,985 non-suppressed tracts (top 10%, rounded up) contain 28.95% of statewide estimated uninsured women. Ties use GEOID order. The excluded small-denominator tracts contain 96 uninsured women, so the curve ends just below 100%.

County membership explains 8.35% of population-weighted variation in rates across 8,985 non-suppressed tracts; 91.65% is within counties. Among 349 reliable tracts, those shares are 23.08% between and 76.92% within counties.

Pearson correlations (reliable tracts only): poverty_rate: r = 0.202, n = 349; medicaid_share: r = 0.122, n = 349.

Reliable-only, unweighted OLS (n = 349, R² = 0.064): a 1 percentage-point increase in poverty is associated with 0.172 percentage points in uninsured rate, and a 1-point increase in Medicaid share with 0.006 points, adjusting for the other covariate and rurality. Relative to urban, coefficients are -4.394 points for large rural, -0.828 for small rural, and -5.702 for isolated; intercept 20.113. These are exploratory associations without causal or statistical-significance claims. Reliable group sizes: large rural 5, small rural 1, isolated 11, urban 332.
<!-- tract-checks-end -->
