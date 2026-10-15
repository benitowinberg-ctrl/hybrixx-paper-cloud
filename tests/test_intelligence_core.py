"""Offline deterministic governance and research tests; no exchange access."""
import unittest
from intelligence_core import evaluate
from research_engine import simulate

class IntelligenceCoreTests(unittest.TestCase):
    def test_reject_live_mode(self):
        with self.assertRaises(ValueError):
            evaluate({"mode":"LIVE","evolution":{"ranking":[]}})
    def test_never_promote_strategy_or_enable_orders(self):
        report={"mode":"RESEARCH_ONLY","evolution":{"ranking":[
            {"strategy":"Example","mean_oos_return_pct":99,"worst_oos_drawdown_pct":1,
             "folds":3,"positive_folds":3}]}}
        core=evaluate(report)
        self.assertIsNone(core["champion"])
        self.assertFalse(core["trade_permission"])
        self.assertFalse(core["automatic_order_execution"])
        self.assertEqual(core["research_candidates"][0]["status"],"EXPLORATORY_ONLY")
    def test_reject_bad_statistics(self):
        with self.assertRaises(ValueError):
            evaluate({"mode":"RESEARCH_ONLY","evolution":{"ranking":[
                {"strategy":"X","mean_oos_return_pct":float("nan"),"worst_oos_drawdown_pct":0,
                 "folds":3,"positive_folds":1}]}})
    def test_no_order_without_signal(self):
        prices=[1.0]*320
        result=simulate(prices,100,300,"Breakout",20)
        self.assertEqual(result["orders"],0)
        self.assertEqual(result["return_pct"],0)
if __name__=="__main__":unittest.main()
