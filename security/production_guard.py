"""Fail-closed deployment gate: forbid live orders in this public repository.

Not sufficient for a real exchange gateway. Only a future PRIVATE service
with verified platform identity and separate approvals may implement that.
"""
from __future__ import annotations

import json
from pathlib import Path

POLICY_FILE = Path(__file__).resolve().parent / "production_policy.json"


class SecurityPolicyError(RuntimeError):
    pass


def verify_public_repo_policy(data):
    if not isinstance(data, dict):
        raise SecurityPolicyError("invalid policy format")
    requirements = {
        "mode": "PAPER_ONLY",
        "allow_real_trades": False,
        "allow_withdrawals": False,
        "public_dashboard_can_place_orders": False,
        "require_strong_owner_authentication": True,
        "require_manual_live_activation": True,
        "allow_hardcoded_credentials": False,
        "api_credentials_storage": "GOOGLE_SECRET_MANAGER_ONLY",
        "waf_deployed": False,
        "protected_backend_deployed": False,
    }
    for key, expected in requirements.items():
        if key not in data or type(data[key]) is not type(expected) or data[key] != expected:
            raise SecurityPolicyError("unsafe public deployment policy: " + key)
    return True


def authorize_order(*_args, **_kwargs):
    """Every real buy/sell/withdrawal request must fail in public demo."""
    raise SecurityPolicyError("LIVE ORDERS BLOCKED: private authenticated gateway missing")


def main():
    verify_public_repo_policy(json.loads(POLICY_FILE.read_text(encoding="utf-8")))
    print("HYBRIXX: public trading API blocked; no real orders or withdrawals")


if __name__ == "__main__":
    main()
