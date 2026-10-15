"""Offline walk-forward evaluator for ten-market HYBRIXX paper engine.
Input CSV columns: time_utc,BTC,ETH,XRP,SOL,ADA,DOGE,DOT,LINK,LTC,AVAX.
All prices must be historical observations in chronological order. No fabricated data.
"""
import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from multi_paper import COINS, advance

def load_rows(path):
    rows=[]
    with Path(path).open(newline="",encoding="utf-8") as stream:
        for raw in csv.DictReader(stream):
            timestamp=raw["time_utc"]
            dt=datetime.fromisoformat(timestamp.replace("Z","+00:00"))
            if dt.tzinfo is None:
                raise ValueError("Timezone required")
            prices={c:float(raw[c]) for c in COINS}
            if any(not math.isfinite(v) or v<=0 for v in prices.values()):
                raise ValueError("Invalid CSV price")
            if rows and dt<=rows[-1][0]:
                raise ValueError("CSV must be chronological")
            rows.append((dt,timestamp,prices))
    if len(rows)<24:
        raise ValueError("At least 24 observations required")
    return rows

def evaluate(rows):
    state={}
    equity_curve=[]
    for _,timestamp,prices in rows:
        state=advance(state,prices,timestamp)
        equity_curve.append(state["equity_eur"])
    peak=500.0
    max_drawdown=0.0
    for equity in equity_curve:
        peak=max(peak,equity)
        max_drawdown=max(max_drawdown,(peak-equity)/peak)
    return {"observations":len(rows),"trades":len(state["trades"]),
            "starting_eur":500.0,"ending_eur":state["equity_eur"],
            "net_pnl_eur":round(state["equity_eur"]-500,2),
            "return_pct":round((state["equity_eur"]/500-1)*100,3),
            "max_drawdown_pct":round(max_drawdown*100,3),
            "realized_pnl_eur":round(state["realized_pnl_eur"],2),
            "fees_eur":round(state["fees_eur"],2),
            "open_positions":list(state["positions"])}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("csv",help="historical ten-market EUR close CSV")
    parser.add_argument("--output",default="backtest_report.json")
    args=parser.parse_args()
    rows=load_rows(args.csv)
    # This is a chronological simulation, NOT a claim of out-of-sample validation.
    report=evaluate(rows)
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
