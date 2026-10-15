import unittest
from claude_research_bridge import COINS,build_payload,analyze

def reports():
    governance={"mode":"RESEARCH_ONLY_NO_ORDERS","trade_authorization":False,
        "markets":{coin:{"accuracy":.52,"baseline_accuracy":.5,
                         "holdout_samples":143,"logloss":.69,
                         "candidate_research_status":"INSUFFICIENT_EVIDENCE",
                         "secret_data":"NEVER_EXPOSE"} for coin in COINS}}
    council={"mode":"UNIFIED_RESEARCH_ONLY","trade_authorization":False,
             "research_status":"EVIDENCE_COMPLETE","veto_reasons":[]}
    return governance,council

class ClaudeBridgeTests(unittest.TestCase):
    def test_allowlisted_fields_only(self):
        g,c=reports()
        data=build_payload(g,c)
        self.assertNotIn("secret_data",str(data))
        self.assertEqual(set(data["markets"]),set(COINS))
        self.assertFalse(data["trade_authorization"])
    def test_reject_trade_authorization(self):
        g,c=reports()
        c["trade_authorization"]=True
        with self.assertRaises(ValueError):build_payload(g,c)
    def test_reject_incomplete_markets(self):
        g,c=reports()
        del g["markets"]["XRP"]
        with self.assertRaises(ValueError):build_payload(g,c)
    def test_missing_key_fails_without_network(self):
        with self.assertRaises(ValueError):analyze({}, "", "claude-sonnet-4-5")
    def test_invalid_model_fails_without_network(self):
        with self.assertRaises(ValueError):analyze({}, "test", "../bad model")

if __name__=="__main__":unittest.main()
