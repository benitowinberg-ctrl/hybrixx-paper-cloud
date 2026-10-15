"""Regression checks: global emergency lock must block multi-coin trading."""
import json
import tempfile
import unittest
from pathlib import Path
from multi_paper import verify_global_emergency_lock, advance, COINS

class GlobalEmergencyLockTests(unittest.TestCase):
    def test_legacy_lock_blocks_multicoin(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"state.json").write_text(json.dumps({"emergency_lock":{"active":True,"reason_code":"SECURITY_AUDIT_FAILED"}}))
            (root/"multi_state.json").write_text("{}")
            with self.assertRaisesRegex(RuntimeError,"GLOBAL PAPER EMERGENCY LOCK"):
                verify_global_emergency_lock(root)
    def test_multicoin_lock_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"state.json").write_text("{}")
            (root/"multi_state.json").write_text(json.dumps({"emergency_lock":{"active":True}}))
            with self.assertRaises(RuntimeError):verify_global_emergency_lock(root)
    def test_missing_or_corrupt_state_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"state.json").write_text("{}")
            with self.assertRaises(RuntimeError):verify_global_emergency_lock(root)
            (root/"multi_state.json").write_text("{")
            with self.assertRaises(RuntimeError):verify_global_emergency_lock(root)
    def test_clean_sources_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ("state.json","multi_state.json"):
                (root/name).write_text("{}")
            self.assertTrue(verify_global_emergency_lock(root))
    def test_direct_advance_blocks_multicoin_lock(self):
        s={"cash_eur":500,"positions":{},"history":{},"trades":[],
           "peak_eur":500,"emergency_lock":{"active":True}}
        prices={c:10.0 for c in COINS}
        out=advance(s,prices,"2026-10-15T20:00:00+00:00")
        self.assertEqual(out["trades"],[])
        self.assertEqual(out["cash_eur"],500)

if __name__=="__main__":unittest.main()
