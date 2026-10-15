import math,unittest
from shadow_arena import CONFIGS,simulate,run_arena
from strategy_research import PAIRS

def series():
 return {c:[(1700000000+i*3600,100+i*.03+math.sin(i/12)) for i in range(180)] for c in PAIRS}
class ShadowArenaTests(unittest.TestCase):
 def test_twenty_unique(self):
  self.assertEqual(len(CONFIGS),20)
  self.assertEqual(len({c["id"] for c in CONFIGS}),20)
 def test_isolated_accounts(self):
  a=run_arena(series())
  self.assertEqual(a["strategy_count"],20)
  self.assertEqual(a["aggregate_hypothetical_initial_eur"],10000)
  self.assertFalse(a["trade_authorization"])
  self.assertEqual(len(a["ranking"]),20)
  self.assertTrue(all(v["initial_eur"]==500 for v in a["accounts"].values()))
 def test_no_lookahead(self):
  c=CONFIGS[0];p=[100+i*.1 for i in range(180)]
  x=simulate(p,c)
  y=simulate(p[:-1]+[p[-1]*2],c)
  self.assertEqual([t["side"] for t in x["orders"] if t["index"]<179],[t["side"] for t in y["orders"] if t["index"]<179])
 def test_invalid_market_set(self):
  a=series();a.pop("BTC")
  with self.assertRaises(ValueError):run_arena(a)
 def test_bad_price(self):
  p=[100.]*180;p[40]=float("nan")
  with self.assertRaises(ValueError):simulate(p,CONFIGS[0])
if __name__=="__main__":unittest.main()
