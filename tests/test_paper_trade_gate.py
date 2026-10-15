import unittest
from datetime import datetime,timezone,timedelta
from paper_trade_gate import approved_coins
from multi_paper import advance,COINS
NOW=datetime(2026,10,15,20,tzinfo=timezone.utc)
def reports():
 gate={"mode":"RESEARCH_ONLY_NO_ORDERS","source_generated_utc":NOW.isoformat(),"assets":{"BTC":{"decision":"RESEARCH_CANDIDATE","reasons":[]}},"missing_or_failed_assets":{}}
 human={"mode":"RESEARCH_ONLY_NO_ORDERS","generated_utc":NOW.isoformat(),"assets":{"BTC":{"selected":"trend_volatility_gate","test_candles":217,"out_of_sample":{"return_pct":4,"max_drawdown_pct":3,"trades":8},"existing_ma_12_48_baseline":{"return_pct":2}}}}
 return gate,human
class GateTests(unittest.TestCase):
 def test_approved(self):
  self.assertEqual(approved_coins(*reports(),now=NOW),{"BTC"})
 def test_stale(self):
  a,b=reports();a["source_generated_utc"]=(NOW-timedelta(days=3)).isoformat()
  self.assertEqual(approved_coins(a,b,now=NOW),set())
 def test_no_trade(self):
  a,b=reports();a["assets"]["BTC"]["decision"]="NO_TRADE"
  self.assertEqual(approved_coins(a,b,now=NOW),set())
 def test_cash_blocks(self):
  a,b=reports();b["assets"]["BTC"]["selected"]="stay_in_cash"
  self.assertEqual(approved_coins(a,b,now=NOW),set())
 def test_unauthorized_buy_blocked(self):
  prices={c:100. for c in COINS}
  previous={"cash_eur":500.,"positions":{},"history":{c:[90.]*12 for c in COINS},"trades":[]}
  state=advance(previous,prices,NOW.isoformat(),approved_buys=set())
  self.assertEqual(state["positions"],{})
  self.assertFalse(any(t["side"]=="BUY" for t in state["trades"]))
  self.assertEqual(state["buy_gate"]["approved_coins"],[])
if __name__=="__main__":unittest.main()
