"""Security baseline regression tests; explicitly no fake HTML password protection."""
import unittest

import security_check


class SecurityChecks(unittest.TestCase):
    def test_no_obvious_secrets_in_tracked_files(self):
        self.assertEqual(security_check.check(), [])

    def test_public_state_rejects_private_access_fields(self):
        result = security_check.scan_tree({"cash_eur": 500, "nested": {"api_key": "dummy"}})
        self.assertEqual(result, [("state.nested.api_key", "private-state-field")])

    def test_empty_public_state_is_safe(self):
        self.assertEqual(security_check.scan_tree({"cash_eur": 500, "trades": []}), [])


if __name__ == "__main__":
    unittest.main()
