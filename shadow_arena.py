"""HYBRIXX Shadow Arena: 20 isolated virtual strategy accounts.

Research-only: no broker access, no modifications to multi_state.json,
no connection to the production paper buy gate. Uses closed Kraken candles.
"""
import json,math,statistics
from datetime import datetime,timezone
from pathlib import Path
from strategy_research import PAIRS,fetch_candles,FEE,SLIPPAGE

INITIAL=500.0
# Twenty genuinely distinct, deterministic signal configurations.
CONFIGS=tuple(
    [{"id":f"trend_{fast}_{slow}","kind":"trend","fast":fast,"slow":slow}
     for fast,slow in ((3,12),(4,16),(6,24),(8,32),(12,48),(16,64),(24,96),(32,128))]
    +[{"id":f"momentum_{look}_{threshold}","kind":"momentum","look":look,"threshold":threshold}
      for look,threshold in ((6,.005),(12,.01),(24,.015),(48,.02),(72,.03),(96,.04))]
    +[{"id":f"breakout_{look}","kind":"breakout","look":look}
      for look in (12,24,48)]
    +[{"id":f"reversion_{look}","kind":"reversion","look":look}
      for look in (12,24,48)]
)

def signal(cfg,history):
    if cfg["kind"]=="trend":
        a,b=cfg["fast"],cfg["slow"]
        return len(history)>=b and statistics.mean(history[-a:])>statistics.mean(history[-b:])*1.003
    if cfg["kind"]=="momentum":
        n=cfg["look"]
        return len(history)>n and history[-1]/history[-n-1]-1>cfg["threshold"]
    if cfg["kind"]=="breakout":
        n=cfg["look"]
        return len(history)>n and history[-1]>max(history[-n-1:-1])
    if cfg["kind"]=="reversion":
        n=cfg["look"]
        return len(history)>=n and history[-1]<statistics.mean(history[-n:])*.98
    raise ValueError("UNKNOWN_STRATEGY")

def simulate(prices,cfg,initial=INITIAL):
    if len(prices)<160 or any(not math.isfinite(float(p)) or p<=0 for p in prices):
        raise ValueError("INVALID_HISTORY")
    cash=float(initial);qty=0.;peak=cash;max_dd=0.;orders=[];equity_curve=[]
    # Decision uses completed prior candles; fills at current candle close.
    for i,price in enumerate(prices):
        desired=bool(signal(cfg,prices[:i]))
        if desired and qty==0:
            qty=cash/(price*(1+SLIPPAGE)*(1+FEE))
            orders.append({"index":i,"side":"BUY","price":price,"fee_eur":round(qty*price*(1+SLIPPAGE)*FEE,6)})
            cash=0.
        elif not desired and qty>0:
            proceeds=qty*price*(1-SLIPPAGE)*(1-FEE)
            orders.append({"index":i,"side":"SELL","price":price,"fee_eur":round(qty*price*(1-SLIPPAGE)*FEE,6)})
            cash=proceeds;qty=0.
        equity=cash+qty*price
        peak=max(peak,equity)
        max_dd=max(max_dd,(peak-equity)/peak)
        equity_curve.append(round(equity,4))
    if qty>0:
        price=prices[-1]
        cash=qty*price*(1-SLIPPAGE)*(1-FEE)
        orders.append({"index":len(prices)-1,"side":"SELL","reason":"MARK_TO_CASH","price":price})
        qty=0
    return {"initial_eur":initial,"final_eur":round(cash,2),
            "net_return_pct":round(100*(cash/initial-1),3),
            "max_drawdown_pct":round(max_dd*100,3),
            "order_count":len(orders),"fees_and_slippage":"0.26% fee and 0.1% slippage per side",
            "orders":orders[-25:],"equity_curve":equity_curve[-100:]}

def run_arena(series):
    if set(series)!=set(PAIRS):raise ValueError("ALL_TEN_MARKETS_REQUIRED")
    if len(CONFIGS)!=20 or len({c["id"] for c in CONFIGS})!=20:raise ValueError("CONFIGURATION_ERROR")
    accounts={}
    for cfg in CONFIGS:
        per_coin={}
        for coin in PAIRS:
            candles=series[coin]
            if len(candles)<160:raise ValueError("INSUFFICIENT_HISTORY_"+coin)
            per_coin[coin]=simulate([p for _,p in candles],cfg)
        # Separate 500 EUR test account per strategy, split equally across ten coin sleeves.
        # Ten independent 50 EUR sleeves; each sleeve's result is scaled from a 500 EUR simulation.
        final=sum(v["final_eur"] for v in per_coin.values())/len(per_coin)
        worst=max(v["max_drawdown_pct"] for v in per_coin.values())
        accounts[cfg["id"]]={"configuration":cfg,"initial_eur":INITIAL,
          "final_eur":round(final,2),"net_return_pct":round((final/INITIAL-1)*100,3),
          "worst_single_coin_drawdown_pct":worst,
          "orders":sum(v["order_count"] for v in per_coin.values()),
          "markets":{c:{"return_pct":v["net_return_pct"],"orders":v["order_count"]} for c,v in per_coin.items()}}
    ranking=sorted(accounts,key=lambda k:(-accounts[k]["net_return_pct"],accounts[k]["worst_single_coin_drawdown_pct"],k))
    return {"generated_utc":datetime.now(timezone.utc).isoformat(),
      "mode":"SHADOW_RESEARCH_ONLY_NO_ORDERS","initial_per_strategy_eur":INITIAL,
      "aggregate_hypothetical_initial_eur":len(accounts)*INITIAL,
      "market_count":len(series),"strategy_count":len(accounts),
      "accounts":accounts,"ranking":ranking,
      "trade_authorization":False,
      "warning":"In-sample exploratory competition; rankings do not demonstrate out-of-sample profitability."}

def main():
    series={coin:fetch_candles(coin) for coin in PAIRS}
    result=run_arena(series)
    Path("shadow_arena_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"strategies":result["strategy_count"],"markets":result["market_count"],"leader":result["ranking"][0]}))
if __name__=="__main__":main()
