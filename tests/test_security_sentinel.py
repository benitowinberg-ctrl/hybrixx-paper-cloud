"""Regression tests for HYBRIXX security sentinel. No network access."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import security_sentinel as sentinel


class SentinelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = json.loads(Path("state.json").read_text(encoding="utf-8"))
        cls.code = Path("paper_v2.py").read_text(encoding="utf-8")

    def test_current_repository_passes(self):
        self.assertTrue(sentinel.check_repository())

    def test_public_state_rejects_credentials_and_live_mode(self):
        for key in ("api_key", "live_mode", "withdrawal_enabled"):
            state = dict(self.state)
            state[key] = "unsafe"
            with self.assertRaises(ValueError):
                sentinel.verify_state(state)

    def test_changed_equity_is_rejected(self):
        state = dict(self.state)
        state["equity_eur"] = float(state["equity_eur"]) + 100
        with self.assertRaisesRegex(ValueError, "equity-mismatch"):
            sentinel.verify_state(state)

    def test_future_price_timestamp_rejected(self):
        state = json.loads(json.dumps(self.state))
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        state["observations"][-1]["time_utc"] = future
        state["last_update_utc"] = future
        with self.assertRaises(ValueError):
            sentinel.verify_state(state)

    def test_unexpected_symbol_rejected(self):
        state = json.loads(json.dumps(self.state))
        state["observations"][-1]["symbol"] = "BTC/EUR"
        with self.assertRaisesRegex(ValueError, "unexpected-market-data"):
            sentinel.verify_state(state)

    def test_trojan_like_process_call_rejected(self):
        with self.assertRaisesRegex(ValueError, "process-or-download-execution"):
            sentinel.verify_engine_source(self.code + "\nos.system('whoami')\n", "paper_v2.py")

    def test_dynamic_evaluation_rejected(self):
        with self.assertRaisesRegex(ValueError, "dynamic-code-execution"):
            sentinel.verify_engine_source(self.code + "\neval('1+1')\n", "paper_v2.py")

    def test_unknown_remote_endpoint_rejected(self):
        altered = self.code.replace(sentinel.PUBLIC_TICKER, "https://unauthorized.example.invalid/x")
        with self.assertRaisesRegex(ValueError, "unexpected-network-endpoint"):
            sentinel.verify_engine_source(altered, "paper_v2.py")

    def test_import_of_process_module_rejected(self):
        with self.assertRaisesRegex(ValueError, "unexpected-import"):
            sentinel.verify_engine_source(self.code + "\nimport subprocess\n", "paper_v2.py")


if __name__ == "__main__":
    unittest.main()
