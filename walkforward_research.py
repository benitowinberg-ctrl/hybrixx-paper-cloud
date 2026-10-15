"""Read-only historical-data validation and rolling walk-forward research.

Kraken's public OHLC endpoint returns only a limited recent window.
This module explicitly does NOT claim multi-year coverage. No orders.
"""
import hashlib
import json
import math
from datetime import datetime,timezone
from pathlib import Path
from strategy_research import PAIRS, STRATEGIES, fetch_candles, simulate

def validate(candles, interval_minutes=60, minimum=180):
    if len(candles)<minimum: raise ValueError("INSUFFICIENT_HISTORY")
    step=interval_minutes*60
    seen=set()
    missing=0
    for index,(timestamp,price) in enumerate(candles):
        if not isinstance(timestamp,int) or timestamp in seen:raise ValueError("DUPLICATE_OR_INVALID_TIMESTAMP")
        if not math.isfinite(price) or price<=0:raise ValueError("INVALID_PRICE")
        if index:
            delta=timestamp-candles[index-1][0]
            if delta<=0 or delta%step:raise ValueError("UNORDERED_OR_MISALIGNED")
            missing+=delta//step-1
        seen.add(timestamp)
    return {"candles":len(candles),"missing_intervals":missing,
            "coverage_pct":round(100*len(candles)/(len(candles)+missing),3),
            "start_utc":datetime.fromtimestamp(candles[0][0],timezone.utc).isoformat(),
            "end_utc":datetime.fromtimestamp(candles[-1][0],timezone.utc).isoformat(),
            "sha256":hashlib.sha256(json.dumps(candles,separators=(",",":")).encode()).hexdigest(),
            "sufficient_for_multi_year_validation":False}

def walk_forward(candles, train=360, test=120, step=120, interval_minutes=60):
    quality=validate(candles,interval_minutes,minimum=train+test)
    if quality["missing_intervals"]:raise ValueError("GAPPED_SERIES_REJECTED")
    prices=[price for _,price in candles]
    folds=[]
    for end in range(train,len(prices)-test+1,step):
        start=end-train
        # Rank strategies on TRAIN ONLY. A minimum 48-candle warmup is included.
        ranks=[]
        for strategy in STRATEGIES:
            training=simulate(prices,strategy,start+48,end)
            score=training["return_pct"]-.5*training["max_drawdown_pct"]
            ranks.append((score,strategy))
        ranks.sort(key=lambda item:(-item[0],item[1]))
        selected=ranks[0][1]
        tested=simulate(prices,selected,end,end+test)
        cash={"return_pct":0.,"max_drawdown_pct":0.,"trades":0,"ending_eur":500.}
        folds.append({"train_start":start,"train_end_exclusive":end,
                      "test_start":end,"test_end_exclusive":end+test,
                      "selected_strategy":selected,"out_of_sample":tested,
                      "cash_benchmark":cash})
    if not folds:raise ValueError("NO_VALID_FOLDS")
    returns=[f["out_of_sample"]["return_pct"] for f in folds]
    return {"data_quality":quality,"folds":folds,"fold_count":len(folds),
            "mean_holdout_return_pct":round(sum(returns)/len(returns),3),
            "positive_fold_fraction":round(sum(r>0 for r in returns)/len(returns),3),
            "total_holdout_trades":sum(f["out_of_sample"]["trades"] for f in folds),
            "decision":"RESEARCH_ONLY_NOT_AUTHORIZED",
            "warning":"Short-window research; do not use to authorize paper or real trades."}

def main():
    result={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "mode":"RESEARCH_ONLY_NO_ORDERS","interval_minutes":60,
            "assets":{},"errors":{},"limitations":"Recent Kraken OHLC only; not multi-year, not production authorization."}
    for coin in PAIRS:
        try:result["assets"][coin]=walk_forward(fetch_candles(coin))
        except (ValueError,TypeError,KeyError,OSError,TimeoutError) as exc:
            result["errors"][coin]=type(exc).__name__+": "+str(exc)[:160]
    Path("walkforward_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"assets":len(result["assets"]),"errors":result["errors"]}))
    if not result["assets"]:raise SystemExit(1)
if __name__=="__main__":main()
