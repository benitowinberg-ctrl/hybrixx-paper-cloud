import copy
import unittest
from datetime import datetime,timezone,timedelta
from learning_governance import COINS,evaluate

NOW=datetime(2026,10,15,20,tzinfo=timezone.utc)
def sample():
    return {"generated_utc":NOW.isoformat(),"mode":"RESEARCH_ONLY_NO_ORDERS",
        "trade_authorization":False,"errors":{},
        "assets":{coin:{"holdout_model_frozen":True,"signal_authorized":False,
                        "holdout_observations":143,"holdout_accuracy":.55,
                        "always_down_baseline_accuracy":.53,"holdout_logloss":.69}
                  for coin in COINS}}

class GovernanceTests(unittest.TestCase):
    def test_ten_checks_and_no_promotion(self):
        report,history=evaluate(sample(),[],NOW)
        self.assertEqual(len(report["checks"]),10)
        self.assertEqual(len(report["markets"]),10)
        self.assertFalse(report["trade_authorization"])
        self.assertEqual(report["models_promoted"],[])
        self.assertEqual(len(history),1)
    def test_duplicate_run_does_not_duplicate_history(self):
        _,history=evaluate(sample(),[],NOW)
        _,again=evaluate(sample(),history,NOW)
        self.assertEqual(len(again),1)
    def test_reject_unsafe_report(self):
        data=sample()
        data["trade_authorization"]=True
        with self.assertRaises(ValueError):evaluate(data,[],NOW)
    def test_reject_incomplete_market(self):
        data=sample()
        del data["assets"]["XRP"]
        with self.assertRaises(ValueError):evaluate(data,[],NOW)
    def test_reject_stale_report(self):
        data=sample()
        data["generated_utc"]=(NOW-timedelta(days=2)).isoformat()
        with self.assertRaises(ValueError):evaluate(data,[],NOW)
    def test_reject_invalid_holdout(self):
        data=sample()
        data["assets"]["XRP"]["holdout_model_frozen"]=False
        with self.assertRaises(ValueError):evaluate(data,[],NOW)
    def test_baseline_gate(self):
        data=sample()
        data["assets"]["XRP"]["holdout_accuracy"]=.5
        result,_=evaluate(data,[],NOW)
        self.assertEqual(result["markets"]["XRP"]["candidate_research_status"],"REJECT")
    def test_drift_flag(self):
        data=sample()
        _,history=evaluate(data,[],NOW)
        later=copy.deepcopy(data)
        later["generated_utc"]=(NOW+timedelta(hours=1)).isoformat()
        later["assets"]["XRP"]["holdout_accuracy"]=.45
        result,_=evaluate(later,history,NOW+timedelta(hours=1))
        self.assertTrue(result["markets"]["XRP"]["drift_warning"])

if __name__=="__main__":
    unittest.main()
