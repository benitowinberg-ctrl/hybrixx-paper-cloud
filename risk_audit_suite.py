"""HYBRIXX read-only risk and audit diagnostics. No order access."""
import json,math
from datetime import datetime,timezone
from pathlib import Path
from paper_health import audit

def evaluate(state,now=None):
    now=now or datetime.now(timezone.utc)
    health=audit(state,now=now,max_age_minutes=60)
    errors=list(health["errors"])
    try:
        cash=float(state["cash_eur"])
        equity=float(state["equity_eur"])
        peak=float(state["peak_eur"])
        positions=state["positions"]
        prices=state["latest_prices_eur"]
        if not all(math.isfinite(x) for x in (cash,equity,peak)) or equity<=0 or peak<=0:
            raise ValueError("INVALID_BALANCE")
        exposure=sum(float(q)*float(prices[c]) for c,q in positions.items())
        drawdown=100*(peak-equity)/peak
        if drawdown>=15:errors.append("DRAWDOWN_LIMIT")
        if abs(equity-cash-exposure)>.02:errors.append("RECONCILIATION_FAILURE")
        closed=[float(t["realized_pnl_eur"]) for t in state.get("trades",[]) if t.get("side")=="SELL" and "realized_pnl_eur" in t]
        return {"timestamp":now.isoformat(),"mode":"AUDIT_ONLY","ok":not errors,"errors":errors,
          "treasury":{"cash_eur":cash,"equity_eur":equity,"exposure_eur":round(exposure,2),"cash_reserve_pct":round(100*cash/equity,2)},
          "risk":{"drawdown_pct":round(drawdown,3),"drawdown_limit_pct":15,"daily_loss_limit_enforced":False},
          "accounting":{"reconciliation_difference_eur":round(equity-cash-exposure,4),"recorded_fees_eur":state.get("fees_eur")},
          "trade_expectancy":{"closed_trades":len(closed),"average_realized_pnl_eur":round(sum(closed)/len(closed),4) if closed else None},
          "execution_quality":{"independent_spread_verified":False,"independent_slippage_verified":False},
          "exchange_reconciliation":{"verified":False},"tax_ledger":{"tax_ready":False},
          "kill_switch":{"active":bool(state.get("safe_stop")),"enforced_by_this_module":False},
          "trade_authorization":False}
    except (ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError) as exc:
        return {"mode":"AUDIT_ONLY","ok":False,"errors":errors+["MALFORMED:"+type(exc).__name__],"trade_authorization":False}

if __name__=="__main__":
    result=evaluate(json.loads(Path("multi_state.json").read_text()))
    Path("risk_audit_report.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"ok":result["ok"],"errors":result["errors"]}))
    if not result["ok"]:raise SystemExit(1)
