"""Deterministic ten-market regression tests: no exchange access."""
import unittest
from datetime import datetime, timedelta, timezone
from multi_paper import advance, COINS, signal

START = datetime(2026,10,15,tzinfo=timezone.utc)
def run(prices, initial=None):
    state = initial or {}
    for i, row in enumerate(prices):
        state = advance(state,row,(START+timedelta(minutes=i)).isoformat())
    return state

class MultiPaperTests(unittest.TestCase):
    def test_warmup_and_risk_limits(self):
        s=run([{c:10+i*0.2 for c in COINS} for i in range(12)])
        self.assertEqual(len(s["history"]),10)
        self.assertLessEqual(len(s["positions"]),3)
        self.assertGreaterEqual(s["cash_eur"],0)
        self.assertLessEqual(sum(s["cost_basis"].values()),150.01)
        self.assertTrue(all(t["side"]=="BUY" for t in s["trades"]))
        self.assertAlmostEqual(s["cash_eur"]+sum(s["positions"][c]*s["latest_prices_eur"][c] for c in s["positions"]),s["equity_eur"],places=2)

    def test_lock_prevents_all_trades(self):
        s=run([{c:10+i*0.2 for c in COINS} for i in range(12)],
              {"emergency_lock":{"active":True}})
        self.assertEqual(s["trades"],[])
        self.assertEqual(s["cash_eur"],500)

    def test_invalid_quotes_do_not_mutate_state(self):
        old={"cash_eur":500.0}
        with self.assertRaises(ValueError):
            advance(old,{"BTC":1},START.isoformat())
        self.assertEqual(old,{"cash_eur":500.0})

    def test_sell_and_realized_pnl(self):
        s=run([{c:10+i*0.2 for c in COINS} for i in range(12)])
        self.assertGreater(len(s["positions"]),0)
        old=s["last_update_utc"]
        down={c:10 for c in COINS}
        s=advance(s,down,(START+timedelta(minutes=12)).isoformat())
        self.assertTrue(any(t["side"]=="SELL" for t in s["trades"]))
        self.assertIsInstance(s["realized_pnl_eur"],float)
        self.assertNotEqual(old,s["last_update_utc"])

    def test_duplicate_timestamp_idempotent(self):
        s=run([{c:10+i*0.2 for c in COINS} for i in range(12)])
        self.assertEqual(advance(s,{c:999 for c in COINS},s["last_update_utc"]),s)

    def test_signal_and_suspicious_jump(self):
        self.assertEqual(signal([1]*11),"WARMUP")
        s=advance({}, {c:10 for c in COINS},START.isoformat())
        with self.assertRaisesRegex(ValueError,"Suspicious"):
            advance(s,{c:100 for c in COINS},(START+timedelta(minutes=1)).isoformat())

if __name__=="__main__":
    unittest.main()
