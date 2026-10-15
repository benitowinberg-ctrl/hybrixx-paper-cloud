"""Persistent learning history invariants, offline and deterministic."""
import json
import tempfile
import unittest
from pathlib import Path
from learning_history import update_history,trends

def sample(stamp,value=1):
    return {"last_candle_utc":stamp,"data_points":720,
            "evolution":{"ranking":[{"strategy":"MA","mean_oos_return_pct":value}]}}

class LearningHistoryTests(unittest.TestCase):
    def test_idempotent_same_candle(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"history.json"
            update_history(path,sample("2026-10-15T20:00:00Z"))
            update_history(path,sample("2026-10-15T20:00:00Z",999))
            self.assertEqual(len(json.loads(path.read_text())["records"]),1)
            self.assertEqual(json.loads(path.read_text())["records"][0]["strategy_mean_oos_pct"]["MA"],1)
    def test_out_of_order_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"history.json"
            update_history(path,sample("2026-10-15T20:00:00Z"))
            with self.assertRaises(ValueError):
                update_history(path,sample("2026-10-14T20:00:00Z"))
    def test_three_distinct_candles_are_descriptive_only(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"history.json"
            history=None
            for i in range(3):
                history=update_history(path,sample(f"2026-10-{13+i:02d}T20:00:00Z",i))
            self.assertEqual(trends(history)["status"],"DESCRIPTIVE_ONLY")
            self.assertEqual(trends(history)["changes"][0]["delta_mean_oos_pct"],2)
    def test_corrupt_history_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"history.json"
            path.write_text('{"records":"invalid"}')
            with self.assertRaises(ValueError):
                update_history(path,sample("2026-10-15T20:00:00Z"))
            self.assertIn("invalid",path.read_text())
if __name__=="__main__":unittest.main()
