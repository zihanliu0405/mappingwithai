"""Checks for statistical edge cases and delivered data integrity."""
import csv
import gzip
import json
import math
from pathlib import Path
import unittest
from build_tract_data import proportion, reliability, number, variance_partition

DATA = Path(__file__).resolve().parents[1] / 'data/pcos_access'

class FormulaTests(unittest.TestCase):
    def test_proportion_and_ratio_fallback(self):
        p, moe, fallback = proportion(20,100,5,10)
        self.assertEqual(p,.2)
        self.assertAlmostEqual(moe,math.sqrt(21)/100)
        self.assertFalse(fallback)
        p, moe, fallback = proportion(80,100,1,10)
        self.assertTrue(fallback)
        self.assertAlmostEqual(moe,math.sqrt(65)/100)

    def test_zero_missing_and_reliability_boundaries(self):
        self.assertEqual(proportion(0,0,2,3),(None,None,False))
        self.assertIsNone(number('-666666666'))
        self.assertIsNone(number('250,000+'))
        self.assertEqual(reliability(49,.2,.001)[0],'suppressed')
        self.assertEqual(reliability(50,.2,.2*1.645*.30)[0],'reliable')
        self.assertEqual(reliability(50,.2,.2*1.645*.31)[0],'low')
        self.assertEqual(reliability(50,0,.1),('low',None))

    def test_variance_with_known_groups(self):
        rows=[{'county_geoid':g,'uninsured_rate':y,'total_women_19_44':1} for g,y in [('a',.1),('a',.3),('b',.5),('b',.7)]]
        self.assertAlmostEqual(variance_partition(rows)['county_r_squared'],.8)

class OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (DATA/'california_tracts_women_insurance.csv').open() as f:
            cls.rows=list(csv.DictReader(f))
        cls.report=json.loads((DATA/'tract_validation.json').read_text())

    def test_counts_and_county_reconciliation(self):
        self.assertEqual(len(self.rows),9129)
        self.assertEqual(len({r['GEOID'] for r in self.rows}),9129)
        self.assertTrue(all(len(r['GEOID'])==11 and r['GEOID'].startswith('06') for r in self.rows))
        self.assertEqual(sum(float(r['uninsured_women_19_44']) for r in self.rows),571146)
        self.assertEqual(sum(float(r['total_women_19_44']) for r in self.rows),6939418)
        with (DATA/'tract_county_reconciliation.csv').open() as f:
            self.assertTrue(all(float(r['uninsured_difference'])==float(r['population_difference'])==0 for r in csv.DictReader(f)))

    def test_geometry_and_missing_tracts(self):
        geo=json.loads((DATA/'california_tracts_simplified.geojson').read_text())
        ids={f['properties']['GEOID'] for f in geo['features']}
        self.assertEqual(len(ids),9109)
        missing=[r for r in self.rows if r['GEOID'] not in ids]
        self.assertEqual(len(missing),20)
        self.assertTrue(all(float(r['total_women_19_44'])==0 for r in missing))
        self.assertLess(len(gzip.compress((DATA/'california_tracts_simplified.geojson').read_bytes())),3_000_000)

    def test_report_against_independent_concentration(self):
        usable=[r for r in self.rows if float(r['total_women_19_44'])>=50]
        usable.sort(key=lambda r:(-float(r['uninsured_rate']),r['GEOID']))
        top=usable[:math.ceil(len(usable)/10)]
        value=sum(float(r['uninsured_women_19_44']) for r in top)/571146
        self.assertAlmostEqual(value,self.report['concentration']['top_share_statewide'])
        curve=self.report['concentration']['curve']
        self.assertTrue(all(a['uninsured_share']<=b['uninsured_share'] for a,b in zip(curve,curve[1:])))

if __name__=='__main__':
    unittest.main()
