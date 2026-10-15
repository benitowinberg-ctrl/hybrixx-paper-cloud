"""Read-only Kraken OHLC strategy comparison. Never submits orders or modifies paper funds."""
import argparse
import json
import math
import statistics
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PAIRS={"BTC":"XBTEUR","ETH":"ETHEUR","XRP":"XRPEUR","SOL":"SOLEUR","ADA":"ADAEUR","DOGE":"XDGEUR","DOT":"DOTEUR","LINK":"LINKEUR","LTC":"LTCEUR","AVAX":"AVAXEUR"}
FEE=.0026
SLIPPAGE=.001
STRATEGIES=("ma_4_12","ma_12_48","momentum_24","rsi_14")

def fetch_candles(symbol,interval=60):
    if symbol not in PAIRS: raise ValueError("Unsupported coin")
    url="https://api.kraken.com/0/public/OHLC?"+urllib.parse.urlencode({"pair":PAIRS[symbol],"interval":interval})
    req=urllib.request.Request(url,headers={"User-Agent":"HYBRIXX-Research/1"})
    with urllib.request.urlopen(req,timeout=20) as response: payload=json.load(response)
    if payload.get("error"): raise ValueError("Kraken: "+str(payload["error"]))
    key=next((k for k in payload["result"] if k!="last"),None)
    if key is None: raise ValueError("Missing candles")
    candles=[(int(r[0]),float(r[4])) for r in payload["result"][key][:-1]]
    if len(candles)<120: raise ValueError("Too few closed candles")
    if any(not math.isfinite(p) or p<=0 for _,p in candles): raise ValueError("Invalid price")
    if any(b[0]<=a[0] for a,b in zip(candles,candles[1:])): raise ValueError("Unordered candles")
    return candles

def signal(name,h):
    if name=="ma_4_12":
        return int(len(h)>=12 and statistics.mean(h[-4:])>statistics.mean(h[-12:])*1.003)
    if name=="ma_12_48":
        return int(len(h)>=48 and statistics.mean(h[-12:])>statistics.mean(h[-48:])*1.003)
    if name=="momentum_24":
        return int(len(h)>=25 and h[-1]/h[-25]>1.01)
    if name=="rsi_14":
        if len(h)<15:return 0
        changes=[h[i]-h[i-1] for i in range(len(h)-14,len(h))]
        gains=sum(max(0,x) for x in changes)
        losses=sum(max(0,-x) for x in changes)
        rsi=100 if losses==0 else 100-100/(1+gains/losses)
        return int(45<=rsi<=70)
    raise ValueError("Unknown strategy")

def simulate(closes,name,start,end):
    cash=500.0
    units=0.0
    trades=0
    peak=500.0
    drawdown=0.0
    for i in range(start,end):
        price=closes[i]
        # Previous completed candle only; execution at current candle close.
        target=signal(name,closes[:i])
        if target and not units:
            units=cash/(price*(1+SLIPPAGE)*(1+FEE))
            cash=0.0
            trades+=1
        elif not target and units:
            cash=units*price*(1-SLIPPAGE)*(1-FEE)
            units=0.0
            trades+=1
        equity=cash+units*price
        peak=max(peak,equity)
        drawdown=max(drawdown,(peak-equity)/peak)
    if units:
        cash=units*closes[end-1]*(1-SLIPPAGE)*(1-FEE)
        trades+=1
    return {"return_pct":round(100*(cash/500-1),3),"max_drawdown_pct":round(drawdown*100,3),"trades":trades,"ending_eur":round(cash,2)}

def research(candles):
    closes=[p for _,p in candles]
    if len(closes)<120: raise ValueError("Need 120 candles")
    split=int(len(closes)*.7)
    ranked=[]
    for name in STRATEGIES:
        training=simulate(closes,name,48,split)
        score=round(training["return_pct"]-.5*training["max_drawdown_pct"],3)
        ranked.append({"strategy":name,"training":training,"training_score":score})
    ranked.sort(key=lambda x:(-x["training_score"],x["strategy"]))
    selected=ranked[0]["strategy"]
    test=simulate(closes,selected,split,len(closes))
    buyhold=100*(closes[-1]/closes[split]*(1-SLIPPAGE)*(1-FEE)/((1+SLIPPAGE)*(1+FEE))-1)
    return {"candles":len(closes),"train_candles":split-48,"test_candles":len(closes)-split,
            "selection_basis":"training-only chronological 70/30 split",
            "strategies":ranked,"selected_strategy":selected,
            "out_of_sample":test,"out_of_sample_buy_hold_pct":round(buyhold,3),
            "warning":"Research only; short historical samples do not predict profits."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--interval",type=int,choices=(15,30,60,240,1440),default=60)
    p.add_argument("--output",default="strategy_report.json")
    args=p.parse_args()
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"mode":"RESEARCH_ONLY_NO_ORDERS",
            "interval_minutes":args.interval,"assets":{},"errors":{}}
    for coin in PAIRS:
        try: report["assets"][coin]=research(fetch_candles(coin,args.interval))
        except (ValueError,KeyError,TypeError,OSError,TimeoutError) as e:
            report["errors"][coin]=type(e).__name__+": "+str(e)[:180]
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"analyzed":len(report["assets"]),"errors":report["errors"]}))
    if not report["assets"]:raise SystemExit(1)
if __name__=="__main__":main()
