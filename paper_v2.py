"""HYBRIXX v2: conservative, auditable XRP/EUR PAPER-ONLY engine.

No authenticated exchange endpoints, no real orders, no API secrets.
Runs once per scheduled GitHub Actions execution; it is NOT continuous trading.
"""
import copy
import json
import math
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("state.json")
KRAKEN_URL = "https://api.kraken.com/0/public/Ticker?pair=XRPEUR"
SYMBOL = "XRP/EUR"

# Deliberately simple assumptions for testing, NOT a validated profitable strategy.
FAST_WINDOW = 4
SLOW_WINDOW = 12
SIGNAL_BAND = 0.003
POSITION_LIMIT = 0.25           # no more than 25% of total paper equity in XRP
TRADE_FEE_RATE = 0.0026         # illustrative 0.26%, not an exchange fee quote
SLIPPAGE_RATE = 0.001           # illustrative 0.10% adverse execution
STOP_LOSS = 0.05
TAKE_PROFIT = 0.10
EQUITY_DRAWDOWN_LIMIT = 0.15
MIN_TRADE_EUR = 15.0
COOLDOWN_OBSERVATIONS = 3
MAX_OBSERVATIONS = 1000


def positive_price(value):
    try:
        price = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid price") from exc
    if not math.isfinite(price) or price <= 0:
        raise ValueError("Price must be finite and positive")
    return price


