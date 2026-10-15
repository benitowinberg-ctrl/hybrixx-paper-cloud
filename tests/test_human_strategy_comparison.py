import math
import unittest
from human_strategy_comparison import METHODS,desired,evaluate,compare
class HumanResearchTests(unittest.TestCase):
 def setUp(self):
  self.prices=[100+i*.03+2*math.sin(i/13) for i in range(240)]
  self.candles=[(1700000000+3600*i,p) for i,p in enumerate(self.prices)]
 def test_cash_always_cash(self):
  r=evaluate(self.prices,"stay_in_cash",60,240)
  self.assertEqual(r["return_pct"],0)
  self.assertEqual(r["trades"],0)
 def test_warmup_no_trading(self):
  for name in METHODS:self.assertFalse(desired(name,self.prices[:59]))
 def test_holdout_separation(self):
  a=compare(self.candles)
  altered=self.candles[:168]+[(t,p*2) for t,p in self.candles[168:]]
  b=compare(altered)
  self.assertEqual(a["training_ranking"],b["training_ranking"])
  self.assertEqual(a["selected"],b["selected"])
 def test_baseline_exists(self):
  self.assertIn("existing_ma_12_48_baseline",compare(self.candles))
 def test_short_data_rejected(self):
  with self.assertRaises(ValueError):compare(self.candles[:100])
if __name__=="__main__":unittest.main()
