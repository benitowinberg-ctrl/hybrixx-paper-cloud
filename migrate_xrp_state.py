"""One-time, auditable legacy XRP paper account migration.
Never invent or add a second 500 EUR balance. Does not alter legacy state.json.
"""
import copy
import json
from pathlib import Path

def migrate(legacy):
    if not isinstance(legacy,dict) or "cash_eur" not in legacy:
        raise ValueError("Legacy account missing")
    cash=float(legacy["cash_eur"])
    units=float(legacy["xrp"])
    observations=legacy.get("observations",[])
    if not observations or not all("xrp_eur" in x for x in observations):
        raise ValueError("Missing XRP history")
    price=float(observations[-1]["xrp_eur"])
    equity=cash+units*price
    if abs(equity-float(legacy["equity_eur"]))>0.05:
        raise ValueError("Legacy equity does not reconcile")
    if "emergency_lock" in legacy:
        lock=legacy["emergency_lock"]
        if not isinstance(lock,dict) or lock.get("active") is not True:
            raise ValueError("Invalid legacy emergency lock")
    engine=legacy.get("paper_engine",{})
    result={
        "cash_eur":cash,
        "positions":{"XRP":units} if units else {},
        "entry":{"XRP":float(engine["entry_price_eur"])} if units else {},
        "cost_basis":{"XRP":float(engine["cost_basis_eur"])} if units else {},
        "history":{"XRP":[float(o["xrp_eur"]) for o in observations][-1000:]},
        "trades":copy.deepcopy(legacy.get("trades",[])),
        "peak_eur":float(engine.get("peak_equity_eur",500)),
        "safe_stop":bool(engine.get("safe_stop",False)),
        "realized_pnl_eur":float(engine.get("realized_pnl_eur",0)),
        "fees_eur":float(engine.get("fees_eur",0)),
        "last_update_utc":legacy["last_update_utc"],
        "equity_eur":round(equity,2),
        "unrealized_pnl_eur":round(units*price-float(engine.get("cost_basis_eur",0)),2),
        "total_pnl_eur":round(equity-500,2),
        "latest_prices_eur":{"XRP":price},
        "mode":"PAPER_ONLY_DEVELOPMENT",
        "migration":{"source":"state.json","source_last_update_utc":legacy["last_update_utc"],
                     "original_start_eur":500.0,"preserved_trade_count":len(legacy.get("trades",[]))}
    }
    if "emergency_lock" in legacy:
        result["emergency_lock"]=copy.deepcopy(legacy["emergency_lock"])
    return result

def main():
    source=Path("state.json")
    dest=Path("multi_state.json")
    if dest.exists():
        raise SystemExit("Refusing to overwrite existing multicoin ledger")
    migrated=migrate(json.loads(source.read_text(encoding="utf-8")))
    dest.write_text(json.dumps(migrated,indent=2)+"\n",encoding="utf-8")
    print("Migrated paper balance:",migrated["equity_eur"],"EUR")

if __name__=="__main__":
    main()
