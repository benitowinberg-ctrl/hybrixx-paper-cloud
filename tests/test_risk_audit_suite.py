import unittest
from datetime import datetime,timezone
from risk_audit_suite import evaluate

NOW=datetime(2026,10,15,18,40,tzinfo=timezone.utc)
def sample():
 return {"last_update_utc":"2026-10-15T18:37:00+00:00","cash_eur":375,
 "equity_eur":500,"peak_eur":500,"positions":{"XRP":100},
 "latest_prices_eur":{"BTC":1,"ETH":1,"XRP":1.25,"SOL":1,"ADA":1,"DOGE":1,"DOT":1,"LINK":1,"LTC":1,"AVAX":1},
 "trades":[],"mode":"PAPER_ONLY_DEVELOPMENT","fees_eur":.3,"safe_stop":False}
class RiskAuditSuiteTests(unittest.TestCase):
 def test_valid_ledger(self):
  r=evaluate(sample(),NOW)
  self.assertTrue(r["ok"],r["errors"])
  self.assertFalse(r["trade_authorization"])
  self.assertEqual(r["accounting"]["reconciliation_difference_eur"],0)
 def test_equity_mismatch(self):
  s=sample();s["equity_eur"]=499
  self.assertFalse(evaluate(s,NOW)["ok"])
 def test_drawdown(self):
  s=sample();s["peak_eur"]=600
  self.assertIn("DRAWDOWN_LIMIT",evaluate(s,NOW)["errors"])
 def test_stale(self):
  s=sample();s["last_update_utc"]="2026-10-14T18:37:00+00:00"
  self.assertIn("STALE_DATA",evaluate(s,NOW)["errors"])
if __name__=="__main__":unittest.main()
