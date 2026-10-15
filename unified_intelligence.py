"""Unified read-only HYBRIXX intelligence council.

Combines existing research evidence without granting orders or modifying account state.
Missing, stale or contradictory evidence fails closed.
"""
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from paper_trade_gate import COINS
from risk_audit_suite import evaluate

MAX_AGE=timedelta(hours=36)
def freshness(report,now):
    try:
        stamp=report.get("generated_utc") or report.get("timestamp")
        t=datetime.fromisoformat(stamp.replace("Z","+00:00"))
        return t.tzinfo is not None and timedelta(0)<=now-t<=MAX_AGE
    except (AttributeError,TypeError,ValueError,OverflowError):
        return False

def synthesize(state,inputs,now=None):
    now=now or datetime.now(timezone.utc)
    risk=evaluate(state,now)
    checks={}
    for name in ("strategy","walkforward","robustness","arena","adaptive","human","gate"):
        data=inputs.get(name)
        checks[name]={"present":isinstance(data,dict),"fresh":isinstance(data,dict) and freshness(data,now)}
    arena=inputs.get("arena") or {}
    adaptive=inputs.get("adaptive") or {}
    checks["arena"]["twenty_strategies"]=arena.get("strategy_count")==20
    checks["adaptive"]["ten_research_modules"]=all(k in adaptive for k in (
      "market_dna","correlation_breaker","black_swan_radar","drift_detector",
      "darwin_engine","counterfactual_lab","reality_twin","capital_guardian",
      "evidence_ledger","investment_committee"))
    checks["adaptive"]["research_only"]=adaptive.get("trade_authorization") is False
    checks["arena"]["research_only"]=arena.get("trade_authorization") is False
    reasons=[]
    if not risk.get("ok"):reasons.append("RISK_AUDIT_FAILED")
    for name,c in checks.items():
        if not all(c.values()):reasons.append("UNVERIFIED_"+name.upper())
    if set(state.get("latest_prices_eur",{}))!=set(COINS):reasons.append("INCOMPLETE_MARKETS")
    return {"generated_utc":now.isoformat(),"mode":"UNIFIED_RESEARCH_ONLY",
      "risk_audit":risk,"evidence_checks":checks,
      "research_status":"EVIDENCE_COMPLETE" if not reasons else "INSUFFICIENT_EVIDENCE",
      "veto_reasons":reasons,"approved_real_trades":[],"approved_paper_buys":[],
      "trade_authorization":False,
      "architecture":"One advisory council; independent execution gate unchanged",
      "limitations":"Research reports may use different market snapshots; no consensus signal is authorized."}

FILES={"strategy":"strategy_report.json","walkforward":"walkforward_report.json",
 "robustness":"robustness_report.json","arena":"shadow_arena_report.json",
 "adaptive":"adaptive_lab_report.json","human":"human_strategy_comparison.json",
 "gate":"strategy_gate_report.json"}
def main():
    state=json.loads(Path("multi_state.json").read_text(encoding="utf-8"))
    inputs={}
    for name,path in FILES.items():
        try:inputs[name]=json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError,ValueError):inputs[name]=None
    result=synthesize(state,inputs)
    Path("unified_intelligence_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["research_status"],"vetoes":result["veto_reasons"],"trade_authorization":False}))
if __name__=="__main__":main()
