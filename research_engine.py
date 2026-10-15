#!/usr/bin/env python3
"""HYBRIXX unattended research: walk-forward PAPER evaluations; no orders."""
import csv,json,math
from intelligence_core import evaluate
from learning_history import update_history,trends
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATA=ROOT/"evolution-lab/data/xrp_eur_1h.csv"
OUT=ROOT/"research_state.json"
COST=(1+.0026)*(1+.001)-1
PARAMS={"MA":[8,12,16,24],"Momentum":[10,15,20,30],"Breakout":[10,15,20,30],"Donchian":[15,20,30,40],"RSI":[25,30,35,40]}
def mean(a,i,n): return sum(a[i-n+1:i+1])/n if i>=n-1 else float("nan")
def rsi(a,i,n=14):
    dif=[a[j]-a[j-1] for j in range(i-n+1,i+1)]
    up=sum(max(0,d) for d in dif); down=sum(max(0,-d) for d in dif)
    return 100 if down==0 else 100-100/(1+up/down)
def signal(a,i,name,p):
    if name=="MA":return int(mean(a,i,p)>mean(a,i,40))
    if name=="Momentum":return int(a[i]>a[i-p]*1.015)
    if name in ("Breakout","Donchian"):
        stop=10 if name=="Breakout" else 15
        if a[i]>max(a[i-p:i]):return 1
        if a[i]<min(a[i-stop:i]):return 0
        return None
    if name=="RSI":
        v=rsi(a,i)
        return 1 if v<p else 0 if v>60 else None
    raise ValueError(name)
def simulate(a,start,end,name,p):
    cash=500.;units=0.;peak=500.;dd=0.;orders=0
    for i in range(start,end):
        s=signal(a,i-1,name,p);price=a[i]
        if s==1 and units==0:
            units=cash/(price*(1+COST));cash=0;orders+=1
        elif s==0 and units>0:
            cash=units*price*(1-COST);units=0;orders+=1
        eq=cash+units*price;peak=max(peak,eq);dd=max(dd,1-eq/peak)
    final=cash+units*a[end-1]*(1-COST)
    return {"return_pct":round((final/500-1)*100,4),"drawdown_pct":round(dd*100,4),"orders":orders}
def main():
    with DATA.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    times=[datetime.fromisoformat(r["timestamp"].replace("Z","+00:00")) for r in rows]
    a=[float(r["close"]) for r in rows]
    if len(a)<300 or any(not math.isfinite(v) or v<=0 for v in a):raise ValueError("Invalid price history")
    if any((y-x).total_seconds()!=3600 for x,y in zip(times,times[1:])):raise ValueError("Irregular hourly data")
    # Several anchored rolling splits; no test data used to choose parameters.
    n=len(a);folds=[]
    for end in [int(n*.65),int(n*.8),n]:
        val_start=end-96;train_start=max(61,val_start-144)
        if train_start>=val_start:continue
        scores=[]
        for name,params in PARAMS.items():
            ranked=sorted(((simulate(a,train_start,val_start,name,p),p) for p in params),
                key=lambda z:z[0]["return_pct"]-.5*z[0]["drawdown_pct"],reverse=True)
            train,p=ranked[0];test=simulate(a,val_start,end,name,p)
            scores.append({"strategy":name,"parameter":p,"training":train,"out_of_sample":test})
        folds.append({"test_start":times[val_start].isoformat(),"test_end":times[end-1].isoformat(),"results":scores})
    stats=[]
    for name in PARAMS:
        tests=[next(x for x in fold["results"] if x["strategy"]==name)["out_of_sample"] for fold in folds]
        stats.append({"strategy":name,"mean_oos_return_pct":round(sum(t["return_pct"] for t in tests)/len(tests),4),
            "worst_oos_drawdown_pct":max(t["drawdown_pct"] for t in tests),
            "positive_folds":sum(t["return_pct"]>0 for t in tests),"folds":len(tests)})
    stats.sort(key=lambda x:(-x["mean_oos_return_pct"],x["worst_oos_drawdown_pct"]))
    out={"version":"0.1","generated_at_utc":datetime.now(timezone.utc).isoformat(),"last_candle_utc":times[-1].isoformat(),
         "mode":"RESEARCH_ONLY","market":"XRPEUR","data_points":n,"assumptions":{"fee_pct":.26,"slippage_pct":.1,"starting_eur":500},
         "evolution":{"method":"rolling out-of-sample parameter selection","ranking":stats,"folds":folds,
            "warning":"Short overlapping test windows, no statistical significance or verified alpha."},
         "copy_trading":{"status":"NO_VERIFIED_TRADER_SIGNALS","message":"No authenticated timestamped third-party trades; cannot infer trader skill from price candles."},
         "special_situations":{"status":"AWAITING_PRIMARY_FILINGS","message":"Fundamental filings and capital structure data not yet connected; no fabricated company scores."},
         "autonomous_learning":{"status":"AUTOMATED_PARAMETER_RESEARCH","message":"Scheduled re-evaluation of public candles, not a trained predictive AI model."}}
    out["intelligence_core"]=evaluate(out)
    history=update_history(ROOT/"learning_history.json",out)
    out["learning_history"]=trends(history)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Updated research_state.json:",n,"candles,",len(folds),"walk-forward folds")
if __name__=="__main__":main()
