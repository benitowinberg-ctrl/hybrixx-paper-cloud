import math,unittest
from adaptive_lab import run
from shadow_arena import run_arena
from strategy_research import PAIRS
class AdaptiveLabTests(unittest.TestCase):
 def setUp(self):
  self.data={c:[(1700000000+i*3600,100+i*.025+math.sin(i/9)) for i in range(180)] for c in PAIRS}
  self.arena=run_arena(self.data)
 def test_ten_components_and_fail_closed(self):
  r=run(self.data,self.arena)
  for k in ("market_dna","correlation_breaker","black_swan_radar","drift_detector","darwin_engine","counterfactual_lab","reality_twin","capital_guardian","investment_committee","evidence_ledger"):
   self.assertIn(k,r)
  self.assertFalse(r["trade_authorization"])
  self.assertEqual(len(r["investment_committee"]),20)
  self.assertTrue(all(v["decision"].startswith("REJECT") for v in r["investment_committee"].values()))
 def test_deterministic_fingerprint(self):
  self.assertEqual(run(self.data,self.arena)["data_candles_sha256"],run(self.data,self.arena)["data_candles_sha256"])
 def test_reject_missing_coin(self):
  d=dict(self.data);d.pop("BTC")
  with self.assertRaises(ValueError):run(d,self.arena)
 def test_reject_nan(self):
  d={k:list(v) for k,v in self.data.items()}
  d["BTC"][0]=(1700000000,float("nan"))
  with self.assertRaises(ValueError):run(d,self.arena)
if __name__=="__main__":unittest.main()
