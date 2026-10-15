"""Offline historical OHLCV CSV validation for HYBRIXX research.

Input: timestamp,open,high,low,close,volume; UTC timestamps as ISO8601 or Unix seconds.
Read-only. Never fetches unlicensed datasets or authorizes trading.
"""
import argparse,csv,hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path

def timestamp(value):
    value=value.strip()
    if value.isdigit(): return int(value)
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None:raise ValueError("TIMESTAMP_NEEDS_TIMEZONE")
    return int(dt.timestamp())

def inspect_csv(path,interval_minutes=60,min_years=3):
    rows=[]; digest=hashlib.sha256()
    with open(path,newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not {"timestamp","open","high","low","close","volume"}.issubset(reader.fieldnames or []):
            raise ValueError("REQUIRED_COLUMNS_MISSING")
        for r in reader:
            t=timestamp(r["timestamp"])
            o,h,l,c,v=(float(r[k]) for k in ("open","high","low","close","volume"))
            if not all(map(math.isfinite,(o,h,l,c,v))) or min(o,h,l,c)<=0 or v<0 or h<max(o,c,l) or l>min(o,c,h):
                raise ValueError("INVALID_OHLCV")
            if rows and t<=rows[-1][0]:raise ValueError("UNSORTED_OR_DUPLICATE")
            rows.append((t,c))
            digest.update(f"{t},{o:.12g},{h:.12g},{l:.12g},{c:.12g},{v:.12g}\n".encode())
    if len(rows)<2:raise ValueError("INSUFFICIENT_ROWS")
    step=interval_minutes*60
    missing=0
    for (a,_),(b,_) in zip(rows,rows[1:]):
        if (b-a)%step:raise ValueError("INVALID_CANDLE_SPACING")
        missing+=(b-a)//step-1
    span_years=(rows[-1][0]-rows[0][0])/86400/365.2425
    coverage=len(rows)/(len(rows)+missing)
    return {"rows":len(rows),"start_utc":datetime.fromtimestamp(rows[0][0],timezone.utc).isoformat(),
        "end_utc":datetime.fromtimestamp(rows[-1][0],timezone.utc).isoformat(),
        "years":round(span_years,3),"missing_intervals":missing,"coverage_pct":round(coverage*100,3),
        "sha256":digest.hexdigest(),"meets_min_years":span_years>=min_years,
        "research_eligible":span_years>=min_years and coverage>=.99,
        "trade_authorization":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("csv",type=Path)
    p.add_argument("--interval",type=int,default=60)
    p.add_argument("--years",type=float,default=3)
    p.add_argument("--report",type=Path,default=Path("historical_quality_report.json"))
    a=p.parse_args()
    result={"mode":"RESEARCH_ONLY_NO_ORDERS","source_file":a.csv.name,
            "checked_utc":datetime.now(timezone.utc).isoformat(),
            "quality":inspect_csv(a.csv,a.interval,a.years)}
    a.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
if __name__=="__main__":main()
