import unittest
from datetime import datetime, timezone
from unified_intelligence import synthesize

NOW = datetime(2026, 10, 15, 18, 40, tzinfo=timezone.utc)
COINS = ("BTC","ETH","XRP","SOL","ADA","DOGE","DOT","LINK","LTC","AVAX")

def state():
    return {"last_update_utc":"2026-10-15T18:37:00+00:00",
            "cash_eur":375,"equity_eur":500,"peak_eur":500,
            "positions":{"XRP":100},
            "latest_prices_eur":dict.fromkeys(COINS,1.25),
            "trades":[],"mode":"PAPER_ONLY_DEVELOPMENT",
            "fees_eur":.3,"safe_stop":False}

def inputs():
    stamp=NOW.isoformat()
    result={k:{"generated_utc":stamp} for k in
            ("strategy","walkforward","robustness","arena","adaptive","human","gate")}
    result["arena"].update(strategy_count=20,trade_authorization=False)
    result["adaptive"].update(trade_authorization=False)
    for key in ("market_dna","correlation_breaker","black_swan_radar",
                "drift_detector","darwin_engine","counterfactual_lab",
                "reality_twin","capital_guardian","evidence_ledger",
                "investment_committee"):
        result["adaptive"][key]={}
    result["learning"]={"generated_utc":stamp,"trade_authorization":False,
                        "errors":{},"assets":{
                            coin:{"holdout_model_frozen":True,
                                  "signal_authorized":False,
                                  "holdout_observations":143}
                            for coin in COINS}}
    return result

class CouncilTests(unittest.TestCase):
    def test_full_evidence_still_no_trade_authorization(self):
        result=synthesize(state(),inputs(),NOW)
        self.assertEqual(result["research_status"],"EVIDENCE_COMPLETE")
        self.assertFalse(result["trade_authorization"])
        self.assertEqual(result["approved_paper_buys"],[])

    def test_gate_source_timestamp_is_accepted(self):
        data=inputs()
        data["gate"]={"source_generated_utc":NOW.isoformat()}
        result=synthesize(state(),data,NOW)
        self.assertNotIn("UNVERIFIED_GATE",result["veto_reasons"])

    def test_missing_evidence_veto(self):
        data=inputs()
        del data["adaptive"]
        self.assertIn("UNVERIFIED_ADAPTIVE",
                      synthesize(state(),data,NOW)["veto_reasons"])

    def test_stale_evidence_veto(self):
        data=inputs()
        data["arena"]["generated_utc"]="2026-10-01T00:00:00+00:00"
        self.assertIn("UNVERIFIED_ARENA",
                      synthesize(state(),data,NOW)["veto_reasons"])

    def test_missing_learning_veto(self):
        data=inputs()
        del data["learning"]
        self.assertIn("UNVERIFIED_LEARNING",
                      synthesize(state(),data,NOW)["veto_reasons"])

    def test_learning_requires_frozen_holdout(self):
        data=inputs()
        data["learning"]["assets"]["XRP"]["holdout_model_frozen"]=False
        self.assertIn("UNVERIFIED_LEARNING",
                      synthesize(state(),data,NOW)["veto_reasons"])

    def test_bad_account_veto(self):
        s=state()
        s["equity_eur"]=499
        self.assertIn("RISK_AUDIT_FAILED",
                      synthesize(s,inputs(),NOW)["veto_reasons"])

if __name__=="__main__":
    unittest.main()
