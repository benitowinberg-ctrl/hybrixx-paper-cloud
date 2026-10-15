"""Verify firewall template presence and fail-closed live-trade policy."""
import json
from pathlib import Path
import unittest

from security.production_guard import (
    SecurityPolicyError, authorize_order, verify_public_repo_policy
)


class FirewallGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(
            Path("security/production_policy.json").read_text(encoding="utf-8")
        )

    def test_real_trades_unconditionally_blocked(self):
        for intent in ("BUY", "SELL", "WITHDRAW"):
            with self.assertRaises(SecurityPolicyError):
                authorize_order(intent, {"owner_authenticated": True})

    def test_policy_is_explicitly_paper_only(self):
        self.assertTrue(verify_public_repo_policy(self.policy))
        self.assertFalse(self.policy["waf_deployed"])
        self.assertFalse(self.policy["protected_backend_deployed"])

    def test_unsafe_toggle_rejected(self):
        for name, value in (
            ("allow_real_trades", True),
            ("allow_withdrawals", True),
            ("require_strong_owner_authentication", False),
            ("waf_deployed", True),
            ("mode", "LIVE"),
        ):
            altered = dict(self.policy, **{name: value})
            with self.assertRaises(SecurityPolicyError):
                verify_public_repo_policy(altered)

    def test_waf_config_has_auth_and_no_deployment_pretence(self):
        source = Path("infra/cloud-armor/main.tf").read_text(encoding="utf-8")
        self.assertIn("google_compute_security_policy", source)
        self.assertIn("evaluatePreconfiguredWaf('sqli-v422-stable'", source)
        self.assertIn("evaluatePreconfiguredWaf('xss-v422-stable'", source)
        self.assertIn("evaluatePreconfiguredWaf('rce-v422-stable'", source)
        self.assertIn("evaluatePreconfiguredWaf('lfi-v422-stable'", source)
        self.assertIn('enforce_on_key = "IP"', source)
        self.assertIn("preview     = true", source)
        self.assertNotIn('resource "google_compute_backend_service"', source)

    def test_dashboard_is_static_not_admin_control(self):
        html = Path("index.html").read_text(encoding="utf-8")
        self.assertNotIn("api_secret", html)
        self.assertNotIn('action="/trade"', html)


if __name__ == "__main__":
    unittest.main()
