"""Download verified official sources; retain California extracts, never an API key."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/pcos_access'
RAW = DATA / 'tract_sources'
CACHE = DATA / 'source_cache'
BASE = 'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/'
TABLES = ['B27001', 'B17001', 'C27007', 'B19013']
GEOMETRY = 'https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_06_tract_500k.zip'
RUCA = 'https://www.ers.usda.gov/media/5443/2020-rural-urban-commuting-area-codes-census-tracts.csv?v=43472'

def download(url, target):
    if target.exists():
        return
    print('Downloading', url, flush=True)
    temporary = target.with_suffix(target.suffix + '.partial')
    with urllib.request.urlopen(url, timeout=120) as response, temporary.open('wb') as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    temporary.replace(target)

def main():
    RAW.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    manifest = []
    for table in TABLES:
        url = BASE + f'acsdt5y2024-{table.lower()}.dat'
        national = CACHE / f'{table}.dat'
        download(url, national)
        target = RAW / f'{table}_california.csv'
        with national.open(encoding='utf-8-sig', newline='') as source, target.open('w', encoding='utf-8', newline='') as output:
            reader = csv.DictReader(source, delimiter='|')
            writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
            writer.writeheader()
            n = 0
            for row in reader:
                if row['GEO_ID'].startswith(('1400000US06', '0500000US06', '0400000US06')):
                    writer.writerow(row)
                    n += 1
        print(table, n, 'California records', flush=True)
        metadata = RAW / f'{table}_metadata.json'
        download(f'https://api.census.gov/data/2024/acs/acs5/groups/{table}.json', metadata)
        manifest.append({'url': url, 'extract': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    download(GEOMETRY, CACHE / 'cb_2020_06_tract_500k.zip')
    download(RUCA, CACHE / 'ruca2020.csv')
    with (CACHE / 'ruca2020.csv').open(encoding='cp1252', newline='') as source, (RAW / 'ruca2020_california.csv').open('w', encoding='utf-8', newline='') as output:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row['StateFIPS20'] == '06':
                writer.writerow(row)
    for url, path in [(GEOMETRY, CACHE / 'cb_2020_06_tract_500k.zip'), (RUCA, CACHE / 'ruca2020.csv')]:
        manifest.append({'url': url, 'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (RAW / 'manifest.json').write_text(json.dumps({'download_date': datetime.date.today().isoformat(), 'sources': manifest}, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
