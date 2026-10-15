import unittest
from datetime import datetime,timezone
from readiness_audit import inspect
from paper_trade_gate import COINS
NOW=datetime(2026,10,15,20,tzinfo=timezone.utc)
def fixture():
 s={"mode":"PAPER_ONLY_DEVELOPMENT","latest_prices_eur":{c:100 for c in COINS},"cash_eur":500,"positions":{},"trades":[],"equity_eur":500,"peak_eur":500,"safe_stop":False,"signals":{},"history":{},"tick_index":1,"fees_eur":0,"buy_gate":{"mode":"FAIL_CLOSED_RESEARCH","approved_coins":[]}}
 g={"mode":"RESEARCH_ONLY_NO_ORDERS","source_generated_utc":NOW.isoformat(),"assets":{}}
 h={"mode":"RESEARCH_ONLY_NO_ORDERS","generated_utc":NOW.isoformat(),"assets":{}}
 return s,g,h
class ReadinessAuditTests(unittest.TestCase):
 def test_clean_state(self):
  result=inspect(*fixture(),now=NOW)
  self.assertEqual(result["total"],23)
  self.assertEqual(result["critical_failures"],[])
 def test_equity_tampering(self):
  s,g,h=fixture();s["equity_eur"]=900
  self.assertIn("11_equity_reconciles",inspect(s,g,h,now=NOW)["critical_failures"])
 def test_unapproved_gate(self):
  s,g,h=fixture();s["buy_gate"]["approved_coins"]=["BTC"]
  self.assertIn("23_no_unapproved_buy_gate",inspect(s,g,h,now=NOW)["critical_failures"])
 def test_real_mode(self):
  s,g,h=fixture();s["mode"]="LIVE"
  self.assertIn("01_paper_mode",inspect(s,g,h,now=NOW)["critical_failures"])
if __name__=="__main__":unittest.main()
