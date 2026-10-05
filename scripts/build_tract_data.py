"""Offline derivation of tract data, diagnostics and static-page findings.

Run download_tract_sources.py first. No runtime API requests are used by the site.
"""
import csv
import gzip
import io
import json
import math
from collections import Counter
from pathlib import Path
import zipfile
import numpy as np
import shapefile
import shapely
from shapely.geometry import shape, mapping

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/pcos_access'
RAW = DATA / 'tract_sources'
CACHE = DATA / 'source_cache'

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')

def number(value):
    try:
        n = float(value)
        return n if n >= 0 and math.isfinite(n) else None
    except (ValueError, TypeError):
        return None

def cell(row, table, i, kind='E'):
    return number(row[f'{table}_{kind}{i:03d}'])

def aggregate(row, table, indices, kind='E'):
    values = [cell(row, table, i, kind) for i in indices]
    if any(v is None for v in values):
        return None
    return sum(values) if kind == 'E' else math.sqrt(sum(v*v for v in values))

def proportion(n, d, mn, md):
    if d is None or d <= 0 or n is None:
        return None, None, False
    p = n/d
    if mn is None or md is None:
        return p, None, False
    radicand = mn*mn - p*p*md*md
    fallback = radicand < 0
    return p, math.sqrt(mn*mn + p*p*md*md if fallback else radicand)/d, fallback

def reliability(d, p, moe):
    if d is None or d < 50:
        return 'suppressed', None
    cv = moe/1.645/p if p is not None and p > 0 and moe is not None else None
    return ('reliable' if cv is not None and cv <= .3 else 'low'), cv

def variance_partition(rows):
    y = np.array([r['uninsured_rate'] for r in rows])
    w = np.array([r['total_women_19_44'] for r in rows])
    mean = np.average(y, weights=w)
    total = float(np.sum(w*(y-mean)**2))
    within = 0.
    for county in sorted({r['county_geoid'] for r in rows}):
        mask = np.array([r['county_geoid'] == county for r in rows])
        within += float(np.sum(w[mask]*(y[mask]-np.average(y[mask], weights=w[mask]))**2))
    return {'n': len(rows), 'county_r_squared': 1-within/total, 'within_share': within/total,
            'weight': 'total_women_19_44'}

