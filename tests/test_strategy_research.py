import math
import unittest
from strategy_research import STRATEGIES,research,simulate,signal

class StrategyTests(unittest.TestCase):
    def setUp(self):
        self.prices=[100+.02*i+2*math.sin(i/12) for i in range(180)]
        self.candles=[(1700000000+3600*i,p) for i,p in enumerate(self.prices)]
    def test_all_signals_binary(self):
        for name in STRATEGIES:self.assertIn(signal(name,self.prices),(0,1))
    def test_holdout(self):
        r=research(self.candles)
        self.assertEqual(r["test_candles"],len(self.candles)-int(len(self.candles)*.7))
        self.assertIn(r["selected_strategy"],STRATEGIES)
    def test_no_test_data_leakage(self):
        original=research(self.candles)
        changed=self.candles[:126]+[(t,p*3) for t,p in self.candles[126:]]
        updated=research(changed)
        self.assertEqual(original["strategies"],updated["strategies"])
        self.assertEqual(original["selected_strategy"],updated["selected_strategy"])
    def test_flat_prices(self):
        r=simulate([100.0]*180,"ma_4_12",48,180)
        self.assertEqual(r["trades"],0)
        self.assertEqual(r["return_pct"],0)
    def test_short_history_rejected(self):
        with self.assertRaises(ValueError):research(self.candles[:50])
if __name__=="__main__":unittest.main()
