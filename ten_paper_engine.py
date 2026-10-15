"""Ten autonomous, isolated virtual research ledgers. Never accesses exchange accounts."""
import csv,json,math
from datetime import datetime,timezone
from pathlib import Path

NAMES=("Alpha","Beta","Gamma","Delta","Epsilon","Zeta","Eta","Theta","Iota","Kappa")
PARAMS=((8,12,16,24),(10,15,20,30),(.8,1.2,1.6,2),(10,15,20,30),(25,30,35,40),(.015,.025,.035,.05),(15,20,30,40),(6,9,12,16),(1.5,1.8,2,2.4),(1,2,3))
FEE=.0026
SLIP=.001
START=500.
def mean(a,i,n):
    return sum(a[i-n+1:i+1])/n if i>=n-1 else float("nan")
def dev(a,i,n):
    m=mean(a,i,n)
    return math.sqrt(sum((x-m)**2 for x in a[i-n+1:i+1])/n)
def ema(a,n):
    v=a[0];out=[];k=2/(n+1)
    for x in a:
        v=k*x+(1-k)*v;out.append(v)
    return out
def features(a):
    e12,e26=ema(a,12),ema(a,26)
    mac=[x-y for x,y in zip(e12,e26)]
    return mac
def rsi(a,i,n=14):
    dif=[a[j]-a[j-1] for j in range(i-n+1,i+1)]
    up=sum(max(0,d) for d in dif);dn=sum(max(0,-d) for d in dif)
    return 100 if dn==0 else 100-100/(1+up/dn)
def signal(a,mac,id,p,i):
    x=a[i];m20=mean(a,i,20);m50=mean(a,i,50)
    if id==0:return int(mean(a,i,p)>mean(a,i,40))
    if id==1:return int(x>a[i-p]*1.015)
    if id==2:return 1 if x<m20-p*dev(a,i,20) else 0 if x>m20 else None
    if id==3:return 1 if x>max(a[i-p:i]) else 0 if x<min(a[i-10:i]) else None
    if id==4:
        value=rsi(a,i);return 1 if value<p else 0 if value>60 else None
    if id==5:return int(dev(a,i,20)/m20<p and x>m50)
    if id==6:return 1 if x>max(a[i-p:i]) else 0 if x<min(a[i-15:i]) else None
    if id==7:return int(mac[i]>mean(mac,i,p))
    if id==8:return 1 if x<m20-p*dev(a,i,20) else 0 if x>m20 else None
    if id==9:return int(sum((mean(a,i,10)>mean(a,i,40),x>a[i-20],x>m50))>=p)
    raise ValueError("Unknown strategy")
def backtest(a,mac,id,p,start,end):
    cash=START;units=0.;orders=0;peak=START;dd=0.
    for i in range(start,end):
        action=signal(a,mac,id,p,i-1)
        if action==1 and units==0:
            units=cash/(a[i]*(1+SLIP)*(1+FEE));cash=0.;orders+=1
        elif action==0 and units>0:
            cash=units*a[i]*(1-SLIP)*(1-FEE);units=0.;orders+=1
        equity=cash+units*a[i];peak=max(peak,equity);dd=max(dd,1-equity/peak)
    final=cash+units*a[end-1]*(1-SLIP)*(1-FEE)
    return {"return_pct":round(100*(final/START-1),4),"drawdown_pct":round(100*dd,4),"orders":orders}
def choose(a,mac,id):
    n=len(a);train_end=int(n*.6);val_end=int(n*.8)
    candidates=[]
    for p in PARAMS[id]:
        validation=backtest(a,mac,id,p,train_end,val_end)
        candidates.append((validation["return_pct"]-.5*validation["drawdown_pct"],p,validation))
    _,param,validation=max(candidates,key=lambda item:item[0])
    return param,validation,backtest(a,mac,id,param,val_end,n)
def validate(rows):
    if len(rows)<300:raise ValueError("Insufficient hourly history")
    stamps=[datetime.fromisoformat(r["timestamp"].replace("Z","+00:00")) for r in rows]
    prices=[float(r["close"]) for r in rows]
    if any(not math.isfinite(x) or x<=0 for x in prices):raise ValueError("Invalid close")
    if any((b-a).total_seconds()!=3600 for a,b in zip(stamps,stamps[1:])):raise ValueError("Missing hourly candles")
    return stamps,prices
