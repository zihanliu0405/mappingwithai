$ErrorActionPreference = 'Stop'
$dir = $PSScriptRoot
$source = Get-Content (Join-Path $dir 'california_counties_source.geojson') -Raw | ConvertFrom-Json
$lookup = @{}
foreach ($f in $source.features) { $lookup['06' + $f.properties.FIPS] = $f.properties.County }
$reader = [IO.File]::OpenText((Join-Path $dir 'acsdt5y2024-b27001.dat'))
$lines = [Collections.Generic.List[string]]::new()
$lines.Add($reader.ReadLine())
try { while (($line = $reader.ReadLine()) -ne $null) { if ($line -match '^0500000US06[0-9]{3}\|') { $lines.Add($line) } } } finally { $reader.Dispose() }
$raw = @($lines | ConvertFrom-Csv -Delimiter '|')
$raw | Export-Csv (Join-Path $dir 'acs_b27001_california_counties_raw.csv') -NoTypeInformation -Encoding UTF8
$rows = foreach ($r in $raw) {
 $id = $r.GEO_ID.Substring(9)
 $den = 0.0; $num = 0.0; $denvar = 0.0; $numvar = 0.0
 foreach ($i in @(37,40,43)) { $v = 'B27001_E' + $i.ToString('000'); $m = 'B27001_M' + $i.ToString('000'); if ([double]$r.$v -lt 0) { throw 'Invalid estimate' }; $den += [double]$r.$v; $denvar += [math]::Pow([double]$r.$m,2) }
 foreach ($i in @(39,42,45)) { $v = 'B27001_E' + $i.ToString('000'); $m = 'B27001_M' + $i.ToString('000'); if ([double]$r.$v -lt 0) { throw 'Invalid estimate' }; $num += [double]$r.$v; $numvar += [math]::Pow([double]$r.$m,2) }
 $p = $num / $den
 $rad = $numvar - $p*$p*$denvar
 if ($rad -lt 0) { $rad = $numvar + $p*$p*$denvar }
 [pscustomobject][ordered]@{ GEOID=$id; county=$lookup[$id]; period='2020-2024'; female_19_44_population=[int]$den; female_19_44_uninsured=[int]$num; uninsured_pct=[math]::Round(100*$p,3); uninsured_pct_moe90_approx=[math]::Round(100*[math]::Sqrt($rad)/$den,3); population_moe90_approx=[math]::Round([math]::Sqrt($denvar),1); uninsured_count_moe90_approx=[math]::Round([math]::Sqrt($numvar),1) }
}
$rows = @($rows | Sort-Object GEOID)
if ($rows.Count -ne 58 -or @($rows.GEOID | Select-Object -Unique).Count -ne 58) { throw 'Expected 58 unique counties' }
$byId = @{}; foreach ($r in $rows) { if (!$r.county -or $r.uninsured_pct -lt 0 -or $r.uninsured_pct -gt 100) { throw 'Invalid mapping record' }; $byId[$r.GEOID] = $r }
$rows | Export-Csv (Join-Path $dir 'california_women_insurance.csv') -NoTypeInformation -Encoding UTF8
$boundaryFeatures = @(); $joinedFeatures = @()
foreach ($f in $source.features) {
 $id = '06' + $f.properties.FIPS
 if (!$byId.ContainsKey($id) -or $f.geometry.type -notin @('Polygon','MultiPolygon')) { throw 'Boundary join failed' }
 $boundaryFeatures += [ordered]@{type='Feature'; id=$id; properties=[ordered]@{GEOID=$id; county=$lookup[$id]}; geometry=$f.geometry}
 $joinedFeatures += [ordered]@{type='Feature'; id=$id; properties=$byId[$id]; geometry=$f.geometry}
}
[ordered]@{type='FeatureCollection'; features=$boundaryFeatures} | ConvertTo-Json -Depth 100 -Compress | Set-Content (Join-Path $dir 'california_counties.geojson') -Encoding UTF8
[ordered]@{type='FeatureCollection'; features=$joinedFeatures} | ConvertTo-Json -Depth 100 -Compress | Set-Content (Join-Path $dir 'california_pcos_access.geojson') -Encoding UTF8
[ordered]@{health_rows=$rows.Count; boundary_features=$boundaryFeatures.Count; matched_counties=58; unmatched_counties=0; unique_join_key='GEOID'; coordinate_system='WGS84 longitude, latitude (EPSG:4326)'; min_uninsured_pct=($rows.uninsured_pct | Measure-Object -Minimum).Minimum; max_uninsured_pct=($rows.uninsured_pct | Measure-Object -Maximum).Maximum} | ConvertTo-Json | Set-Content (Join-Path $dir 'validation.json') -Encoding UTF8
Get-Content (Join-Path $dir 'validation.json')
