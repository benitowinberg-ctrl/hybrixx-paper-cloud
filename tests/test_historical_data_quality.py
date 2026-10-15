import tempfile,unittest,csv
from pathlib import Path
from historical_data_quality import inspect_csv

class HistoricalQualityTests(unittest.TestCase):
 def make(self,rows):
  t=tempfile.TemporaryDirectory()
  p=Path(t.name)/"data.csv"
  with p.open("w",newline="") as f:
   w=csv.writer(f);w.writerow(["timestamp","open","high","low","close","volume"])
   w.writerows(rows)
  self.addCleanup(t.cleanup)
  return p
 def test_valid_but_short(self):
  p=self.make([[1700000000+i*3600,100,102,99,101,3] for i in range(10)])
  q=inspect_csv(p)
  self.assertEqual(q["coverage_pct"],100)
  self.assertFalse(q["research_eligible"])
  self.assertFalse(q["trade_authorization"])
 def test_gap(self):
  p=self.make([[1700000000+i*3600,100,102,99,101,3] for i in (0,1,3)])
  self.assertEqual(inspect_csv(p)["missing_intervals"],1)
 def test_invalid_ohlc(self):
  p=self.make([[1700000000,100,90,99,101,3],[1700003600,100,102,99,101,3]])
  with self.assertRaises(ValueError):inspect_csv(p)
 def test_duplicate(self):
  p=self.make([[1700000000,100,102,99,101,3]]*2)
  with self.assertRaises(ValueError):inspect_csv(p)
if __name__=="__main__":unittest.main()
