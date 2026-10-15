"""HYBRIXX multi-market research simulator. No real orders, keys, or withdrawals.
Development branch ONLY. Separate paper ledger, never claim it shares XRP funds.
"""
import copy
import json
import math
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from paper_trade_gate import load_approved

COINS = {"BTC":"XBTEUR","ETH":"ETHEUR","XRP":"XRPEUR","SOL":"SOLEUR",
         "ADA":"ADAEUR","DOGE":"XDGEUR","DOT":"DOTEUR","LINK":"LINKEUR",
         "LTC":"LTCEUR","AVAX":"AVAXEUR"}
STATE = Path("multi_state.json")
LEGACY_STATE = Path("state.json")

def verify_global_emergency_lock(directory=Path(".")):
    """Fail closed if the legacy or multi-market emergency lock is active or unreadable."""
    for name in ("state.json", "multi_state.json"):
        path = directory / name
        if not path.is_file():
            raise RuntimeError("Emergency lock source missing: " + name)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError("Emergency lock source unreadable: " + name) from exc
        lock = record.get("emergency_lock")
        if lock is not None:
            if not isinstance(lock, dict) or lock.get("active") is not True:
                raise RuntimeError("Malformed emergency lock in " + name)
            raise RuntimeError("GLOBAL PAPER EMERGENCY LOCK ACTIVE in " + name)
    return True

FEE = 0.0026
SLIPPAGE = 0.001
STOP_LOSS = 0.05
TAKE_PROFIT = 0.10
MAX_POSITIONS = 3
MAX_POSITION_FRACTION = 0.10
RISK_FRACTION = 0.005
MAX_DRAWDOWN = 0.15
MIN_TRADE_EUR = 15.0
MAX_HISTORY = 1000

def quotes():
    """Request each public ticker separately; Kraken response keys vary by asset."""
    found = {}
    for coin, pair in COINS.items():
        url = "https://api.kraken.com/0/public/Ticker?pair=" + pair
        req = urllib.request.Request(url, headers={"User-Agent":"HYBRIXX-Paper-Research/3"})
        with urllib.request.urlopen(req, timeout=15) as response:
            payload = json.load(response)
        if payload.get("error") or len(payload.get("result", {})) != 1:
            raise ValueError("Unavailable public quote: " + coin)
        ticker = next(iter(payload["result"].values()))
        value = float(ticker["c"][0])
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Invalid public quote: " + coin)
        found[coin] = value
    return found

def signal(history):
    if len(history) < 12:
        return "WARMUP"
    fast = sum(history[-4:]) / 4
    slow = sum(history[-12:]) / 12
    return "BUY" if fast > slow * 1.003 else ("SELL" if fast < slow * 0.997 else "HOLD")

