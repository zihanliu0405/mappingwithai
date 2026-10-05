# Tract data dictionary

Insurance fields describe survey-estimated civilian noninstitutionalized women ages 19–44, not patients or PCOS outcomes. CSV rates are **proportions (0–1)**. Blanks/JSON nulls mean unavailable, never zero. Import GEOIDs as strings.

| Field | Definition |
| --- | --- |
| GEOID | Eleven-character 2020 census tract identifier, preserving leading 06. |
| county_geoid / county | First five GEOID characters / existing county dataset name. |
| period | 2020-2024 ACS five-year period. |
| total_women_19_44 | B27001_037E + _040E + _043E. |
| uninsured_women_19_44 | B27001_039E + _042E + _045E. |
| total_moe90 / uninsured_moe90 | Root-sum-of-squares of the respective published component MOEs. |
| uninsured_rate | Uninsured / total; blank if denominator zero. Small-denominator estimates remain downloadable, but displayed rates are suppressed below 50. |
| uninsured_rate_moe90 | Approximate 90% MOE, proportion units. |
| rate_ci90_low / rate_ci90_high | Rate ± MOE, clipped to [0,1]. |
| rate_cv | (Rate MOE / 1.645) / rate; blank for zero/undefined rate or suppressed denominator. |
| reliability | `reliable`: denominator ≥50 and CV ≤0.30; `low`: denominator ≥50 and CV >0.30 or undefined; `suppressed`: denominator <50. A project display rule, not Census suppression. |
| ratio_moe_fallback | True if the negative proportion-formula radicand required the ratio formula. |
| poverty_rate | B17001_002E / _001E. Universe: all ages/sexes with determined poverty status, **not women 19–44**. |
| medicaid_share | Sum C27007_004E, _007E, _010E, _014E, _017E, _020E / _001E. Medicaid/means-tested coverage alone or in combination, **not all public coverage**. Universe: civilian noninstitutionalized population, all ages/both sexes, **not women 19–44**. |
| median_household_income | B19013_001E, households, 2024 dollars; missing/sentinel or nonnumeric top-coded values are blank. |
| ruca_primary | USDA 2020 PrimaryRUCA joined on TractFIPS20; 99 = not coded. |
| rurality | Primary RUCA 1–3 urban, 4–6 large rural, 7–9 small rural, 10 isolated, 99/missing unknown. Analyst grouping, not a clinical access classification. |

Bulk ACS names put E/M before cell numbers (B27001_E037); API names put them after (B27001_037E). Original estimates and MOEs are retained in raw extracts. Negative Census sentinels and nonnumeric special values become missing. Covariate MOEs are retained but are not propagated into associations.

For numerator N, denominator D, p=N/D, and aggregated count MOEs MN and MD:

```
MN = sqrt(sum(numerator component MOE²))
MD = sqrt(sum(denominator component MOE²))
rate MOE = sqrt(MN² - p² MD²) / D
if radicand negative: sqrt(MN² + p² MD²) / D
CV = (rate MOE / 1.645) / p
```

These approximations omit covariance between age cells. Zero uninsured estimates have undefined CV and are flagged low, not treated as certainty of no uninsured women. All counts remain in statewide rollups.

## Other files and analyses

`california_tracts_simplified.geojson` retains GEOID, reliability and `uninsured_pct` (**0–100**, unlike CSV). Other attributes join in the browser. Gray overrides rate colors for low/suppressed tracts. Census NAD83 longitude/latitude coordinates are used as WGS84-equivalent for this generalized web map, not precise surveying.

`tract_county_reconciliation.csv` lists tract sums and differences **tract minus existing county**, in counts and percentage points. `tract_validation.json` stores diagnostics and chart inputs.

Concentration ranks all tracts with ≥50 women, including low reliability; descending rate, ties by GEOID, top decile = ceil(0.1 × ranked n). Cumulative counts divide by **all statewide uninsured women**, including suppressed tracts. Weighted one-way ANOVA R² uses total women as weights and is shown for non-suppressed and reliable-only samples. Quantiles, moment skewness, Pearson correlations and OLS are unweighted. OLS uses percentage-point outcome/covariates with urban as rurality reference. No causal, individual-level or statistical-significance interpretation is warranted.
