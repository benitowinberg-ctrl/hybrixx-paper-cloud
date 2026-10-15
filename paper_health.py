"""HYBRIXX read-only paper-run health and accounting checks."""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from multi_paper import COINS, MAX_POSITIONS

def audit(state, now=None, max_age_minutes=50):
    now=now or datetime.now(timezone.utc)
    errors=[]
    try:
        timestamp=datetime.fromisoformat(state["last_update_utc"].replace("Z","+00:00"))
        if timestamp.tzinfo is None: raise ValueError("missing timezone")
        age=(now-timestamp).total_seconds()/60
        if age > max_age_minutes: errors.append("STALE_DATA")
        if age < -10: errors.append("FUTURE_TIMESTAMP")
        cash=float(state["cash_eur"])
        positions=state["positions"]
        prices=state["latest_prices_eur"]
        if set(prices)!=set(COINS): errors.append("INCOMPLETE_MARKETS")
        if set(positions)-set(COINS): errors.append("UNKNOWN_POSITION")
        if len(positions)>MAX_POSITIONS: errors.append("POSITION_LIMIT")
        if not math.isfinite(cash) or cash<0: errors.append("INVALID_CASH")
        if any(not math.isfinite(float(v)) or float(v)<=0 for v in prices.values()): errors.append("INVALID_QUOTES")
        if any(not math.isfinite(float(q)) or float(q)<=0 for q in positions.values()): errors.append("INVALID_QUANTITY")
        calculated=cash+sum(float(q)*float(prices[c]) for c,q in positions.items())
        if not math.isclose(calculated,float(state["equity_eur"]),abs_tol=.02): errors.append("EQUITY_MISMATCH")
        if state.get("mode")!="PAPER_ONLY_DEVELOPMENT": errors.append("UNSAFE_MODE")
        if not isinstance(state.get("trades"),list): errors.append("MISSING_TRADES")
        if state.get("emergency_lock",{}).get("active") is True: errors.append("EMERGENCY_LOCK_ACTIVE")
        if state.get("safe_stop") is True: errors.append("DRAWDOWN_STOP_ACTIVE")
    except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
        errors.append("MALFORMED_STATE:"+type(exc).__name__)
    return {"ok":not errors,"errors":errors,"last_update_utc":state.get("last_update_utc"),"markets":len(state.get("latest_prices_eur",{}))}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--state",default="multi_state.json")
    parser.add_argument("--max-age-minutes",type=int,default=50)
    args=parser.parse_args()
    try:
        state=json.loads(Path(args.state).read_text(encoding="utf-8"))
        report=audit(state,max_age_minutes=args.max_age_minutes)
    except (OSError,ValueError) as exc:
        report={"ok":False,"errors":["STATE_UNAVAILABLE:"+type(exc).__name__]}
    print(json.dumps(report,ensure_ascii=False))
    if not report["ok"]: raise SystemExit(1)
if __name__=="__main__": main()
