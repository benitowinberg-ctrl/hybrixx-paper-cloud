"""Deterministic HYBRIXX paper engine regression tests; no network, no money."""
import unittest
from datetime import datetime, timedelta, timezone

from paper_v2 import advance, signal_for, positive_price

T0 = datetime(2026, 10, 15, tzinfo=timezone.utc)


def simulate(prices, initial=None):
    state = initial if initial is not None else {"cash_eur": 500.0, "xrp": 0.0, "trades": [], "observations": []}
    for i, price in enumerate(prices):
        state = advance(state, price, (T0 + timedelta(hours=i)).isoformat())
    return state


class PaperOnlyTests(unittest.TestCase):
    def test_signal_needs_twelve_observations(self):
        self.assertEqual(signal_for([1.0] * 11), "WARMUP")
        self.assertEqual(signal_for([1.0] * 12), "HOLD")
        self.assertEqual(signal_for([1 + i * 0.02 for i in range(12)]), "BUY")
        self.assertEqual(signal_for([2 - i * 0.02 for i in range(12)]), "SELL")

    def test_buy_is_capped_and_all_paper(self):
        state = simulate([1 + i * 0.025 for i in range(12)])
        self.assertEqual(state["paper_engine"]["signal"], "BUY")
        self.assertEqual(len(state["trades"]), 1)
        self.assertEqual(state["trades"][0]["side"], "BUY")
        self.assertGreater(state["cash_eur"], 374.0)
        self.assertLessEqual(state["invested_eur"], 125.0)
        self.assertGreater(state["paper_engine"]["fees_eur"], 0)

    def test_stop_loss_closes_position(self):
        up = [1 + i * 0.025 for i in range(12)]
        state = simulate(up + [up[-1] * 0.90])
        self.assertEqual([t["side"] for t in state["trades"]], ["BUY", "SELL"])
        self.assertEqual(state["trades"][-1]["reason"], "STOP_LOSS")
        self.assertEqual(state["xrp"], 0.0)
        self.assertIn("realized_pnl_eur", state["trades"][-1])

    def test_no_double_observation(self):
        timestamp = T0.isoformat()
        first = advance({}, 1.0, timestamp)
        second = advance(first, 1.0, timestamp)
        self.assertEqual(first, second)
        self.assertEqual(len(second["observations"]), 1)

    def test_invalid_market_price_is_rejected(self):
        for price in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                positive_price(price)

    def test_old_state_migrates_without_resetting_balance(self):
        old = {"cash_eur": 500.0, "xrp": 0.0, "trades": [], "observations": [
            {"time_utc": "2026-10-15T13:58:56+00:00", "xrp_eur": 1.14822}
        ]}
        updated = advance(old, 1.18, "2026-10-15T18:00:00+00:00")
        self.assertEqual(updated["cash_eur"], 500.0)
        self.assertEqual(updated["paper_engine"]["signal"], "WARMUP")
        self.assertEqual(len(updated["observations"]), 2)


if __name__ == "__main__":
    unittest.main()
