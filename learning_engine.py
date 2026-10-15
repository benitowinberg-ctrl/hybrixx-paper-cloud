"""HYBRIXX Learning Engine v0.1 — deterministic online market learner.

Inspired by River's predict-then-learn pattern. Standard-library only.
Strictly research-only: no orders, account mutations, or model promotion.
"""
import json
import math
from datetime import datetime,timezone
from pathlib import Path
from strategy_research import PAIRS,fetch_candles

FEATURE_NAMES=("return_1","return_6","return_24","volatility_12","trend_12_48")
MIN_CANDLES=160

def features(prices,i):
    """Features available at close i; label is close i+1 versus close i."""
    if i<48:raise ValueError("INSUFFICIENT_CONTEXT")
    r1=prices[i]/prices[i-1]-1
    r6=prices[i]/prices[i-6]-1
    r24=prices[i]/prices[i-24]-1
    recent=[prices[j]/prices[j-1]-1 for j in range(i-11,i+1)]
    avg=sum(recent)/len(recent)
    vol=math.sqrt(sum((x-avg)**2 for x in recent)/len(recent))
    trend=sum(prices[i-11:i+1])/12/(sum(prices[i-47:i+1])/48)-1
    return (r1,r6,r24,vol,trend)

def sigmoid(x):
    if x>=0:
        return 1/(1+math.exp(-min(x,50)))
    e=math.exp(max(x,-50))
    return e/(1+e)

class OnlineLogistic:
    def __init__(self,rate=.04):
        self.weights=[0.0]*len(FEATURE_NAMES)
        self.bias=0.0
        self.rate=rate
        self.samples=0
    def predict_one(self,x):
        if len(x)!=len(self.weights):raise ValueError("INVALID_FEATURES")
        return sigmoid(self.bias+sum(w*v for w,v in zip(self.weights,x)))
    def learn_one(self,x,y):
        if y not in (0,1):raise ValueError("INVALID_LABEL")
        p=self.predict_one(x)
        error=p-y
        for j,v in enumerate(x):
            self.weights[j]-=self.rate*error*v
        self.bias-=self.rate*error
        self.samples+=1

def run_market(candles):
    if len(candles)<MIN_CANDLES:raise ValueError("INSUFFICIENT_HISTORY")
    stamps=[t for t,_ in candles]
    prices=[float(p) for _,p in candles]
    if any(not math.isfinite(p) or p<=0 for p in prices):raise ValueError("INVALID_PRICE")
    if any(b<=a for a,b in zip(stamps,stamps[1:])):raise ValueError("INVALID_TIMESTAMPS")
    # Scale bounded features by fixed constants; no future-fit scaler.
    def vector(i):
        x=features(prices,i)
        return tuple(max(-5.,min(5.,v*s)) for v,s in zip(x,(20,10,5,30,10)))
    model=OnlineLogistic()
    split=max(100,int(len(prices)*.8))
    train_count=0
    # Strict predict -> evaluate -> learn, with only realized next-candle labels.
    for i in range(48,split-1):
        x=vector(i)
        model.predict_one(x)
        label=int(prices[i+1]>prices[i])
        model.learn_one(x,label)
        train_count+=1
    # Frozen model: unseen last 20%, no learning on test data.
    correct=0
    logloss=0.
    baseline_correct=0
    count=0
    predictions=[]
    for i in range(split,len(prices)-1):
        p=model.predict_one(vector(i))
        y=int(prices[i+1]>prices[i])
        correct+=int((p>=.5)==bool(y))
        baseline_correct+=int(y==0)
        logloss-=y*math.log(max(p,1e-12))+(1-y)*math.log(max(1-p,1e-12))
        count+=1
        if len(predictions)<5:
            predictions.append({"timestamp":stamps[i],"probability_up":round(p,5),"realized_up":bool(y)})
    if count<25:raise ValueError("INSUFFICIENT_HOLDOUT")
    return {"train_observations":train_count,"holdout_observations":count,
            "holdout_accuracy":round(correct/count,4),
            "always_down_baseline_accuracy":round(baseline_correct/count,4),
            "holdout_logloss":round(logloss/count,5),
            "model":"online_logistic_sgd","feature_names":list(FEATURE_NAMES),
            "model_weights":[round(w,7) for w in model.weights],
            "model_bias":round(model.bias,7),
            "test_predictions_sample":predictions,
            "holdout_model_frozen":True,
            "signal_authorized":False}

def run_all(series):
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "mode":"RESEARCH_ONLY_NO_ORDERS",
            "method":"Chronological prequential train; frozen final 20 percent holdout",
            "assets":{},"errors":{},"trade_authorization":False,
            "limitations":"Hourly short-history next-close direction classifier; no fees, economic edge, independent multi-year validation or order access."}
    for coin in PAIRS:
        try:report["assets"][coin]=run_market(series[coin])
        except (KeyError,ValueError,TypeError,OverflowError) as exc:
            report["errors"][coin]=type(exc).__name__
    return report

def main():
    series={}
    for coin in PAIRS:
        try:series[coin]=fetch_candles(coin)
        except (OSError,ValueError,TimeoutError,KeyError) :continue
    result=run_all(series)
    Path("learning_engine_report.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"learned_markets":len(result["assets"]),"errors":result["errors"],"trade_authorization":False}))
    if not result["assets"]:raise SystemExit(1)

if __name__=="__main__":main()
