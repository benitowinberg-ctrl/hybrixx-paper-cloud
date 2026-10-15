"""Emergency lockdown switch for HYBRIXX PAPER ONLY.

Lock is one-way: no automatic unlocking and no external transfer. Triggering
requires authenticated GitHub workflow_dispatch, not a public dashboard call.
"""
import argparse
import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("state.json")
REASONS = ("MANUAL_EMERGENCY", "SUSPICIOUS_ACTIVITY", "SECURITY_AUDIT_FAILED")


def lock_state(previous, reason, timestamp):
    if reason not in REASONS:
        raise ValueError("Unknown emergency reason")
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if not isinstance(previous, dict):
        raise ValueError("Invalid emergency state")
    state = copy.deepcopy(previous)
    current = state.get("emergency_lock")
    if current is not None:
        if isinstance(current, dict) and current.get("active") is True:
            return state  # never change the original trigger or reactivate
        raise ValueError("Unrecognized lock state; refusal to overwrite")
    state["emergency_lock"] = {
        "active": True,
        "reason_code": reason,
        "activated_at_utc": timestamp,
    }
    engine = state.setdefault("paper_engine", {})
    engine["safe_stop"] = True
    engine["last_action"] = "LOCKED"
    engine["signal"] = "LOCKED"
    return state


def main():
    parser = argparse.ArgumentParser(description="Lock paper trading without transfers")
    parser.add_argument("--reason", choices=REASONS, required=True)
    args = parser.parse_args()
    if not STATE_PATH.exists():
        raise RuntimeError("Missing state; cannot claim emergency lock applied")
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).isoformat()
    updated = lock_state(state, args.reason, stamp)
    temp = STATE_PATH.with_suffix(".json.tmp")
    temp.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, STATE_PATH)
    print("HYBRIXX PAPER EMERGENCY LOCK ACTIVE. No trades and NO withdrawals.")


if __name__ == "__main__":
    main()
