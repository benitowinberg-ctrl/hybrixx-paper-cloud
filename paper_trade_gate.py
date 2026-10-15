"""Fail-closed research authorization for NEW paper buys only.
Existing paper positions retain ordinary stop-loss / sell logic.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
COINS=("BTC","ETH","XRP","SOL","ADA","DOGE","DOT","LINK","LTC","AVAX")
MAX_AGE=timedelta(hours=30)

def approved_coins(gate, human, now=None):
    now=now or datetime.now(timezone.utc)
    try:
        if gate.get("mode")!="RESEARCH_ONLY_NO_ORDERS" or human.get("mode")!="RESEARCH_ONLY_NO_ORDERS":
            return set()
        a=datetime.fromisoformat(gate["source_generated_utc"].replace("Z","+00:00"))
        b=datetime.fromisoformat(human["generated_utc"].replace("Z","+00:00"))
        if any(t.tzinfo is None or t>now+timedelta(minutes=5) or now-t>MAX_AGE for t in (a,b)):
            return set()
        if abs((a-b).total_seconds())>3600:return set()
        if gate.get("missing_or_failed_assets"):return set()
        allowed=set()
        for coin in COINS:
            g=gate.get("assets",{}).get(coin,{})
            h=human.get("assets",{}).get(coin,{})
            out=h.get("out_of_sample",{})
            if (g.get("decision")=="RESEARCH_CANDIDATE" and
                g.get("reasons")==[] and
                h.get("selected")!="stay_in_cash" and
                h.get("test_candles",0)>=100 and
                out.get("return_pct",-999)>0 and
                out.get("max_drawdown_pct",999)<=10 and
                out.get("trades",0)>=4 and
                out.get("return_pct",-999)>h.get("existing_ma_12_48_baseline",{}).get("return_pct",999)):
                allowed.add(coin)
        return allowed
    except (KeyError,TypeError,ValueError,OverflowError):
        return set()

def load_approved(directory=Path("."),now=None):
    try:
        gate=json.loads((directory/"strategy_gate_report.json").read_text(encoding="utf-8"))
        human=json.loads((directory/"human_strategy_comparison.json").read_text(encoding="utf-8"))
        return approved_coins(gate,human,now)
    except (OSError,ValueError,TypeError):
        return set()
