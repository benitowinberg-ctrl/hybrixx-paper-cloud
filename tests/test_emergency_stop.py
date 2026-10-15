"""Emergency workflows remain PAPER ONLY; no withdrawal, no auto unlock."""
import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from emergency_stop import lock_state
from paper_v2 import advance
from security_sentinel import verify_state


class EmergencyStopTests(unittest.TestCase):
    def test_lock_is_persistent_and_idempotent(self):
        original = {"cash_eur": 500.0, "xrp": 0.0, "trades": [],
                    "observations": [{"time_utc": "2026-10-15T19:00:00+00:00", "xrp_eur": 1.0}],
                    "last_update_utc": "2026-10-15T19:00:00+00:00",
                    "equity_eur": 500.0, "paper_engine": {"version": "2.0",
                    "safe_stop": False, "signal": "HOLD", "last_action": "HOLD"}}
        now = datetime.now(timezone.utc).isoformat()
        locked = lock_state(original, "MANUAL_EMERGENCY", now)
        self.assertNotIn("emergency_lock", original)
        self.assertTrue(locked["emergency_lock"]["active"])
        self.assertTrue(locked["paper_engine"]["safe_stop"])
        self.assertTrue(verify_state(locked))
        again = lock_state(locked, "SECURITY_AUDIT_FAILED", now)
        self.assertEqual(locked, again)

    def test_locked_cannot_buy_or_sell_even_on_market_signals(self):
        base = {"cash_eur": 500.0, "xrp": 0.0, "trades": [], "observations": []}
        t0 = datetime(2026, 10, 15, tzinfo=timezone.utc)
        for i in range(12):
            base = advance(base, 1 + i * 0.025, (t0 + timedelta(minutes=30*i)).isoformat())
        self.assertEqual([x["side"] for x in base["trades"]], ["BUY"])
        start_count = len(base["trades"])
        units_before = base["xrp"]
        cash_before = base["cash_eur"]
        locked = lock_state(base, "SUSPICIOUS_ACTIVITY", datetime.now(timezone.utc).isoformat())
        updated = advance(locked, 1.12, (t0 + timedelta(minutes=30*13)).isoformat())
        self.assertEqual(len(updated["trades"]), start_count)
        self.assertEqual(updated["xrp"], units_before)
        self.assertEqual(updated["cash_eur"], cash_before)
        self.assertEqual(updated["paper_engine"]["last_action"], "LOCKED")
        self.assertEqual(updated["paper_engine"]["signal"], "LOCKED")
        self.assertTrue(verify_state(updated))

    def test_invalid_lock_state_refuses_to_trade(self):
        bad = {"cash_eur": 500.0, "xrp": 0.0, "trades": [], "observations": [],
               "emergency_lock": {"active": False}}
        with self.assertRaises(ValueError):
            advance(bad, 1.1, datetime.now(timezone.utc).isoformat())

    def test_unlock_has_no_api_and_unknown_reason_rejected(self):
        with self.assertRaises(ValueError):
            lock_state({}, "UNLOCK", datetime.now(timezone.utc).isoformat())
        import emergency_stop
        self.assertFalse(hasattr(emergency_stop, "unlock_state"))

    def test_no_private_key_in_public_lock(self):
        state = lock_state({}, "MANUAL_EMERGENCY", datetime.now(timezone.utc).isoformat())
        self.assertEqual(set(state["emergency_lock"]),
                         {"active", "reason_code", "activated_at_utc"})


if __name__ == "__main__":
    unittest.main()
