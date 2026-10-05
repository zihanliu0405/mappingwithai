"""Refresh computed HTML/README text and the downloadable bundle after a data build."""
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/pcos_access'

def main():
    s = json.loads((DATA / 'tract_validation.json').read_text())
    date = json.loads((DATA / 'tract_sources/manifest.json').read_text())['download_date']
    f, j, d = s['flags'], s['joins'], s['reliable_distribution_pct']
    top, v, vr, reg = s['concentration'], s['variance_all_usable'], s['variance_reliable'], s['regression']
    checks = (f"{s['tracts']:,} ACS tracts: {s['zero_population']:,} with zero women and {s['positive_population_under_50']:,} with 1–49 women; "
              f"{f['suppressed']:,} suppressed, {f['low']:,} low reliability, and {f['reliable']:,} reliable. "
              f"{s['usable']:,} have denominators of at least 50 (usable for descriptive concentration, not necessarily reliable). "
              f"Reliable rate distribution: min {d['min']:.2f}%, Q1 {d['q1']:.2f}%, median {d['median']:.2f}%, Q3 {d['q3']:.2f}%, max {d['max']:.2f}%; moment skewness {s['reliable_skew']:.3f}. "
              f"Geometry: {j['geometry']:,}; ACS: {j['acs']:,}; matched: {j['matched']:,}; geometry-only: {len(j['geometry_only'])}; ACS-only: {len(j['acs_only'])} zero-population tracts omitted by the cartographic geometry. "
              f"RUCA matches all {j['ruca_matched']:,} ACS tracts. Tract sums exactly match all 58 county numerator and denominator counts: "
              f"{s['statewide']['uninsured']:,.0f} / {s['statewide']['total']:,.0f} = {100*s['statewide']['rate']:.4f}% statewide, rounding to 8.2%. "
              f"The largest rate difference from the rounded county CSV is {s['reconciliation']['max_abs_rate_difference_pp']:.6f} percentage points.")
    concentration = (f"The top {top['top_n']:,} of {top['ranked_n']:,} non-suppressed tracts (top 10%, rounded up) contain "
                     f"{100*top['top_share_statewide']:.2f}% of statewide estimated uninsured women. "
                     f"Ties use GEOID order. The excluded small-denominator tracts contain {top['excluded_uninsured']:,.0f} uninsured women, so the curve ends just below 100%.")
    variance = (f"County membership explains {100*v['county_r_squared']:.2f}% of population-weighted variation in rates across {v['n']:,} non-suppressed tracts; "
                f"{100*v['within_share']:.2f}% is within counties. Among {vr['n']:,} reliable tracts, those shares are "
                f"{100*vr['county_r_squared']:.2f}% between and {100*vr['within_share']:.2f}% within counties.")
    b = reg['coefficients']
    regression = (f"Reliable-only, unweighted OLS (n = {reg['n']}, R² = {reg['r_squared']:.3f}): a 1 percentage-point increase in poverty is associated with "
                  f"{b['poverty_pp']:.3f} percentage points in uninsured rate, and a 1-point increase in Medicaid share with {b['medicaid_pp']:.3f} points, adjusting for the other covariate and rurality. "
                  f"Relative to urban, coefficients are {b['large rural']:.3f} points for large rural, {b['small rural']:.3f} for small rural, and {b['isolated']:.3f} for isolated; intercept {b['intercept']:.3f}. "
                  "These are exploratory associations without causal or statistical-significance claims. "
                  + 'Reliable group sizes: ' + ', '.join(f"{g} {a['n']}" for g,a in s['rurality_reliable'].items()) + '.')
    correlations = 'Pearson correlations (reliable tracts only): ' + '; '.join(f"{key}: r = {value['pearson_r']:.3f}, n = {value['n']}" for key,value in s['correlations'].items()) + '.'
    html_path = ROOT / 'index.html'
    html = html_path.read_text(encoding='utf-8')
    findings = {
        'finding-statewide': f"About {100*s['statewide']['rate']:.1f}% of women ages 19–44 were uninsured in 2020–2024: {s['statewide']['uninsured']:,.0f} estimated women. Tract sums exactly reproduce the county counts; this is a population-weighted estimate.",
        'finding-variation': f"{100*v['within_share']:.1f}% of observed population-weighted tract-rate variation is within counties. Survey noise contributes to this spread; county averages cannot show the full local pattern.",
        'finding-reliability': f"Only {f['reliable']:,} of {s['tracts']:,} tracts meet the reliability rule. The reliable subset favors higher uninsured estimates. Read group patterns with care; none of these measures identify PCOS patients.",
        'reliability-summary': f"Only {f['reliable']:,} of {s['tracts']:,} tracts meet CV ≤ 30% and a denominator of at least 50 women. This filter favors larger uninsured estimates: the reliable subset does not represent all California neighborhoods. Read patterns across groups of tracts, not rankings of individual tracts."
    }
    for id, text in {'tract-check-summary':checks,'concentration-summary':concentration,'variance-summary':variance,'regression-summary':regression,**findings}.items():
        html, count = re.subn(fr'(<p id="{id}"[^>]*>).*?(</p>)', lambda m:m[1]+text+m[2], html, flags=re.S)
        assert count == 1
    html = html.replace('Data downloaded September 5, 2026.',f'County data downloaded September 5, 2026; tract sources downloaded {date}.')
    html_path.write_text(html,encoding='utf-8')
    summary = '\n\n'.join([checks,concentration,variance,correlations,regression])
    for path in [ROOT / 'README.md', DATA / 'README.md']:
        text = path.read_text(encoding='utf-8')
        block = '<!-- tract-checks-start -->\n## Computed tract checks\n\n' + summary + '\n<!-- tract-checks-end -->'
        if '<!-- tract-checks-start -->' in text:
            text = re.sub(r'<!-- tract-checks-start -->.*?<!-- tract-checks-end -->',lambda _:block,text,flags=re.S)
        else:
            text += '\n\n' + block + '\n'
        path.write_text(text,encoding='utf-8')
    # Explicit allowlist prevents exploratory data, virtual environments or the bundle itself from entering the archive.
    names = ['README.md','TRACT_DATA_DICTIONARY.md','california_women_insurance.csv','california_pcos_access.geojson',
             'california_counties.geojson','california_tracts_women_insurance.csv','california_tracts_simplified.geojson',
             'tract_county_reconciliation.csv','tract_validation.json','validation.json','prepare_data.ps1',
             'acs_b27001_california_counties_raw.csv','acs_b27001_metadata.json']
    with zipfile.ZipFile(DATA / 'california_pcos_access_bundle.zip','w',zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / 'README.md','README.md')
        for name in ['index.html','app.js','tracts.js','styles.css']:
            archive.write(ROOT / name,name)
        for name in names:
            archive.write(DATA / name, 'data/pcos_access/' + name)
        for path in sorted((DATA / 'tract_sources').glob('*')):
            archive.write(path,'data/pcos_access/tract_sources/' + path.name)
        archive.write(DATA / 'source_cache/cb_2020_06_tract_500k.zip','data/pcos_access/source_cache/cb_2020_06_tract_500k.zip')
        for path in sorted((ROOT / 'scripts').glob('*')):
            if path.is_file():archive.write(path,'scripts/' + path.name)
    print(summary)

if __name__ == '__main__':
    main()
