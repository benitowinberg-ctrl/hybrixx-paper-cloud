import unittest
from paper_engine import simulate

class PaperTests(unittest.TestCase):
    def test_invalid_price(self):
        with self.assertRaises(ValueError):
            simulate({}, 0, "2026-10-15T12:00:00Z")
    def test_no_trade_without_history(self):
        s = simulate({}, 1.0, "2026-10-15T12:00:00Z")
        self.assertEqual(s["trades"], [])
        self.assertEqual(s["cash_eur"], 500)
    def test_buy_is_paper_and_risk_limited(self):
        s = simulate({"pending_signal":"BUY"}, 1.0, "2026-10-15T12:00:00Z")
        self.assertEqual(s["trades"][0]["mode"], "PAPER")
        self.assertLessEqual(s["cash_eur"] + s["xrp"] * 1.001, 501)
        self.assertLessEqual(s["xrp"] * 1.001, 101)
    def test_sell(self):
        s = simulate({"cash_eur":400,"xrp":100,"pending_signal":"SELL"},1.0,"2026-10-15T12:00:00Z")
        self.assertEqual(s["xrp"],0)
        self.assertEqual(s["trades"][0]["side"],"SELL")
    def test_real_mode_rejected(self):
        with self.assertRaises(ValueError):
            simulate({"mode":"REAL"},1.0,"2026-10-15T12:00:00Z")
    def test_daily_loss_blocks_buy(self):
        s=simulate({"cash_eur":400,"xrp":0,"pending_signal":"BUY","risk_day":"2026-10-15","day_open_equity":500},1.0,"2026-10-15T12:00:00Z")
        self.assertEqual(s["trades"],[])
    def test_stop_sells(self):
        s=simulate({"cash_eur":400,"xrp":100,"stop_price":1.1},1.0,"2026-10-15T12:00:00Z")
        self.assertEqual(s["trades"][0]["side"],"SELL")

if __name__ == "__main__":
    unittest.main()