def main():
    tables = {t: {r['GEO_ID'].split('US')[1]: r for r in read_csv(RAW / f'{t}_california.csv') if r['GEO_ID'].startswith('1400000US')} for t in ['B27001','B17001','C27007','B19013']}
    assert all(set(t) == set(tables['B27001']) for t in tables.values()), 'ACS tables have different tract keys'
    counties = {r['GEOID']: r for r in read_csv(DATA / 'california_women_insurance.csv')}
    ruca_rows = read_csv(RAW / 'ruca2020_california.csv')
    ruca = {r['TractFIPS20']: r for r in ruca_rows}
    assert len(ruca) == len(ruca_rows), 'Duplicate RUCA 2020 tract key'
    records = []
    for geoid, row in sorted(tables['B27001'].items()):
        assert len(geoid) == 11 and geoid.startswith('06')
        n = aggregate(row, 'B27001', [39,42,45])
        d = aggregate(row, 'B27001', [37,40,43])
        mn = aggregate(row, 'B27001', [39,42,45], 'M')
        md = aggregate(row, 'B27001', [37,40,43], 'M')
        p, moe, fallback = proportion(n,d,mn,md)
        flag, cv = reliability(d,p,moe)
        poverty = tables['B17001'][geoid]
        pov, _, _ = proportion(cell(poverty,'B17001',2), cell(poverty,'B17001',1), None, None)
        medicaid = tables['C27007'][geoid]
        med, _, _ = proportion(aggregate(medicaid,'C27007',[4,7,10,14,17,20]), cell(medicaid,'C27007',1), None, None)
        ru = ruca.get(geoid)
        code = int(ru['PrimaryRUCA']) if ru else None
        group = 'unknown' if code in (None,99) else 'urban' if code <= 3 else 'large rural' if code <= 6 else 'small rural' if code <= 9 else 'isolated'
        assert code is None or code == 99 or 1 <= code <= 10
        records.append(dict(GEOID=geoid, county_geoid=geoid[:5], county=counties[geoid[:5]]['county'],
            period='2020-2024', total_women_19_44=d, uninsured_women_19_44=n,
            total_moe90=md, uninsured_moe90=mn, uninsured_rate=p, uninsured_rate_moe90=moe,
            rate_ci90_low=max(0,p-moe) if moe is not None else None,
            rate_ci90_high=min(1,p+moe) if moe is not None else None,
            rate_cv=cv, reliability=flag, ratio_moe_fallback=fallback,
            poverty_rate=pov, medicaid_share=med, median_household_income=cell(tables['B19013'][geoid],'B19013',1),
            ruca_primary=code, rurality=group))
    lookup = {r['GEOID']: r for r in records}
    assert all(r['uninsured_women_19_44'] is not None and r['total_women_19_44'] is not None for r in records), 'Missing insurance estimates'
    assert all(0 <= r['uninsured_women_19_44'] <= r['total_women_19_44'] for r in records)
    write_csv(DATA / 'california_tracts_women_insurance.csv', records)

    with zipfile.ZipFile(CACHE / 'cb_2020_06_tract_500k.zip') as archive:
        def member(ext):
            return io.BytesIO(archive.read(next(n for n in archive.namelist() if n.endswith(ext))))
        reader = shapefile.Reader(shp=member('.shp'), shx=member('.shx'), dbf=member('.dbf'))
        source = list(reader.iterShapeRecords())
    ids = [r.record.as_dict()['GEOID'] for r in source]
    assert len(set(ids)) == len(ids)
    shapes = np.array([shape(r.shape.__geo_interface__) for r in source], dtype=object)
    valid_coverage = bool(shapely.coverage_is_valid(shapes))
    # Preserve shared boundaries when the source is a valid coverage. Otherwise
    # use the already-generalized Census cartographic boundaries without simplification.
    simplified = shapely.coverage_simplify(shapes, .0005) if valid_coverage else shapes
    features = []
    for geoid, geometry in zip(ids, simplified):
        assert geometry.is_valid and not geometry.is_empty
        row = lookup.get(geoid)
        props = {'GEOID': geoid, 'reliability': row['reliability'] if row else 'unmatched',
                 'uninsured_pct': 100*row['uninsured_rate'] if row and row['uninsured_rate'] is not None else None}
        features.append({'type':'Feature','properties':props,'geometry':mapping(geometry)})
    assert bool(shapely.coverage_is_valid(simplified)), 'Simplification damaged shared boundaries'
    missing_geometry = set(lookup)-set(ids)
    assert all(lookup[g]['total_women_19_44']==0 for g in missing_geometry), 'Populated ACS tract lacks geometry'
    assert not (set(ids)-set(lookup)), 'Geometry tract lacks ACS data'
    assert not (set(lookup)-set(ruca)), 'ACS tract lacks verified RUCA join'
    geo_path = DATA / 'california_tracts_simplified.geojson'
    write_json(geo_path, {'type':'FeatureCollection','features':features})
    gz_size = len(gzip.compress(geo_path.read_bytes(), mtime=0))
    initial_files = ['california_pcos_access.geojson','california_women_insurance.csv','california_tracts_women_insurance.csv']
    initial_gzip = sum(len(gzip.compress((DATA/name).read_bytes(), mtime=0)) for name in initial_files)
    county_differences = []
    for geoid, county in counties.items():
        subset = [r for r in records if r['county_geoid'] == geoid]
        n = sum(r['uninsured_women_19_44'] for r in subset)
        d = sum(r['total_women_19_44'] for r in subset)
        county_differences.append(dict(GEOID=geoid, county=county['county'], tract_count=len(subset),
            tract_uninsured=n, tract_total=d, tract_rate_pct=100*n/d,
            uninsured_difference=n-float(county['female_19_44_uninsured']),
            population_difference=d-float(county['female_19_44_population']),
            rate_difference_pp=100*n/d-float(county['uninsured_pct'])))
    write_csv(DATA / 'tract_county_reconciliation.csv', county_differences)
    reliable = [r for r in records if r['reliability']=='reliable']
    usable = [r for r in records if r['reliability']!='suppressed' and r['uninsured_rate'] is not None]
    rates = np.array([100*r['uninsured_rate'] for r in reliable])
    ranked = sorted(usable, key=lambda r: (-r['uninsured_rate'],r['GEOID']))
    n_top = math.ceil(.1*len(ranked))
    n_state = sum(r['uninsured_women_19_44'] for r in records)
    d_state = sum(r['total_women_19_44'] for r in records)
    cumulative = [{'tract_share':0, 'uninsured_share':0}]
    n_cum = 0
    for i, row in enumerate(ranked,1):
        n_cum += row['uninsured_women_19_44']
        cumulative.append({'tract_share':i/len(ranked), 'uninsured_share':n_cum/n_state})
    correlations = {}
    for key in ['poverty_rate','medicaid_share']:
        complete = [r for r in reliable if r[key] is not None]
        correlations[key] = {'n':len(complete), 'pearson_r':float(np.corrcoef([r[key] for r in complete],[r['uninsured_rate'] for r in complete])[0,1])}
    complete = [r for r in reliable if r['poverty_rate'] is not None and r['medicaid_share'] is not None and r['rurality']!='unknown']
    terms = ['intercept','poverty_pp','medicaid_pp','large rural','small rural','isolated']
    x = np.array([[1,100*r['poverty_rate'],100*r['medicaid_share'],*[int(r['rurality']==g) for g in terms[3:]]] for r in complete])
    y = np.array([100*r['uninsured_rate'] for r in complete])
    beta, _, rank, _ = np.linalg.lstsq(x,y,rcond=None)
    assert rank == len(terms), 'Regression is not full rank'
    regression = {'n':len(complete),'coefficients':dict(zip(terms,beta.tolist())),
                  'r_squared':float(1-np.sum((y-x@beta)**2)/np.sum((y-y.mean())**2)), 'reference':'urban', 'weight':'unweighted'}
    groups = {g:{'n':len(rs), 'weighted_rate':sum(r['uninsured_women_19_44'] for r in rs)/sum(r['total_women_19_44'] for r in rs)} for g in terms[3:]+['urban'] if (rs := [r for r in reliable if r['rurality']==g])}
    summary = dict(tracts=len(records), flags=dict(Counter(r['reliability'] for r in records)),
        zero_population=sum(r['total_women_19_44']==0 for r in records),
        positive_population_under_50=sum(0<r['total_women_19_44']<50 for r in records),
        zero_uninsured_non_suppressed=sum(r['uninsured_women_19_44']==0 and r['total_women_19_44']>=50 for r in records),
        usable=len(usable), missing_moe=sum(r['uninsured_rate_moe90'] is None and r['total_women_19_44']>0 for r in records),
        ratio_fallbacks=sum(r['ratio_moe_fallback'] for r in records),
        joins={'geometry':len(ids),'acs':len(records),'matched':len(set(ids)&set(lookup)),
               'geometry_only':sorted(set(ids)-set(lookup)), 'acs_only':sorted(set(lookup)-set(ids)),
               'ruca_matched':len(set(ruca)&set(lookup)), 'ruca_missing':sorted(set(lookup)-set(ruca))},
        geometry={'source_coverage_valid':valid_coverage,'simplification_degrees':.0005 if valid_coverage else 0,
                  'bytes':geo_path.stat().st_size,'gzip_bytes':gz_size,
                  'initial_county_and_csv_gzip_bytes':initial_gzip},
        statewide={'uninsured':n_state,'total':d_state,'rate':n_state/d_state,'matches_existing_count':n_state==571146,'matches_existing_rounded_rate':round(100*n_state/d_state,1)==8.2},
        reconciliation={'counties':len(counties),'max_abs_uninsured_difference':max(abs(r['uninsured_difference']) for r in county_differences),
                        'max_abs_population_difference':max(abs(r['population_difference']) for r in county_differences),
                        'max_abs_rate_difference_pp':max(abs(r['rate_difference_pp']) for r in county_differences)},
        reliable_distribution_pct=dict(zip(['min','q1','median','q3','max'],np.quantile(rates,[0,.25,.5,.75,1]).tolist())),
        reliable_skew=float(np.mean((rates-rates.mean())**3)/np.std(rates)**3),
        concentration={'ranked_n':len(ranked),'top_n':n_top,'top_share_statewide':cumulative[n_top]['uninsured_share'],
                       'excluded_uninsured':n_state-n_cum,'curve':cumulative},
        variance_all_usable=variance_partition(usable), variance_reliable=variance_partition(reliable),
        correlations=correlations, regression=regression, rurality_reliable=groups)
    write_json(DATA / 'tract_validation.json', summary)
    initial_total = initial_gzip + len(gzip.compress((DATA / 'tract_validation.json').read_bytes(), mtime=0))
    print(json.dumps({k:v for k,v in summary.items() if k!='concentration'}, indent=2))
    print('Top decile:', {k:v for k,v in summary['concentration'].items() if k!='curve'})
    assert gz_size < 3_000_000, 'Tract geometry exceeds gzip budget'
    assert initial_total < 3_000_000, 'Initial county/chart data exceed gzip budget'
    print('Initial county/chart local data gzip bytes:', initial_total)
    return summary

if __name__ == '__main__':
    main()
