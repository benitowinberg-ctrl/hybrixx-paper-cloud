"""Append-only-by-candle HYBRIXX research history. No trading capability."""
import json,math
from pathlib import Path

MAX_RECORDS=2000
def update_history(path, report):
    path=Path(path)
    old={"version":"1","records":[]}
    if path.exists():
        old=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(old,dict) or not isinstance(old.get("records"),list):
        raise ValueError("Invalid research history; refusing overwrite")
    records=old["records"]
    if len(records)>MAX_RECORDS or any(not isinstance(r,dict) for r in records):
        raise ValueError("Invalid research history records")
    stamp=report["last_candle_utc"]
    if not isinstance(stamp,str) or not stamp.endswith(("+00:00","Z")):
        raise ValueError("Invalid UTC candle stamp")
    ranking=report["evolution"]["ranking"]
    scores={}
    for row in ranking:
        key=row["strategy"]
        value=row["mean_oos_return_pct"]
        if not isinstance(key,str) or not key or not isinstance(value,(float,int)) or not math.isfinite(value):
            raise ValueError("Invalid strategy score")
        scores[key]=round(value,4)
    if records and stamp<records[-1]["last_candle_utc"]:
        raise ValueError("Refusing out-of-order history update")
    if records and stamp==records[-1]["last_candle_utc"]:
        # Same candle must not count as another independent learning observation.
        return old
    records.append({"last_candle_utc":stamp,"data_points":report["data_points"],
                    "strategy_mean_oos_pct":scores,"mode":"RESEARCH_ONLY"})
    if len(records)>MAX_RECORDS:
        del records[:-MAX_RECORDS]
    result={"version":"1","records":records}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def trends(history):
    records=history["records"]
    if len(records)<3:
        return {"status":"INSUFFICIENT_DISTINCT_CANDLES","observations":len(records),
                "message":"Three distinct updates required; overlapping backtests are not independent evidence."}
    names=set.intersection(*(set(r["strategy_mean_oos_pct"]) for r in records[-3:]))
    return {"status":"DESCRIPTIVE_ONLY","observations":len(records),
            "changes":[{"strategy":name,"delta_mean_oos_pct":round(
                records[-1]["strategy_mean_oos_pct"][name]-records[-3]["strategy_mean_oos_pct"][name],4)}
                for name in sorted(names)],
            "message":"Changes reflect rolling recalculations, not out-of-sample forward performance."}
