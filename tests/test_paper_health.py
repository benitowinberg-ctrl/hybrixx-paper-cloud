"""Deterministic regression tests for paper health and offline backtest."""
import unittest
from datetime import datetime, timezone, timedelta
from paper_health import audit
from research_backtest import evaluate
from multi_paper import COINS

NOW=datetime(2026,10,15,20,0,tzinfo=timezone.utc)
def valid():
 return {"last_update_utc":NOW.isoformat(),"cash_eur":375.0,
         "positions":{"XRP":100.0},"latest_prices_eur":{c:(1.25 if c=="XRP" else 10) for c in COINS},
         "equity_eur":500.0,"trades":[],"mode":"PAPER_ONLY_DEVELOPMENT"}
class HealthTests(unittest.TestCase):
 def test_healthy_account(self):
  self.assertTrue(audit(valid(),now=NOW)["ok"])
 def test_stale_data(self):
  s=valid();s["last_update_utc"]=(NOW-timedelta(hours=2)).isoformat()
  self.assertIn("STALE_DATA",audit(s,now=NOW)["errors"])
 def test_equity_tamper(self):
  s=valid();s["equity_eur"]=999
  self.assertIn("EQUITY_MISMATCH",audit(s,now=NOW)["errors"])
 def test_unknown_market(self):
  s=valid();s["latest_prices_eur"].pop("AVAX")
  self.assertIn("INCOMPLETE_MARKETS",audit(s,now=NOW)["errors"])
 def test_offline_backtest_synthetic_only(self):
  rows=[]
  for i in range(30):
   stamp=NOW+timedelta(minutes=15*i)
   rows.append((stamp,stamp.isoformat(),{c:10+i*.02 for c in COINS}))
  result=evaluate(rows)
  self.assertEqual(result["observations"],30)
  self.assertGreaterEqual(result["ending_eur"],0)
  self.assertIn("max_drawdown_pct",result)
if __name__=="__main__":unittest.main()
