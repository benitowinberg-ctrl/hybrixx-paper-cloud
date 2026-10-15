"""Security regressions for market tampering and public CSP."""
import unittest
from pathlib import Path
from paper_v2 import advance


class RuntimeGuardTests(unittest.TestCase):
    def test_huge_price_spike_rejected_without_mutating_state(self):
        state = advance({}, 1.0, "2026-10-15T15:00:00+00:00")
        before = state.copy()
        with self.assertRaisesRegex(ValueError, "Suspicious XRP quote jump"):
            advance(state, 1.5, "2026-10-15T16:00:00+00:00")
        self.assertEqual(state, before)

    def test_huge_price_drop_rejected(self):
        state = advance({}, 1.0, "2026-10-15T15:00:00+00:00")
        with self.assertRaises(ValueError):
            advance(state, 0.5, "2026-10-15T16:00:00+00:00")

    def test_regular_quote_changes_still_allowed(self):
        state = advance({}, 1.0, "2026-10-15T15:00:00+00:00")
        updated = advance(state, 1.05, "2026-10-15T16:00:00+00:00")
        self.assertEqual(len(updated["observations"]), 2)

    def test_no_inline_dashboard_scripts_or_styles(self):
        for name in ("index.html", "hybrixx.html"):
            html = Path(name).read_text(encoding="utf-8")
            self.assertIn('http-equiv="Content-Security-Policy"', html)
            self.assertIn("script-src 'self'", html)
            self.assertIn("connect-src 'self'", html)
            self.assertIn('src="./dashboard.js"', html)
            self.assertIn('href="./styles.css"', html)
            self.assertNotIn("<script>", html)
            self.assertNotIn("<style>", html)
            self.assertNotIn("style=", html)
        self.assertTrue(Path("dashboard.js").is_file())
        self.assertTrue(Path("styles.css").is_file())


if __name__ == "__main__":
    unittest.main()
