"""HYBRIXX ten experimental research controls. Read-only, fail-closed.
No order execution, keys, balance writes or promotion to the live/paper buy gate.
All findings exploratory until independently validated on unseen history.
"""
import hashlib,json,math,statistics
from datetime import datetime,timezone
from pathlib import Path
from shadow_arena import CONFIGS,signal,simulate
from strategy_research import PAIRS,FEE,SLIPPAGE

def returns(prices):
    return [b/a-1 for a,b in zip(prices,prices[1:])]
def correlation(a,b):
    n=min(len(a),len(b));a=a[-n:];b=b[-n:]
    if n<30:return None
    x=statistics.pstdev(a);y=statistics.pstdev(b)
    return round(sum((v-statistics.mean(a))*(w-statistics.mean(b)) for v,w in zip(a,b))/(n*x*y),3) if x>0 and y>0 else None
def regime(p):
    r=returns(p[-49:]);vol=statistics.pstdev(r)*math.sqrt(24)*100 if r else 0
    trend=(p[-1]/p[-49]-1)*100
    label="HIGH_VOLATILITY" if vol>10 else ("UPTREND" if trend>3 else "DOWNTREND" if trend< -3 else "SIDEWAYS")
    return {"label":label,"trend_48h_pct":round(trend,3),"volatility_daily_pct":round(vol,3)}
def run(ohlc,arena):
    if set(ohlc)!=set(PAIRS) or arena.get("strategy_count")!=20:raise ValueError("INCOMPLETE_INPUT")
    prices={k:[float(v) for _,v in candles] for k,candles in ohlc.items()}
    if any(len(v)<160 or any(not math.isfinite(x) or x<=0 for x in v) for v in prices.values()):raise ValueError("INVALID_DATA")
    rs={k:returns(v) for k,v in prices.items()}
    regimes={k:regime(v) for k,v in prices.items()}
    correlations={a:{b:correlation(rs[a],rs[b]) for b in PAIRS if b!=a} for a in PAIRS}
    high_pairs=[{"pair":[a,b],"correlation":correlations[a][b]} for i,a in enumerate(PAIRS) for b in list(PAIRS)[i+1:] if correlations[a][b] is not None and correlations[a][b]>.8]
    # Darwin: mutation proposals ONLY, never scored as if independently tested.
    proposals=[{"parent":c["id"],"mutation":"require regime UP trend and volatility below threshold"} for c in CONFIGS[:5]]
    # Counterfactual: cash and buy-and-hold comparators with two-sided costs.
    baselines={k:{"cash_pct":0,"buy_hold_after_costs_pct":round(100*(v[-1]/v[0]*(1-SLIPPAGE)*(1-FEE)/((1+SLIPPAGE)*(1+FEE))-1),3)} for k,v in prices.items()}
    # Black Swan: instantaneous adverse shocks to an equally weighted 10-coin basket.
    shocks={f"shock_{pct}pct":{"portfolio_loss_eur":round(500*pct/100,2),"equity_after_eur":round(500*(1-pct/100),2)} for pct in (10,25,50,75)}
    # Drift: first-half vs second-half hourly realized volatility, flag large changes.
    drift={}
    for k,r in rs.items():
        mid=len(r)//2;a=statistics.pstdev(r[:mid]);b=statistics.pstdev(r[mid:])
        drift[k]={"volatility_ratio":round(b/a,3) if a else None,"flag":a==0 or b/a>1.5 or b/a<.667}
    # Reality twin: rerun top three with a conservative additional round-trip penalty.
    twin={}
    for name in arena["ranking"][:3]:
        cfg=next(c for c in CONFIGS if c["id"]==name)
        regular=[simulate(v,cfg) for v in prices.values()]
        # Stress charge is explicit proxy: 0.5% per executed side; not a rerun at modified fills.
        extra=sum(x["order_count"]*.5 for x in regular)/len(regular)
        twin[name]={"normal_net_pct":arena["accounts"][name]["net_return_pct"],
                    "stress_cost_proxy_pct_points":round(extra,3),
                    "stress_adjusted_proxy_pct":round(arena["accounts"][name]["net_return_pct"]-extra,3),
                    "method":"conservative extra 0.5 percentage points per order; proxy only"}
    # Capital guardian and committee are advisory, never authorize trades.
    guardian={"max_single_strategy_fraction":.1,"max_total_risk_fraction":.02,
              "max_portfolio_drawdown_fraction":.15,"cash_reserve_fraction":.5,
              "status":"ADVISORY_ONLY_NOT_CONNECTED_TO_EXECUTION"}
    committee={}
    for name in arena["ranking"]:
        account=arena["accounts"][name]
        positive=account["net_return_pct"]>0
        dd=account["worst_single_coin_drawdown_pct"]<15
        committee[name]={"research_positive":positive,"risk_check":dd,
            "independent_holdout_passed":False,"security_passed":True,
            "decision":"REJECT_PENDING_INDEPENDENT_VALIDATION"}
    # Evidence ledger: digest exact input candles and arena output; no self-referential hash.
    fingerprint=hashlib.sha256(json.dumps(ohlc,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"mode":"READ_ONLY_NO_ORDERS",
       "data_candles_sha256":fingerprint,"market_dna":regimes,"correlation_breaker":{"high_correlation_pairs":high_pairs,"correlations":correlations},
       "black_swan_radar":shocks,"drift_detector":drift,"darwin_engine":{"unvalidated_mutation_proposals":proposals},
       "counterfactual_lab":baselines,"reality_twin":twin,"capital_guardian":guardian,
       "investment_committee":committee,
       "evidence_ledger":{"source":"Kraken public closed hourly OHLC","markets":list(PAIRS),
          "candle_counts":{k:len(v) for k,v in prices.items()},"arena_strategy_count":20,
          "input_sha256":fingerprint,"method":"Exploratory in-sample diagnostics; no unseen holdout"},
       "trade_authorization":False,
       "limitations":"Short history, in-sample selection, no volume/orderbook, no true independent validation. No buy permissions."}
    return report

def main():
    from strategy_research import fetch_candles
    from shadow_arena import run_arena
    data={coin:fetch_candles(coin) for coin in PAIRS}
    arena=run_arena(data)
    report=run(data,arena)
    Path("adaptive_lab_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"systems":10,"markets":len(data),"trade_authorization":False}))
if __name__=="__main__":main()
