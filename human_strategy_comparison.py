"""HYBRIXX: independently test human-inspired risk disciplines (not copied trades).
Read-only research; no changes to multi_state.json, no brokerage access.
"""
import json
import math
import statistics
from datetime import datetime,timezone
from pathlib import Path
from strategy_research import PAIRS, fetch_candles, simulate, FEE, SLIPPAGE

METHODS=("trend_volatility_gate","momentum_drawdown_guard","stay_in_cash")
def desired(method, prior):
    if method=="stay_in_cash": return False
    if len(prior)<60:return False
    fast=statistics.mean(prior[-12:])
    slow=statistics.mean(prior[-48:])
    changes=[prior[i]/prior[i-1]-1 for i in range(len(prior)-30,len(prior))]
    volatility=statistics.stdev(changes) if len(changes)>1 else 0
    if method=="trend_volatility_gate":
        return fast>slow*1.005 and volatility<0.045 and prior[-1]>slow
    if method=="momentum_drawdown_guard":
        peak=max(prior[-30:])
        return prior[-1]/prior[-25]>1.012 and prior[-1]>=peak*.95 and volatility<.06
    raise ValueError("Unknown method")

def evaluate(prices,method,start,end):
    cash=500.;qty=0.;peak=500.;maxdd=0.;trades=0
    for i in range(start,end):
        p=prices[i]
        want=desired(method,prices[:i])
        if want and qty==0:
            qty=cash/(p*(1+SLIPPAGE)*(1+FEE));cash=0.;trades+=1
        elif not want and qty:
            cash=qty*p*(1-SLIPPAGE)*(1-FEE);qty=0.;trades+=1
        equity=cash+qty*p
        peak=max(peak,equity)
        maxdd=max(maxdd,(peak-equity)/peak)
    if qty:
        cash=qty*prices[end-1]*(1-SLIPPAGE)*(1-FEE);trades+=1
    return {"ending_eur":round(cash,2),"return_pct":round((cash/500-1)*100,3),
            "max_drawdown_pct":round(maxdd*100,3),"trades":trades}

def compare(candles):
    closes=[p for _,p in candles]
    if len(closes)<180:raise ValueError("Need at least 180 closed candles")
    split=int(len(closes)*.7)
    ranking=[]
    for method in METHODS:
        training=evaluate(closes,method,60,split)
        ranking.append({"method":method,"training":training,
                        "training_score":round(training["return_pct"]-.5*training["max_drawdown_pct"],3)})
    ranking.sort(key=lambda x:(-x["training_score"],x["method"]))
    selected=ranking[0]["method"]
    holdout=evaluate(closes,selected,split,len(closes))
    baseline=simulate(closes,"ma_12_48",split,len(closes))
    return {"selection":"training-only 70/30 chronological holdout",
            "train_candles":split-60,"test_candles":len(closes)-split,
            "training_ranking":ranking,"selected":selected,
            "out_of_sample":holdout,"existing_ma_12_48_baseline":baseline,
            "caution":"No-trade cash is an eligible strategy; holdout is not a profit guarantee."}

def main():
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "mode":"RESEARCH_ONLY_NO_ORDERS","methodology":"Human-inspired discipline, not human transaction replication",
            "assets":{},"errors":{}}
    for coin in PAIRS:
        try:report["assets"][coin]=compare(fetch_candles(coin))
        except (ValueError,KeyError,TypeError,OSError,TimeoutError) as e:
            report["errors"][coin]=type(e).__name__+": "+str(e)[:180]
    Path("human_strategy_comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"analyzed":len(report["assets"]),"errors":report["errors"]}))
    if not report["assets"]:raise SystemExit(1)
if __name__=="__main__":main()
