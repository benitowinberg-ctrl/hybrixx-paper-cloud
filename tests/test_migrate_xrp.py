import unittest
from migrate_xrp_state import migrate
from multi_paper import COINS, advance

LEGACY={
 "cash_eur":375.0,"xrp":104.09374735,
 "equity_eur":499.59,
 "last_update_utc":"2026-10-15T17:53:07+00:00",
 "observations":[{"time_utc":"2026-10-15T17:53:07+00:00","xrp_eur":1.1969}],
 "trades":[{"side":"BUY","symbol":"XRP/EUR","qty":104.09374735}],
 "paper_engine":{"entry_price_eur":1.19772653,"cost_basis_eur":125.0,
                 "peak_equity_eur":500.0,"fees_eur":0.32415719,
                 "realized_pnl_eur":0.0,"safe_stop":False}
}
class MigrationTests(unittest.TestCase):
 def test_preserves_single_account(self):
  original=LEGACY.copy()
  state=migrate(LEGACY)
  self.assertEqual(state["cash_eur"],375)
  self.assertAlmostEqual(state["positions"]["XRP"],104.09374735)
  self.assertEqual(state["migration"]["original_start_eur"],500)
  self.assertEqual(len(state["trades"]),1)
  self.assertAlmostEqual(state["equity_eur"],499.59,places=2)
  self.assertEqual(original["cash_eur"],375)
 def test_new_tick_keeps_xrp_and_adds_other_histories(self):
  state=migrate(LEGACY)
  prices={c:1.1969 if c=="XRP" else 10 for c in COINS}
  updated=advance(state,prices,"2026-10-15T18:00:00+00:00")
  self.assertEqual(updated["cash_eur"],375)
  self.assertEqual(updated["positions"]["XRP"],104.09374735)
  self.assertEqual(len(updated["history"]),10)
  self.assertEqual(len(updated["trades"]),1)
 def test_rejects_inconsistent_ledger(self):
  legacy=dict(LEGACY,equity_eur=999)
  with self.assertRaisesRegex(ValueError,"reconcile"):
   migrate(legacy)
 def test_emergency_lock_carries_over(self):
  legacy=dict(LEGACY,emergency_lock={"active":True,"reason_code":"MANUAL_EMERGENCY","activated_at_utc":"2026-10-15T17:00:00+00:00"})
  state=migrate(legacy)
  updated=advance(state,{c:1.1969 if c=="XRP" else 10 for c in COINS},"2026-10-15T18:00:00+00:00")
  self.assertEqual(updated["trades"],state["trades"])
if __name__=="__main__":unittest.main()
