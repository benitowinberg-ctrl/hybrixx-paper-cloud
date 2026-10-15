import unittest
from datetime import datetime, timedelta, timezone
from multi_paper import advance, COINS
class MultiPaperTests(unittest.TestCase):
    def test_warmup_and_three_position_cap(self):
        s={}
        for i in range(12):
            p={c: 10+i for c in COINS}
            s=advance(s,p,(datetime(2026,10,15,tzinfo=timezone.utc)+timedelta(minutes=i)).isoformat())
        self.assertLessEqual(len(s["positions"]),3)
        self.assertGreaterEqual(s["cash_eur"],0)
        self.assertEqual(len(s["history"]),10)
    def test_no_trades_under_lock(self):
        s={"emergency_lock":{"active":True}}
        for i in range(12):
            s=advance(s,{c:10+i for c in COINS},(datetime(2026,10,15,tzinfo=timezone.utc)+timedelta(minutes=i)).isoformat())
        self.assertEqual(s["trades"],[])
if __name__=="__main__":unittest.main()
