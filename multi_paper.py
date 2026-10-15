"""HYBRIXX 10-coin paper engine: simulation only; no authenticated endpoints."""
import json
import math
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

COINS = {"BTC":"XBTEUR","ETH":"ETHEUR","XRP":"XRPEUR","SOL":"SOLEUR","ADA":"ADAEUR","DOGE":"XDGEUR","DOT":"DOTEUR","LINK":"LINKEUR","LTC":"LTCEUR","AVAX":"AVAXEUR"}
STATE = Path("multi_state.json")
FEE, SLIPPAGE = 0.0026, 0.001
def quotes():
    url = "https://api.kraken.com/0/public/Ticker?pair=" + ",".join(COINS.values())
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"HYBRIXX-Paper/3"}),timeout=20) as r:
        data=json.load(r)
    if data.get("error"): raise ValueError(str(data["error"]))
    result=data["result"]
    # Kraken response keys may be normalized; resolve by returned altname or explicit keys.
    found={}
    for name,pair in COINS.items():
        candidates=[pair, pair.replace("XBT","XXBT"), pair.replace("XDG","XXDG")]
        key=next((k for k in candidates if k in result),None)
        if key is None:
            # Some Kraken keys use X/Z prefix; resolve from AssetPairs in a future release.
            raise ValueError("Missing Kraken market: "+name)
        found[name]=float(result[key]["c"][0])
    return found

def advance(state, prices, stamp):
    state=json.loads(json.dumps(state))
    state.setdefault("cash_eur",500.0)
    state.setdefault("positions",{})
    state.setdefault("history",{})
    state.setdefault("trades",[])
    state.setdefault("peak_eur",500.0)
    state.setdefault("safe_stop",False)
    if state.get("last_update_utc")==stamp:return state
    if set(prices)!=set(COINS):raise ValueError("Incomplete quotes")
    for coin in COINS:
        price=float(prices[coin])
        if not math.isfinite(price) or price<=0:raise ValueError("Invalid quote")
        h=state["history"].setdefault(coin,[])
        if h and abs(price/h[-1]-1)>0.25:raise ValueError("Suspicious quote: "+coin)
        h.append(price)
        state["history"][coin]=h[-1000:]
    equity=state["cash_eur"]+sum(q*prices[c] for c,q in state["positions"].items())
    state["peak_eur"]=max(state["peak_eur"],equity)
    if equity<=state["peak_eur"]*0.85:state["safe_stop"]=True
    locked=state.get("emergency_lock",{}).get("active",False)
    for coin in COINS:
        h=state["history"][coin]
        if len(h)<12:continue
        fast=sum(h[-4:])/4
        slow=sum(h[-12:])/12
        price=prices[coin]
        qty=state["positions"].get(coin,0)
        if locked:continue
        if qty and (fast<slow*0.997 or price<=state["entry"][coin]*0.95 or price>=state["entry"][coin]*1.10):
            gross=qty*price*(1-SLIPPAGE)
            fee=gross*FEE
            state["cash_eur"]+=gross-fee
            state["positions"].pop(coin)
            state["entry"].pop(coin)
            state["trades"].append({"time_utc":stamp,"symbol":coin+"/EUR","side":"SELL","qty":qty,"net_eur":round(gross-fee,8),"fee_eur":round(fee,8)})
        elif not qty and not state["safe_stop"] and len(state["positions"])<3 and fast>slow*1.003:
            budget=min(state["cash_eur"],equity*0.10)
            if budget<15:continue
            fill=price*(1+SLIPPAGE)
            qty=math.floor(budget/(fill*(1+FEE))*1e8)/1e8
            cost=qty*fill*(1+FEE)
            if qty<=0 or cost>state["cash_eur"]:continue
            state["cash_eur"]-=cost
            state["positions"][coin]=qty
            state.setdefault("entry",{})[coin]=fill
            state["trades"].append({"time_utc":stamp,"symbol":coin+"/EUR","side":"BUY","qty":qty,"cost_eur":round(cost,8),"fee_eur":round(qty*fill*FEE,8)})
    state["cash_eur"]=round(state["cash_eur"],8)
    state["equity_eur"]=round(state["cash_eur"]+sum(q*prices[c] for c,q in state["positions"].items()),2)
    state["last_update_utc"]=stamp
    state["latest_prices_eur"]=prices
    return state

def main():
    prices=quotes()
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    updated=advance(state,prices,datetime.now(timezone.utc).isoformat())
    temp=STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(updated,indent=2)+"\n")
    os.replace(temp,STATE)
    print("PAPER ONLY",updated["equity_eur"],"EUR",len(updated["positions"]),"open positions")

if __name__=="__main__":main()
