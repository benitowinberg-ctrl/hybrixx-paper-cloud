"""Read-only HYBRIXX readiness audit. Never places orders or changes accounts."""
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from paper_trade_gate import COINS, approved_coins

def inspect(state, gate, human, now=None):
    now=now or datetime.now(timezone.utc)
    checks={}
    def check(name, condition):
        checks[name]=bool(condition)
    cash=state.get("cash_eur")
    prices=state.get("latest_prices_eur",{})
    positions=state.get("positions",{})
    check("01_paper_mode",state.get("mode")=="PAPER_ONLY_DEVELOPMENT")
    check("02_market_universe",set(prices)==set(COINS))
    check("03_price_finite",isinstance(prices,dict) and all(isinstance(v,(int,float)) and math.isfinite(v) and v>0 for v in prices.values()))
    check("04_cash_finite",isinstance(cash,(int,float)) and math.isfinite(cash) and cash>=0)
    check("05_positions_dictionary",isinstance(positions,dict))
    check("06_known_positions",isinstance(positions,dict) and set(positions).issubset(COINS))
    check("07_position_count",isinstance(positions,dict) and len(positions)<=3)
    check("08_position_quantities",isinstance(positions,dict) and all(isinstance(q,(int,float)) and math.isfinite(q) and q>0 for q in positions.values()))
    check("09_trades_journal",isinstance(state.get("trades"),list))
    check("10_equity_present",isinstance(state.get("equity_eur"),(int,float)) and math.isfinite(state["equity_eur"]))
    can_value=all(checks[k] for k in ("03_price_finite","04_cash_finite","06_known_positions","08_position_quantities","10_equity_present"))
    check("11_equity_reconciles",can_value and math.isclose(cash+sum(q*prices[c] for c,q in positions.items()),state["equity_eur"],abs_tol=.02))
    check("12_no_negative_equity",checks["10_equity_present"] and state["equity_eur"]>=0)
    check("13_peak_present",isinstance(state.get("peak_eur"),(int,float)) and state["peak_eur"]>=0)
    check("14_safe_stop_boolean",isinstance(state.get("safe_stop"),bool))
    lock=state.get("emergency_lock")
    check("15_emergency_lock_schema",lock is None or (isinstance(lock,dict) and lock.get("active") is True))
    check("16_signals_dictionary",isinstance(state.get("signals"),dict))
    check("17_history_dictionary",isinstance(state.get("history"),dict))
    check("18_trade_index",isinstance(state.get("tick_index"),int) and state["tick_index"]>=0)
    check("19_fee_accounting",isinstance(state.get("fees_eur"),(int,float)) and math.isfinite(state["fees_eur"]) and state["fees_eur"]>=0)
    check("20_research_modes",gate.get("mode")=="RESEARCH_ONLY_NO_ORDERS" and human.get("mode")=="RESEARCH_ONLY_NO_ORDERS")
    check("21_gate_present",isinstance(state.get("buy_gate"),dict) and state["buy_gate"].get("mode")=="FAIL_CLOSED_RESEARCH")
    authorized=approved_coins(gate,human,now)
    check("22_gate_approval_matches",checks["21_gate_present"] and set(state["buy_gate"].get("approved_coins",[])).issubset(COINS))
    check("23_no_unapproved_buy_gate",checks["22_gate_approval_matches"] and set(state["buy_gate"]["approved_coins"]).issubset(authorized))
    critical=("01_paper_mode","02_market_universe","03_price_finite","04_cash_finite","05_positions_dictionary","06_known_positions","07_position_count","08_position_quantities","10_equity_present","11_equity_reconciles","12_no_negative_equity","15_emergency_lock_schema","20_research_modes","21_gate_present","22_gate_approval_matches","23_no_unapproved_buy_gate")
    return {"mode":"READ_ONLY_AUDIT","checked_utc":now.isoformat(),"checks":checks,
            "passed":sum(checks.values()),"total":len(checks),
            "critical_failures":[k for k in critical if not checks[k]],
            "warnings":[k for k in checks if k not in critical and not checks[k]],
            "current_authorized_coins":sorted(authorized),
            "note":"Research audit only; no real-money authorization."}

def main():
    try:
        state=json.loads(Path("multi_state.json").read_text())
        gate=json.loads(Path("strategy_gate_report.json").read_text())
        human=json.loads(Path("human_strategy_comparison.json").read_text())
        result=inspect(state,gate,human)
    except (OSError,ValueError,TypeError) as e:
        result={"mode":"READ_ONLY_AUDIT","critical_failures":["INPUT_UNAVAILABLE"],"error":type(e).__name__}
    Path("readiness_audit.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
    if result["critical_failures"]:raise SystemExit(1)
if __name__=="__main__":main()