def advance(path,stamps,prices,locked=True):
    """One virtual decision per distinct closed candle; no external or existing paper state touched."""
    path=Path(path)
    old={"version":"1","mode":"TEN_ISOLATED_VIRTUAL_PAPER_ACCOUNTS","systems":{}}
    if path.exists():old=json.loads(path.read_text(encoding="utf-8"))
    if old.get("mode")!="TEN_ISOLATED_VIRTUAL_PAPER_ACCOUNTS":raise ValueError("Invalid ledger mode")
    if set(old.get("systems",{}))-set(NAMES):raise ValueError("Unexpected strategy")
    mac=features(prices);stamp=stamps[-1].isoformat()
    systems={}
    for id,name in enumerate(NAMES):
        prior=old.get("systems",{}).get(name,{})
        if prior.get("last_candle_utc") and stamp<prior["last_candle_utc"]:
            raise ValueError("Out-of-order candle")
        param,validation,test=choose(prices,mac,id)
        # Choose on historical validation only. New live-forward virtual execution
        # begins on NEXT closed candle; never replay historical test as live profits.
        cash=float(prior.get("cash_eur",START));units=float(prior.get("units",0))
        trades=list(prior.get("trades",[]))
        if len(trades)>1000:raise ValueError("Ledger overflow")
        if not locked and prior.get("last_candle_utc")!=stamp and prior.get("last_candle_utc"):
            # Parameter from previous report, not freshly optimized on today's close.
            previous_param=prior["parameter"]
            action=signal(prices,mac,id,previous_param,len(prices)-2)
            price=prices[-1]
            if action==1 and units==0 and cash>0:
                units=cash/(price*(1+SLIP)*(1+FEE));cash=0.
                trades.append({"time_utc":stamp,"side":"BUY","price_eur":price,"parameter":previous_param})
            elif action==0 and units>0:
                cash=units*price*(1-SLIP)*(1-FEE);units=0.
                trades.append({"time_utc":stamp,"side":"SELL","price_eur":price,"parameter":previous_param})
        # Initial run records a baseline, never backdates virtual trades.
        equity=cash+units*prices[-1]*(1-SLIP)*(1-FEE)
        systems[name]={"last_candle_utc":stamp,"parameter":param,"cash_eur":round(cash,8),
            "units":round(units,10),"equity_eur":round(equity,4),
            "pnl_eur":round(equity-START,4),"validation":validation,"historical_test":test,
            "trades":trades,"status":"EMERGENCY_LOCK_ACTIVE" if locked else "VIRTUAL_PAPER_ONLY"}
    result={"version":"1","mode":"TEN_ISOLATED_VIRTUAL_PAPER_ACCOUNTS",
            "market":"XRPEUR","last_candle_utc":stamp,"starting_eur_per_system":START,
            "system_count":len(systems),"systems":systems,"emergency_lock_active":locked,
            "warning":"Ten independent 500 EUR virtual ledgers, not 500 EUR shared capital; no live orders. Only new closed candles create virtual decisions."}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result
def main():
    root=Path(__file__).resolve().parent
    with (root/"evolution-lab/data/xrp_eur_1h.csv").open(encoding="utf-8",newline="") as file:
        rows=list(csv.DictReader(file))
    stamps,prices=validate(rows)
    lock=json.loads((root/"state.json").read_text(encoding="utf-8")).get("emergency_lock")
    multi=json.loads((root/"multi_state.json").read_text(encoding="utf-8")).get("emergency_lock")
    if lock is not None and (not isinstance(lock,dict) or lock.get("active") is not True):raise ValueError("Invalid legacy lock")
    if multi is not None and (not isinstance(multi,dict) or multi.get("active") is not True):raise ValueError("Invalid multi lock")
    result=advance(root/"ten_paper_state.json",stamps,prices,locked=lock is not None or multi is not None)
    print("Ten isolated virtual ledgers:",result["system_count"],"last candle:",result["last_candle_utc"])
if __name__=="__main__":main()
