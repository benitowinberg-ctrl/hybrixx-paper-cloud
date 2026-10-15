"""HYBRIXX v1.2 XRP paper-only simulator. No exchange authentication or order placement."""
import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

START_CASH = 500.0
RISK_FRACTION = 0.005
MAX_POSITIONS = 3
STOP_FRACTION = 0.025
MAX_DAILY_LOSS = 0.02
FEE = 0.0026
SLIPPAGE = 0.001
LOOKBACK = 12
MIN_OBSERVATIONS = 24
SYMBOLS = ["BTC", "ETH", "XRP", "SOL", "NVDA", "MSFT", "VWCE", "SXR8", "SXRV", "4GLD"]
WATCHLIST_TARGET = 30

def simulate(state, price, timestamp):
    if not math.isfinite(price) or price <= 0:
        raise ValueError("Invalid market price")
    s = json.loads(json.dumps(state))
    s.setdefault("cash_eur", START_CASH)
    s.setdefault("xrp", 0.0)
    s.setdefault("trades", [])
    s.setdefault("observations", [])
    s.setdefault("pending_signal", None)
    s.setdefault("entry_price", None)
    s.setdefault("stop_price", None)
    s.setdefault("mode", "PAPER_ONLY")
    if s["mode"] != "PAPER_ONLY":
        raise ValueError("Real trading is forbidden")
    day = timestamp[:10]
    equity = s["cash_eur"] + s["xrp"] * price
    if s.get("risk_day") != day:
        s["risk_day"] = day
        s["day_open_equity"] = equity
    halted = equity <= s["day_open_equity"] * (1 - MAX_DAILY_LOSS)
    # Stop-loss takes priority; signal was generated on a previous observation.
    signal = "SELL" if s["xrp"] > 0 and s["stop_price"] is not None and price <= s["stop_price"] else s["pending_signal"]
    s["pending_signal"] = None
    if signal == "SELL" and s["xrp"] > 0:
        qty = s["xrp"]
        fill = price * (1 - SLIPPAGE)
        proceeds = qty * fill * (1 - FEE)
        s["cash_eur"] += proceeds
        s["xrp"] = 0.0
        s["entry_price"] = None
        s["stop_price"] = None
        s["trades"].append({"time_utc": timestamp, "symbol": "XRP", "side": "SELL", "quantity": qty, "fill_eur": fill, "fee_eur": qty * fill * FEE, "mode": "PAPER"})
    elif signal == "BUY" and not halted and s["xrp"] == 0:
        # One XRP position; other nine assets remain research-only until feeds exist.
        fill = price * (1 + SLIPPAGE)
        risk_budget = equity * RISK_FRACTION
        qty = min(risk_budget / (fill * STOP_FRACTION), s["cash_eur"] / (fill * (1 + FEE)), equity * 0.20 / (fill * (1 + FEE)))
        if qty > 0:
            fee = qty * fill * FEE
            s["cash_eur"] -= qty * fill + fee
            s["xrp"] += qty
            s["entry_price"] = fill
            s["stop_price"] = fill * (1 - STOP_FRACTION)
            s["trades"].append({"time_utc": timestamp, "symbol": "XRP", "side": "BUY", "quantity": qty, "fill_eur": fill, "fee_eur": fee, "mode": "PAPER"})
    s["observations"].append({"time_utc": timestamp, "xrp_eur": price})
    s["observations"] = s["observations"][-1000:]
    closes = [float(o["xrp_eur"]) for o in s["observations"]]
    if len(closes) >= MIN_OBSERVATIONS and not halted:
        prior = closes[-LOOKBACK-1:-1]
        if s["xrp"] == 0 and price > max(prior) * 1.005:
            s["pending_signal"] = "BUY"
        elif s["xrp"] > 0 and price < min(prior) * 0.995:
            s["pending_signal"] = "SELL"
    s["equity_eur"] = round(s["cash_eur"] + s["xrp"] * price, 2)
    s["last_update_utc"] = timestamp
    s["active_positions"] = int(s["xrp"] > 0)
    s["max_positions"] = MAX_POSITIONS
    s["risk_per_trade_fraction"] = RISK_FRACTION
    s["research_symbols"] = SYMBOLS
    s["watchlist_target"] = WATCHLIST_TARGET
    s["trading_halted"] = halted
    return s

def main():
    url = "https://api.kraken.com/0/public/Ticker?pair=XRPEUR"
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.load(response)
    if payload.get("error") or not payload.get("result"):
        raise RuntimeError("Market feed error")
    price = float(next(iter(payload["result"].values()))["c"][0])
    path = Path("state.json")
    old = json.loads(path.read_text()) if path.exists() else {}
    new = simulate(old, price, datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(new, indent=2) + "\n")
    print("PAPER ONLY", new["equity_eur"], len(new["trades"]), new["pending_signal"])

if __name__ == "__main__":
    main()
