"""HYBRIXX Security Sentinel: conservative fail-closed checks for public paper mode.

Detects known dangerous Python patterns, non-public trading endpoints, leaked
control fields, and inconsistent public paper-account state. This is NOT a
malware scanner, network firewall, AI detector, or intrusion proof.
"""
import ast
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC_TICKER = "https://api.kraken.com/0/public/Ticker?pair=XRPEUR"
ALLOWED_IMPORTS = {"copy", "json", "math", "os", "urllib", "datetime", "pathlib"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}
FORBIDDEN_ATTRS = {
    "system", "popen", "spawnl", "spawnv", "execl", "execv",
    "fork", "forkpty", "urlretrieve", "Popen",
}
PRIVATE_STATE_KEYS = {
    "password", "api_key", "api_secret", "secret_key", "access_token",
    "refresh_token", "private_key", "exchange_key", "trading_enabled",
    "live_mode", "real_trading", "withdrawal_enabled", "withdrawal_key",
}
BANNED_SUFFIXES = {".exe", ".dll", ".so", ".dylib", ".pyd", ".class", ".jar"}
CHECKED_CODE = ("paper.py", "paper_v2.py")
VALID_SIGNALS = {"WARMUP", "HOLD", "BUY", "SELL"}
VALID_ACTIONS = {"HOLD", "BUY", "SELL"}


def failure(code):
    raise ValueError("HYBRIXX Sentinel: " + code)


def positive_number(value, label, allow_zero=False):
    if isinstance(value, bool):
        failure("invalid-number:" + label)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        failure("invalid-number:" + label)
    if not math.isfinite(number) or (number < 0 if allow_zero else number <= 0):
        failure("invalid-number:" + label)
    return number


def parse_time(value, label):
    if not isinstance(value, str):
        failure("invalid-time:" + label)
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        failure("invalid-time:" + label)
    if stamp.tzinfo is None:
        failure("naive-time:" + label)
    if stamp > datetime.now(timezone.utc) + timedelta(minutes=10):
        failure("future-time:" + label)
    return stamp


def inspect_forbidden_state_keys(obj):
    if isinstance(obj, dict):
        for key, val in obj.items():
            if str(key).lower() in PRIVATE_STATE_KEYS:
                failure("forbidden-control-or-secret-in-public-state")
            inspect_forbidden_state_keys(val)
    elif isinstance(obj, list):
        for item in obj:
            inspect_forbidden_state_keys(item)


def verify_state(state):
    """Validate public, simulation-only journal without executing it."""
    if not isinstance(state, dict):
        failure("state-not-object")
    inspect_forbidden_state_keys(state)
    cash = positive_number(state.get("cash_eur"), "cash_eur", allow_zero=True)
    units = positive_number(state.get("xrp"), "xrp", allow_zero=True)
    equity = positive_number(state.get("equity_eur"), "equity_eur", allow_zero=True)
    observations = state.get("observations")
    trades = state.get("trades")
    if not isinstance(observations, list) or not 1 <= len(observations) <= 1000:
        failure("observation-count")
    if not isinstance(trades, list) or len(trades) > 10000:
        failure("trade-count")
    previous = None
    for item in observations:
        if not isinstance(item, dict) or item.get("symbol", "XRP/EUR") != "XRP/EUR":
            failure("unexpected-market-data")
        stamp = parse_time(item.get("time_utc"), "observation")
        if previous is not None and stamp <= previous:
            failure("observations-not-chronological")
        previous = stamp
        positive_number(item.get("xrp_eur"), "price")
    for item in trades:
        if not isinstance(item, dict) or item.get("side") not in {"BUY", "SELL"}:
            failure("unexpected-trade")
        if item.get("symbol") != "XRP/EUR":
            failure("unexpected-trade-symbol")
        parse_time(item.get("time_utc"), "trade")
        positive_number(item.get("qty"), "trade-quantity")
        positive_number(item.get("fee_eur"), "trade-fee", allow_zero=True)
    if state.get("last_update_utc") != observations[-1].get("time_utc"):
        failure("last-update-does-not-match-journal")
    latest_price = float(observations[-1]["xrp_eur"])
    expected_equity = cash + units * latest_price
    if abs(equity - expected_equity) > 0.05:
        failure("equity-mismatch")
    if "invested_eur" in state and abs(
        positive_number(state["invested_eur"], "invested", allow_zero=True)
        - units * latest_price
    ) > 0.05:
        failure("invested-mismatch")
    engine = state.get("paper_engine")
    if engine is not None:
        if not isinstance(engine, dict):
            failure("invalid-engine")
        if str(engine.get("version")) != "2.0":
            failure("unexpected-engine-version")
        if type(engine.get("safe_stop")) is not bool:
            failure("invalid-safe-stop")
        if engine.get("signal") not in VALID_SIGNALS:
            failure("invalid-signal")
        if engine.get("last_action") not in VALID_ACTIONS:
            failure("invalid-action")
    return True


def verify_engine_source(code, name):
    """Small AST guardrail, intentionally NOT comprehensive malware analysis."""
    try:
        tree = ast.parse(code, filename=name)
    except SyntaxError:
        failure("invalid-python:" + name)
    ticker_urls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    failure("unexpected-import:" + name)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                failure("unexpected-import:" + name)
        elif isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id in FORBIDDEN_CALLS:
                failure("dynamic-code-execution:" + name)
            if isinstance(target, ast.Attribute) and target.attr in FORBIDDEN_ATTRS:
                failure("process-or-download-execution:" + name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith(("https://", "http://")):
                ticker_urls.append(node.value)
    if ticker_urls != [PUBLIC_TICKER]:
        failure("unexpected-network-endpoint:" + name)
    return True


def check_repository(root=ROOT):
    if not root.joinpath("state.json").is_file():
        failure("missing-paper-journal")
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            if path.suffix.lower() in BANNED_SUFFIXES:
                failure("unexpected-executable-artifact")
    for name in CHECKED_CODE:
        file = root / name
        if not file.is_file():
            failure("missing-paper-program:" + name)
        verify_engine_source(file.read_text(encoding="utf-8"), name)
    verify_state(json.loads((root / "state.json").read_text(encoding="utf-8")))
    return True


def main():
    try:
        check_repository()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("::error::HYBRIXX Security Sentinel BLOCKED: " + str(exc))
        raise SystemExit(1)
    print("HYBRIXX Sentinel: PASS (paper-state and known threat-pattern checks)")


if __name__ == "__main__":
    main()
