import copy
import unittest
from learning_engine import FEATURE_NAMES
from learning_governance import COINS
from learning_model_archive import archive,rollback_snapshot,verified

def report():
    return {"generated_utc":"2026-10-15T20:00:00+00:00",
            "trade_authorization":False,"errors":{},
            "assets":{coin:{"feature_names":list(FEATURE_NAMES),
              "model_weights":[0.01]*len(FEATURE_NAMES),"model_bias":0.1,
              "holdout_model_frozen":True,"signal_authorized":False}
              for coin in COINS}}

class ArchiveTests(unittest.TestCase):
    def test_archive_and_rollback(self):
        history=archive(report())
        self.assertEqual(len(history),1)
        self.assertTrue(verified(rollback_snapshot(history,history[0]["sha256"])))
    def test_idempotent(self):
        first=archive(report())
        self.assertEqual(len(archive(report(),first)),1)
    def test_tamper_rejected(self):
        history=archive(report())
        history[0]["payload"]["models"]["XRP"]["bias"]=999
        self.assertFalse(verified(history[0]))
        with self.assertRaises(ValueError):rollback_snapshot(history,history[0]["sha256"])
    def test_fail_closed(self):
        data=report()
        data["trade_authorization"]=True
        with self.assertRaises(ValueError):archive(data)
    def test_bounded(self):
        history=[]
        for i in range(15):
            data=report()
            data["generated_utc"]=str(i)
            history=archive(data,history)
        self.assertEqual(len(history),12)

if __name__=="__main__":unittest.main()
