"""Research-only trade/no-trade gate. Never changes live or paper account state."""
import json
from pathlib import Path

MIN_TEST_CANDLES=100
MIN_TRADES=4
MAX_DRAWDOWN_PCT=10.0
MIN_EXCESS_RETURN_PCT=1.0

def decide(asset):
    reasons=[]
    if asset.get("test_candles",0)<MIN_TEST_CANDLES:
        reasons.append("INSUFFICIENT_HOLDOUT_DATA")
    outcome=asset.get("out_of_sample",{})
    if outcome.get("trades",0)<MIN_TRADES:
        reasons.append("TOO_FEW_TEST_TRADES")
    if outcome.get("return_pct",-999)<=0:
        reasons.append("NONPOSITIVE_NET_RETURN")
    if outcome.get("max_drawdown_pct",999)>MAX_DRAWDOWN_PCT:
        reasons.append("EXCESSIVE_DRAWDOWN")
    baseline=asset.get("out_of_sample_buy_hold_pct",999)
    if outcome.get("return_pct",-999)-baseline<MIN_EXCESS_RETURN_PCT:
        reasons.append("INSUFFICIENT_BENCHMARK_EDGE")
    return {"decision":"RESEARCH_CANDIDATE" if not reasons else "NO_TRADE",
            "reasons":reasons,
            "selected_strategy":asset.get("selected_strategy"),
            "note":"Research screening only, never an automatic trading authorization."}

def evaluate_report(report):
    return {"mode":"RESEARCH_ONLY_NO_ORDERS",
            "source_generated_utc":report.get("generated_utc"),
            "assets":{coin:decide(asset) for coin,asset in report.get("assets",{}).items()},
            "missing_or_failed_assets":report.get("errors",{})}

def main():
    report=json.loads(Path("strategy_report.json").read_text(encoding="utf-8"))
    result=evaluate_report(report)
    Path("strategy_gate_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v["decision"] for k,v in result["assets"].items()}))
if __name__=="__main__":main()