def kraken_xrp_eur():
    request = urllib.request.Request(
        KRAKEN_URL, headers={"User-Agent": "HYBRIXX-Paper-Only/2.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if payload.get("error"):
        raise RuntimeError("Kraken API error: " + str(payload["error"]))
    results = payload.get("result") or {}
    if not results:
        raise RuntimeError("Kraken ticker missing")
    ticker = next(iter(results.values()))
    return positive_price(ticker["c"][0])


def signal_for(prices):
    if len(prices) < SLOW_WINDOW:
        return "WARMUP"
    fast = sum(prices[-FAST_WINDOW:]) / FAST_WINDOW
    slow = sum(prices[-SLOW_WINDOW:]) / SLOW_WINDOW
    if fast > slow * (1 + SIGNAL_BAND):
        return "BUY"
    if fast < slow * (1 - SIGNAL_BAND):
        return "SELL"
    return "HOLD"


def advance(previous_state, price, timestamp):
    """Pure state transition: create a journal entry and simulate trades.

    The caller alone writes state.json. Errors leave the prior file unchanged.
    """
    price = positive_price(price)
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    state = copy.deepcopy(previous_state)
    state.setdefault("cash_eur", 500.0)
    state.setdefault("xrp", 0.0)
    state.setdefault("trades", [])
    state.setdefault("observations", [])
    cash = float(state["cash_eur"])
    units = float(state["xrp"])
    if not all(math.isfinite(x) and x >= 0 for x in [cash, units]):
        raise ValueError("Invalid account balance")
    if state["observations"] and state["observations"][-1].get("time_utc") == timestamp:
        return state

    engine = state.setdefault("paper_engine", {})
    engine["version"] = "2.0"
    engine.setdefault("realized_pnl_eur", 0.0)
    engine.setdefault("fees_eur", 0.0)
    engine.setdefault("safe_stop", False)
    engine.setdefault("entry_price_eur", None)
    engine.setdefault("cost_basis_eur", 0.0)
    engine.setdefault("last_trade_seq", -1000)
    engine["observation_seq"] = int(engine.get("observation_seq", len(state["observations"]))) + 1
    seq = engine["observation_seq"]

    state["observations"].append({
        "time_utc": timestamp, "symbol": SYMBOL, "xrp_eur": price
    })
    state["observations"] = state["observations"][-MAX_OBSERVATIONS:]
    prices = [
        positive_price(x["xrp_eur"])
        for x in state["observations"]
        if x.get("symbol", SYMBOL) == SYMBOL and "xrp_eur" in x
    ]
    signal = signal_for(prices)
    equity_before = cash + units * price
    engine["peak_equity_eur"] = max(
        float(engine.get("peak_equity_eur", 500.0)), equity_before
    )
    peak = engine["peak_equity_eur"]
    if peak > 0 and equity_before <= peak * (1 - EQUITY_DRAWDOWN_LIMIT):
        engine["safe_stop"] = True

    entry = engine["entry_price_eur"]
    exit_reason = None
    if units > 0 and entry is not None:
        if price <= float(entry) * (1 - STOP_LOSS):
            exit_reason = "STOP_LOSS"
        elif price >= float(entry) * (1 + TAKE_PROFIT):
            exit_reason = "TAKE_PROFIT"
    if units > 0 and signal == "SELL":
        exit_reason = exit_reason or "MOVING_AVERAGE_SELL"

    action = "HOLD"
    # Sells are still allowed during safe-stop to reduce existing exposure.
    if units > 0 and exit_reason:
        fill = price * (1 - SLIPPAGE_RATE)
        gross = units * fill
        fee = gross * TRADE_FEE_RATE
        net = gross - fee
        basis = float(engine["cost_basis_eur"])
        pnl = net - basis
        cash += net
        state["trades"].append({
            "time_utc": timestamp, "side": "SELL", "symbol": SYMBOL,
            "reason": exit_reason, "market_price_eur": price,
            "fill_price_eur": round(fill, 8), "qty": units,
            "gross_eur": round(gross, 8), "fee_eur": round(fee, 8),
            "net_eur": round(net, 8), "realized_pnl_eur": round(pnl, 8)
        })
        engine["fees_eur"] += fee
        engine["realized_pnl_eur"] += pnl
        engine["entry_price_eur"] = None
        engine["cost_basis_eur"] = 0.0
        engine["last_trade_seq"] = seq
        units = 0.0
        action = "SELL"
    elif (units == 0 and signal == "BUY" and not engine["safe_stop"]
          and seq - int(engine["last_trade_seq"]) >= COOLDOWN_OBSERVATIONS):
        # Entire cost, including fees, must remain below the 25% position limit.
        budget = min(cash, equity_before * POSITION_LIMIT)
        if budget >= MIN_TRADE_EUR:
            fill = price * (1 + SLIPPAGE_RATE)
            qty = math.floor(budget / (fill * (1 + TRADE_FEE_RATE)) * 1e8) / 1e8
            gross = qty * fill
            fee = gross * TRADE_FEE_RATE
            cost = gross + fee
            if qty > 0 and cost <= cash:
                cash -= cost
                units = qty
                engine["entry_price_eur"] = fill
                engine["cost_basis_eur"] = cost
                engine["fees_eur"] += fee
                engine["last_trade_seq"] = seq
                state["trades"].append({
                    "time_utc": timestamp, "side": "BUY", "symbol": SYMBOL,
                    "reason": "MOVING_AVERAGE_BUY", "market_price_eur": price,
                    "fill_price_eur": round(fill, 8), "qty": qty,
                    "gross_eur": round(gross, 8), "fee_eur": round(fee, 8),
                    "cost_eur": round(cost, 8)
                })
                action = "BUY"

    state["cash_eur"] = round(cash, 8)
    state["xrp"] = round(units, 8)
    state["invested_eur"] = round(units * price, 2)
    state["equity_eur"] = round(cash + units * price, 2)
    state["last_update_utc"] = timestamp
    engine["signal"] = signal
    engine["last_action"] = action
    engine["drawdown_pct"] = round(
        (1 - (cash + units * price) / peak) * 100, 3
    ) if peak else 0.0
    return state


def main():
    price = kraken_xrp_eur()  # if the data source fails, do not corrupt the ledger
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {
        "cash_eur": 500.0, "xrp": 0.0, "trades": [], "observations": []
    }
    timestamp = datetime.now(timezone.utc).isoformat()
    updated = advance(state, price, timestamp)
    temp_path = STATE_PATH.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp_path, STATE_PATH)
    engine = updated["paper_engine"]
    print(
        f"HYBRIXX PAPER ONLY | XRP/EUR {price:.5f} | "
        f"signal={engine['signal']} action={engine['last_action']} | "
        f"equity={updated['equity_eur']:.2f} EUR | "
        f"safe_stop={engine['safe_stop']}"
    )


if __name__ == "__main__":
    main()
