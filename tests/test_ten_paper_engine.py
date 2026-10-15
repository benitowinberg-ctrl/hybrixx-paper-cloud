import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from ten_paper_engine import NAMES,PARAMS,validate,advance

class TenPaperTests(unittest.TestCase):
    def setUp(self):
        self.times=[datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(hours=i) for i in range(400)]
        self.prices=[1+i*.0002 for i in range(400)]
    def test_ten_systems(self):
        self.assertEqual(len(NAMES),10)
        self.assertEqual(len(PARAMS),10)
        self.assertEqual(len(set(NAMES)),10)
    def test_emergency_lock_freezes_orders(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"paper.json"
            a=advance(path,self.times,self.prices,locked=True)
            self.assertEqual(a["system_count"],10)
            b=advance(path,self.times+[self.times[-1]+timedelta(hours=1)],self.prices+[1.09],locked=True)
            self.assertTrue(b["emergency_lock_active"])
            self.assertTrue(all(not x["trades"] for x in b["systems"].values()))
    def test_same_candle_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"paper.json"
            a=advance(path,self.times,self.prices,locked=True)
            b=advance(path,self.times,self.prices,locked=True)
            self.assertEqual(a["systems"],b["systems"])
    def test_irregular_candles_fail(self):
        rows=[{"timestamp":x.isoformat(),"close":str(p)} for x,p in zip(self.times,self.prices)]
        rows[100]["timestamp"]=rows[99]["timestamp"]
        with self.assertRaises(ValueError):validate(rows)
if __name__=="__main__":
    unittest.main()