def advance(previous, prices, stamp, approved_buys=None):
    datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if set(prices) != set(COINS):
        raise ValueError("All ten quotes required; no partial trading")
    approved_buys = set() if approved_buys is None else set(approved_buys)
    if not approved_buys.issubset(COINS):
        raise ValueError('Unknown authorized coin')
    s = copy.deepcopy(previous)
    if s.get("last_update_utc") == stamp:
        return s
    s.setdefault("cash_eur", 500.0)
    s.setdefault("positions", {})
    s.setdefault("history", {})
    s.setdefault("trades", [])
    s.setdefault("peak_eur", 500.0)
    s.setdefault("safe_stop", False)
    s.setdefault("realized_pnl_eur", 0.0)
    s.setdefault("fees_eur", 0.0)
    s.setdefault("entry", {})
    s.setdefault("cost_basis", {})
    s.setdefault("signals", {})
    s.setdefault("last_trade_index", {})
    cash = float(s["cash_eur"])
    if not math.isfinite(cash) or cash < 0:
        raise ValueError("Invalid cash")
    if any(c not in COINS or not math.isfinite(float(q)) or float(q) <= 0
           for c,q in s["positions"].items()):
        raise ValueError("Invalid position")
    for coin, raw in prices.items():
        price = float(raw)
        if not math.isfinite(price) or price <= 0:
            raise ValueError("Invalid price")
        h = s["history"].setdefault(coin, [])
        if h and abs(price / float(h[-1]) - 1) > 0.25:
            raise ValueError("Suspicious price jump: " + coin)
        h.append(price)
        s["history"][coin] = h[-MAX_HISTORY:]
    equity_before = cash + sum(float(q) * float(prices[c]) for c,q in s["positions"].items())
    s["peak_eur"] = max(float(s["peak_eur"]), equity_before)
    if equity_before <= s["peak_eur"] * (1 - MAX_DRAWDOWN):
        s["safe_stop"] = True
    lock = s.get("emergency_lock")
    if lock is not None and (not isinstance(lock, dict) or lock.get("active") is not True):
        raise ValueError("Malformed emergency lock")
    locked = lock is not None
    signals = {c:signal(s["history"][c]) for c in COINS}
    s["signals"] = signals
    s["buy_gate"] = {"mode":"FAIL_CLOSED_RESEARCH","approved_coins":sorted(approved_buys),"blocked_coins":sorted(set(COINS)-approved_buys)}
    tick_index = int(s.get("tick_index", 0)) + 1
    # Liquidations first; never open more than three concurrent positions.
    if not locked:
        for coin in list(s["positions"]):
            price = float(prices[coin])
            entry = float(s["entry"][coin])
            reason = ("STOP_LOSS" if price <= entry * (1-STOP_LOSS) else
                      "TAKE_PROFIT" if price >= entry * (1+TAKE_PROFIT) else
                      "SIGNAL_SELL" if signals[coin] == "SELL" else None)
            if not reason:
                continue
            qty = float(s["positions"].pop(coin))
            gross = qty * price * (1-SLIPPAGE)
            fee = gross * FEE
            net = gross - fee
            pnl = net - float(s["cost_basis"].pop(coin))
            cash += net
            s["fees_eur"] += fee
            s["realized_pnl_eur"] += pnl
            s["entry"].pop(coin)
            s["last_trade_index"][coin] = tick_index
            s["trades"].append({"time_utc":stamp,"symbol":coin+"/EUR",
                                "side":"SELL","reason":reason,"qty":qty,
                                "net_eur":round(net,8),"fee_eur":round(fee,8),
                                "realized_pnl_eur":round(pnl,8)})
        # Rank qualifying candidates by trend strength, not dictionary order.
        candidates = []
        for coin in COINS:
            if coin in s["positions"] or coin not in approved_buys or signals[coin] != "BUY":
                continue
            if tick_index - int(s["last_trade_index"].get(coin,-1000)) < 3:
                continue
            h = s["history"][coin]
            strength = (sum(h[-4:])/4) / (sum(h[-12:])/12) - 1
            candidates.append((strength,coin))
        candidates.sort(reverse=True)
        if not s["safe_stop"]:
            for _,coin in candidates:
                if len(s["positions"]) >= MAX_POSITIONS:
                    break
                price = float(prices[coin])
                budget = min(cash, equity_before * MAX_POSITION_FRACTION,
                             equity_before * RISK_FRACTION / STOP_LOSS)
                if budget < MIN_TRADE_EUR:
                    continue
                fill = price * (1+SLIPPAGE)
                qty = math.floor(budget / (fill*(1+FEE)) * 1e8) / 1e8
                cost = qty * fill * (1+FEE)
                if qty <= 0 or cost > cash:
                    continue
                cash -= cost
                s["positions"][coin] = qty
                s["entry"][coin] = fill
                s["cost_basis"][coin] = cost
                s["last_trade_index"][coin] = tick_index
                s["fees_eur"] += qty*fill*FEE
                s["trades"].append({"time_utc":stamp,"symbol":coin+"/EUR",
                                    "side":"BUY","reason":"TREND_RANK",
                                    "qty":qty,"cost_eur":round(cost,8),
                                    "fee_eur":round(qty*fill*FEE,8)})
    s["cash_eur"] = round(cash,8)
    s["equity_eur"] = round(cash + sum(float(q)*float(prices[c])
                                      for c,q in s["positions"].items()),2)
    s["unrealized_pnl_eur"] = round(sum(
        float(q)*float(prices[c])-float(s["cost_basis"][c])
        for c,q in s["positions"].items()),2)
    s["total_pnl_eur"] = round(s["equity_eur"]-500,2)
    s["latest_prices_eur"] = dict(prices)
    s["last_update_utc"] = stamp
    s["tick_index"] = tick_index
    s["mode"] = "PAPER_ONLY_DEVELOPMENT"
    return s

def main():
    verify_global_emergency_lock()
    prices = quotes()
    if STATE.exists():
        previous = json.loads(STATE.read_text(encoding="utf-8"))
    else:
        from migrate_xrp_state import migrate
        previous = migrate(json.loads(Path("state.json").read_text(encoding="utf-8")))
    verify_global_emergency_lock()
    approved = load_approved()
    print("RESEARCH BUY GATE", sorted(approved) if approved else "ALL NEW BUYS BLOCKED")
    updated = advance(previous, prices, datetime.now(timezone.utc).isoformat(), approved_buys=approved)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(updated, indent=2)+"\n", encoding="utf-8")
    os.replace(tmp, STATE)
    print("PAPER DEV", updated["equity_eur"], "EUR", len(updated["positions"]), "positions")

if __name__ == "__main__":
    main()
