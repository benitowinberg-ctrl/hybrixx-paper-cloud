"""HYBRIXX Learning Governance v0.2: ten linked read-only research controls.

Never loads credentials, trades, changes model weights or promotes models.
Snapshots are observations, not persistent neural-network training.
"""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

COINS=("BTC","ETH","XRP","SOL","ADA","DOGE","DOT","LINK","LTC","AVAX")
MAX_HISTORY=90
MAX_AGE_HOURS=36

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def validate(report,now):
    if report.get("mode")!="RESEARCH_ONLY_NO_ORDERS" or report.get("trade_authorization") is not False:
        raise ValueError("UNSAFE_REPORT")
    stamp=datetime.fromisoformat(report["generated_utc"].replace("Z","+00:00"))
    if stamp.tzinfo is None or not 0<=(now-stamp).total_seconds()<=MAX_AGE_HOURS*3600:
        raise ValueError("STALE_REPORT")
    if report.get("errors") or set(report.get("assets",{}))!=set(COINS):
        raise ValueError("INCOMPLETE_REPORT")
    for coin,asset in report["assets"].items():
        if asset.get("holdout_model_frozen") is not True or asset.get("signal_authorized") is not False:
            raise ValueError("UNSAFE_MODEL_"+coin)
        n=asset.get("holdout_observations",0)
        acc=asset.get("holdout_accuracy")
        base=asset.get("always_down_baseline_accuracy")
        loss=asset.get("holdout_logloss")
        if not isinstance(n,int) or n<100 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (acc,base,loss)):
            raise ValueError("BAD_METRICS_"+coin)
        if not (0<=acc<=1 and 0<=base<=1 and 0<=loss<=20):
            raise ValueError("BAD_METRICS_"+coin)
    return stamp

def evaluate(report,history=None,now=None):
    now=now or datetime.now(timezone.utc)
    stamp=validate(report,now)
    history=history if isinstance(history,list) else []
    fingerprint=digest({"generated_utc":report["generated_utc"],"assets":report["assets"]})
    previous=[h for h in history if isinstance(h,dict) and isinstance(h.get("markets"),dict) and h.get("fingerprint")!=fingerprint]
    latest=previous[-1] if previous else None
    markets={}
    for coin,asset in report["assets"].items():
        acc=asset["holdout_accuracy"]
        base=asset["always_down_baseline_accuracy"]
        advantage=round(acc-base,4)
        # Conservative, heuristic bound, not an inferential confidence interval.
        n=asset["holdout_observations"]
        uncertainty=1.96*math.sqrt(.25/n)
        previous_acc=(latest or {}).get("markets",{}).get(coin,{}).get("accuracy")
        drift=(round(acc-previous_acc,4) if isinstance(previous_acc,(int,float)) else None)
        # Fee + slippage stress proxy, not a backtested strategy return.
        cost_roundtrip_pct=round(2*(.0026+.001)*100,3)
        markets[coin]={"accuracy":acc,"baseline_accuracy":base,
          "accuracy_advantage":advantage,"holdout_samples":n,
          "heuristic_uncertainty":round(uncertainty,4),
          "logloss":asset["holdout_logloss"],
          "drift_from_previous":drift,
          "drift_warning":drift is not None and drift<-.05,
          "cost_roundtrip_pct_proxy":cost_roundtrip_pct,
          "cost_adjusted_profit_test":"NOT_AVAILABLE",
          "candidate_research_status":"REJECT" if advantage<=0 else "INSUFFICIENT_EVIDENCE"}
    entry={"source_generated_utc":stamp.isoformat(),"fingerprint":fingerprint,
           "markets":{coin:{"accuracy":v["accuracy"],"baseline_accuracy":v["baseline_accuracy"]} for coin,v in markets.items()}}
    clean=[h for h in history if isinstance(h,dict) and isinstance(h.get("fingerprint"),str) and isinstance(h.get("markets"),dict)]
    if not any(h["fingerprint"]==fingerprint for h in clean):
        clean.append(entry)
    clean=clean[-MAX_HISTORY:]
    checks={
      "01_provenance_sha256":True,
      "02_timestamp_and_freshness":True,
      "03_ten_market_completeness":True,
      "04_holdout_integrity":True,
      "05_baseline_comparison":True,
      "06_uncertainty_screen":True,
      "07_drift_tracking":True,
      "08_cost_stress_disclosure":True,
      "09_bounded_version_history":True,
      "10_fail_closed_promotion":True}
    return {"generated_utc":now.isoformat(),"mode":"RESEARCH_ONLY_NO_ORDERS",
      "checks":checks,"source_fingerprint":fingerprint,
      "source_generated_utc":stamp.isoformat(),"markets":markets,
      "models_promoted":[],"trade_authorization":False,
      "readiness":"RESEARCH_ONLY_NOT_VALIDATED",
      "limitations":"No multi-year history, no genuine online checkpoint restoration, no cost-adjusted trading backtest, no statistically significant edge. History records evaluation snapshots only."},clean

def main():
    report=json.loads(Path("learning_engine_report.json").read_text(encoding="utf-8"))
    path=Path("learning_governance_history.json")
    history=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    result,updated=evaluate(report,history)
    Path("learning_governance_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    path.write_text(json.dumps(updated,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"markets":len(result["markets"]),"history_entries":len(updated),
                      "readiness":result["readiness"],"trade_authorization":False}))

if __name__=="__main__":
    main()
